
import logging
import re
from contextlib import asynccontextmanager
from typing import List

# 部署REST API相关
from fastapi import FastAPI
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# prompt模版
from langchain_core.prompts import PromptTemplate
# 配置可配置字段
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from config import Config
from core.emotion_recognition import create_sentiment_chain
from core.tool import SQLiteChatMessageHistory

logger = logging.getLogger(__name__)



class ChatProcess:
    def __init__(self):
        self.model = None
        self.embeddings = None
        self.vectorstore = None
        self.prompt = None
        self.chain = None
        self.with_message_history = None
        self.sentiment_chain = None
        self._history_store = None

    # 获取prompt在chain中传递的prompt最终的内容
    @staticmethod
    def get_prompt(prompt):
        logger.info(f"最后给到LLM的prompt的内容: {prompt}")
        return prompt


    # 格式化响应，对输入的文本进行段落分隔、添加适当的换行符，以及在代码块中增加标记，以便生成更具可读性的输出
    @staticmethod
    def format_response(response):
        paragraphs = re.split(r'\n{2,}', response)
        formatted_paragraphs = []
        for para in paragraphs:
            if '```' in para:
                parts = para.split('```')
                for i, part in enumerate(parts):
                    if i % 2 == 1:
                        parts[i] = f"\n```\n{part.strip()}\n```\n"
                para = ''.join(parts)
            else:
                para = para.replace('. ', '.\n')
            formatted_paragraphs.append(para.strip())
        return '\n\n'.join(formatted_paragraphs)


    # 获取消息历史记录
    def _compress_messages(self: List[BaseMessage]) -> List[BaseMessage]:
        if not self:
            return self

        # 先裁剪每条消息长度，避免单条过长。
        clipped: List[BaseMessage] = []
        for msg in self:
            content = msg.content
            if not isinstance(content, str):
                content = str(content)
            if len(content) > Config.MAX_SINGLE_MESSAGE_CHARS:
                content = content[:Config.MAX_SINGLE_MESSAGE_CHARS] + " ...(已截断)"
            msg.content = content
            clipped.append(msg)

        # 再按“最近优先”控制消息数与总长度。
        selected: List[BaseMessage] = []
        total_chars = 0
        for msg in reversed(clipped):
            text = msg.content if isinstance(msg.content, str) else str(msg.content)
            msg_len = len(text)
            if len(selected) >= Config.MAX_HISTORY_MESSAGES:
                break
            if total_chars + msg_len > Config.MAX_HISTORY_CHARS:
                break
            selected.append(msg)
            total_chars += msg_len

        selected.reverse()
        return selected


    @staticmethod
    def get_session_history(user_id: str, conversation_id: str):
        return SQLiteChatMessageHistory(
            user_id=user_id,
            conversation_id=conversation_id
        )


    @asynccontextmanager
    async def lifespan(self: FastAPI):
        # 在应用启动时执行的代码
        print("应用正在启动...")
        # 导入 api.chat 模块，以便能够设置其全局变量
        import api.chat
        try:
            # （1）初始化模型和嵌入模型
            api.chat.model = ChatOpenAI(
                base_url=Config.DASHSCOPE_API_BASE_URL,
                api_key=Config.get_api_key(),
                model=Config.MODEL_NAME,
                temperature=Config.TEMPERATURE,
                streaming=True,
                extra_body={"enable_thinking": False}  # 思考过程
            )
            # (2)初始化情感识别链
            api.chat.sentiment_chain = create_sentiment_chain(api.chat.model)
            api.chat.embeddings = DashScopeEmbeddings(
                model=Config.EMBEDDINGS_MODEL_NAME,
                dashscope_api_key=Config.get_api_key(),
            )

            # （3）初始化chroma向量数据库
            api.chat.vectorstore = Chroma(
                persist_directory=Config.CHROMA_PERSIST_DIR,#使用配置中的持久化目录
                collection_name=Config.CHROMA_COLLECTION_NAME,#使用配置中的集合名称
                embedding_function=api.chat.embeddings,#使用上面初始化的嵌入模型
            )
            # （4）初始化模板prompt
            prompt_template = PromptTemplate.from_file(Config.PROMPT_TEMPLATE_PATH)
            api.chat.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", Config.SYSTEM_PROMPT),
                    ("system", "{emotional_prompt}"),
                    MessagesPlaceholder("history"),
                    ("system", "以下是可能相关的心理健康资料:\n{context}"),
                    ("human", prompt_template.template)
                ]
            )

            api.chat.chain = api.chat.prompt | ChatProcess.get_prompt | api.chat.model
            # （4）构建带有消息历史的智能体
            api.chat.with_message_history = RunnableWithMessageHistory(
                api.chat.chain,
                ChatProcess.get_session_history,
                input_messages_key="query",
                history_messages_key="history",
                history_factory_config=[
                    ConfigurableFieldSpec(
                        id="user_id",
                        annotation=str,
                        name="User ID",
                        description="Unique identifier for the user.",
                        default="",
                        is_shared=True,
                    ),
                    ConfigurableFieldSpec(
                        id="conversation_id",
                        annotation=str,
                        name="Conversation ID",
                        description="Unique identifier for the conversation.",
                        default="",
                        is_shared=True,
                    ),
                ],
            )
            print("应用初始化成功！")
        except Exception as e:
            print(f"应用启动时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
        yield
        # 在应用关闭时执行的代码
        print("应用正在关闭...")
