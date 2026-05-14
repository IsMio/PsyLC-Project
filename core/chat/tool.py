from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from typing import List

from starlette.responses import JSONResponse

from api.v1.auth import verify_token
from config import Config
from core.chat.sqlite_chat_store import SQLiteChatStore

class TokenVerificationTool:
    @staticmethod
    def verify_token(request):
        """验证令牌的有效性"""
        try:
            authorization = request.headers.get("Authorization")
            if not authorization:
                return None

            # 提取token
            token = authorization.replace("Bearer ", "")

            # 验证token
            payload = verify_token(token)
            if not payload:
                return None
            print(payload)
            return payload
        except Exception:
            return None
class SQLiteChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, user_id: str, conversation_id: str):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self._history_store = SQLiteChatStore(Config.DB_PATH)  # 使用与 api/chat.py 相同的数据库路径

    # 获取消息历史记录
    def _compress_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        if not messages:
            return messages

        # 先裁剪每条消息长度，避免单条过长。
        clipped: List[BaseMessage] = []
        for msg in messages:
            content = msg.content
            if not isinstance(content, str):
                content = str(content)
            if len(content) > 400:  # 使用硬编码值，因为 Config 可能没有这些配置
                content = content[:400] + " ...(已截断)"
            msg.content = content
            clipped.append(msg)

        # 再按“最近优先”控制消息数与总长度。
        selected: List[BaseMessage] = []
        total_chars = 0
        for msg in reversed(clipped):
            text = msg.content if isinstance(msg.content, str) else str(msg.content)
            msg_len = len(text)
            if len(selected) >= 12:  # 使用硬编码值，因为 Config 可能没有这些配置
                break
            if total_chars + msg_len > 2400:  # 使用硬编码值，因为 Config 可能没有这些配置
                break
            selected.append(msg)
            total_chars += msg_len

        selected.reverse()
        return selected
    def add_message(self, message: BaseMessage) -> None:
        """添加一条消息"""
        # 这里可以实现添加消息的逻辑
        # 但由于我们使用了 add_message 方法来批量添加消息
        # 这里可以留空或实现简单的添加逻辑
        pass

    def get_messages(self) -> List[BaseMessage]:
        """获取所有消息"""
        # 从 SQLiteChatStore 获取消息历史
        messages = self._history_store.get_session_history(self.conversation_id)
        # 转换为 BaseMessage 对象
        base_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "user":
                base_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                base_messages.append(AIMessage(content=content))
            elif role == "system":
                base_messages.append(SystemMessage(content=content))
        # 压缩消息
        return self._compress_messages(base_messages)

    def clear(self) -> None:
        """清空消息"""
        # 这里可以实现清空消息的逻辑
        pass

    async def aadd_message(self, message: BaseMessage) -> None:
        """异步添加一条消息"""
        self.add_message(message)

    async def aget_messages(self) -> List[BaseMessage]:
        """异步获取所有消息"""
        return self.get_messages()

    async def aclear(self) -> None:
        """异步清空消息"""
        self.clear()

