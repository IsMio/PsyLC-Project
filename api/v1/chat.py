
import asyncio
import json
import logging
import time
import uuid

# 部署REST API相关
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

import type
from config import Config
from core.chat.chat_process import ChatProcess
from core.chat.emotion_recognition import analyze_sentiment, create_emotional_response
from core.filter.output_filter import OutputFilterService, build_llm_moderator, build_stream_replace_signal
from core.filter.output_policy_store import OutputPolicyStore
from core.chat.sqlite_chat_store import SQLiteChatStore
from core.chat.tool import TokenVerificationTool

# prompt模版
# 配置可配置字段

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
_history_store = SQLiteChatStore(Config.DB_PATH)

# 全局变量
model = None
embeddings = None
vectorstore = None
prompt = None
chain = None
with_message_history = None
sentiment_chain = None
output_filter_service = OutputFilterService(llm_moderator=build_llm_moderator(Config.OUTPUT_FILTER_REVIEW_ENABLED))

# 从ChatProcess导入format_response函数
def format_response(response):
    return ChatProcess.format_response(response)


def estimate_token_count(text: str) -> int:
    text = (text or "").strip()
    if not text:
        return 0
    try:
        import tiktoken  # type: ignore

        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def filter_chat_response(query_prompt: str, response_text: str) -> dict:
    if not Config.OUTPUT_FILTER_ENABLED:
        return {
            'filtered': False,
            'reason': None,
            'content': response_text,
        }
    policy = OutputPolicyStore(Config.DB_PATH).get_policy()
    review_enabled = bool(policy.get('review_enabled', Config.OUTPUT_FILTER_REVIEW_ENABLED))
    service = OutputFilterService(
        llm_moderator=build_llm_moderator(review_enabled),
        policy=policy,
    )
    if not bool(policy.get('enabled', Config.OUTPUT_FILTER_ENABLED)):
        return {
            'filtered': False,
            'reason': None,
            'content': response_text,
        }
    return service.filter_response(user_input=query_prompt, response_text=response_text)

# 初始化APIRouter
router = APIRouter(tags=["chat"])


@router.get("/system/session/list")
async def get_session_list(req: Request,userId: str, pageNum: int = 1, pageSize: int = 25,
                           isAsc: str = "desc", orderByColumn: str = "createTime" ):
    userinfo = TokenVerificationTool.verify_token(req)
    if not userinfo:
        return type.standard_response(code=401, msg="未登录仅提供有限服务")

    # 从userinfo中获取userId
    user_id = userinfo.get("user_id", userId)
    """查询会话列表"""
    try:
        sessions = _history_store.get_all_sessions(user_id)
        # 模拟分页
        start = (pageNum - 1) * pageSize
        end = start + pageSize
        paginated_sessions = sessions[start:end]

        # 转换为前端需要的格式
        chat_sessions = []
        for session in paginated_sessions:
            chat_sessions.append({
                "id": session["id"],
                "sessionTitle": session["title"],
                "userId": userId,
                "createTime": session["updated_at"],
                "sessionContent": "",  # 可选字段
                "remark": ""  # 可选字段
            })

        return type.standard_response(rows=chat_sessions)
    except Exception as e:
        return type.standard_response(code=500, msg=f"获取会话列表失败: {str(e)}")


@router.post("/system/session")
async def create_session(req: type.CreateSessionRequest):
    """创建会话"""
    try:
        session_id = str(uuid.uuid4())

        # 保存到数据库
        _history_store.save_chat(
            req.userId,
            session_id,
            {
                "messages": [],
                "total_times": [],
                "model_names": [],
                "turn_costs": [],
                "current_times": []
            }
        )

        # 重命名会话为用户提供的标题
        _history_store.rename_chat(req.userId, session_id, req.sessionTitle)

        return type.standard_response(data={
            "id": session_id,
            "sessionTitle": req.sessionTitle,
            "userId": req.userId,
            "sessionContent": req.sessionContent,
            "remark": req.remark
        })
    except Exception as e:
        return type.standard_response(code=500, msg=f"创建会话失败: {str(e)}")


@router.put("/system/session")
async def update_session(req: type.UpdateSessionRequest):
    """更新会话"""
    try:
        # 重命名会话
        _history_store.rename_chat(req.userId, req.id, req.sessionTitle)
        return type.standard_response()
    except Exception as e:
        return type.standard_response(code=500, msg=f"更新会话失败: {str(e)}")


@router.get("/system/session/{session_id}")
async def get_session(session_id: str,req: Request ,userId: str = "88823a1b-c1ce-4aa7-ba6e-a937cf4baa1d"):
    """获取会话详情"""
    userinfo = TokenVerificationTool.verify_token(req)
    if not userinfo:
        return type.standard_response(code=401, msg="未登录仅提供有限服务")
    
    # 从userinfo中获取userId
    user_id = userinfo.get("user_id", userId)
    print(f"当前用户ID: {user_id}")

    try:
        # 根据userId查询会话
        sessions = _history_store.get_all_sessions(user_id)
        session = next((s for s in sessions if s["id"] == session_id), None)
        
        # 如果会话不存在，创建一个新的会话
        if not session:
            # 生成标题：新对话+日期
            import datetime
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            session_title = f"新对话 {today}"
            
            # 保存到数据库
            _history_store.save_chat(
                user_id,
                session_id,
                {
                    "messages": [],
                    "total_times": [],
                    "model_names": [],
                    "turn_costs": [],
                    "current_times": []
                }
            )
            
            # 重命名会话为生成的标题
            _history_store.rename_chat(user_id, session_id, session_title)
            
            # 重新获取会话信息
            sessions = _history_store.get_all_sessions(user_id)
            session = next((s for s in sessions if s["id"] == session_id), None)
        
        if not session:
            return type.standard_response(code=500, msg="创建会话失败")

        return type.standard_response(data={
            "id": session["id"],
            "sessionTitle": session["title"],
            "userId": user_id,
            "createTime": session["updated_at"]
        })
    except Exception as e:
        return type.standard_response(code=500, msg=f"获取会话详情失败: {str(e)}")


@router.delete("/system/session/{ids}")
async def delete_session(ids: str, userId: str = "88823a1b-c1ce-4aa7-ba6e-a937cf4baa1d"):
    """删除会话"""
    try:
        session_ids = ids.split(",")
        for session_id in session_ids:
            _history_store.delete_chat(userId, session_id)
        return type.standard_response()
    except Exception as e:
        return type.standard_response(code=500, msg=f"删除会话失败: {str(e)}")


from fastapi.responses import StreamingResponse


@router.post("/chat/send")
async def send_message(req: type.ChatRequest, request: Request):
    # 申明引用全局变量，在函数中被初始化，并在整个应用中使用
    if not model or not embeddings or not prompt or not chain:
        logger.error("服务未初始化")
        raise HTTPException(status_code=500, detail="服务未初始化")

    try:
        if vectorstore is None or with_message_history is None:
            logger.error("服务未初始化: vectorstore 或 with_message_history 为 None")
            raise HTTPException(status_code=500, detail="服务未完成初始化，请检查启动日志")

        logger.info(f"收到聊天完成请求: {req}")
        if not req.messages:
            raise HTTPException(status_code=400, detail="messages 不能为空")
        query_prompt = req.messages[-1].content
        if query_prompt is None:
            raise HTTPException(status_code=400, detail="最后一条消息 content 不能为空")
        query_prompt = str(query_prompt).strip()
        if not query_prompt:
            raise HTTPException(status_code=400, detail="最后一条消息 content 不能为空字符串")
        logger.info(f"用户问题是: {query_prompt}")

        # 进行情感分析
        sentiment_data = analyze_sentiment(sentiment_chain, query_prompt)
        emotional_prompt = create_emotional_response(sentiment_data)
        logger.info(f"情感分析结果: {sentiment_data}")
        logger.info(f"情感提示: {emotional_prompt}")

        # 进行本地知识库检索
        retriever = await vectorstore.asimilarity_search(
            query_prompt,# 查询文本
            k=2# 返回最相似的前2条结果
        )

        # 确保sessionId存在
        session_id = req.sessionId or str(uuid.uuid4())
        # 优先使用token中的user_id，然后使用请求体中的userId，最后使用"anonymous"
        user_id = "anonymous"
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("userId", request.state.user.get("user_id", req.userId or "anonymous"))
        else:
            user_id = req.userId or "anonymous"
        logger.info(f"当前用户ID: {user_id}")

        # 调用chain进行查询

        # 处理流式响应
        if req.stream:
            # 定义一个异步生成器函数，用于生成流式数据
            async def generate_stream():
                # 为每个流式数据片段生成一个唯一的chunk_id
                # 将格式化后的响应按行分割
                # lines = formatted_response.split('\n')
                # 历每一行，并构建响应片段
                context = "\n".join([doc.page_content for doc in retriever])
                full_response = ""
                async for l in with_message_history.astream(

                        {"query": query_prompt, "context": context, "emotional_prompt": emotional_prompt},
                        config={
                            "configurable": {
                                "user_id": user_id,
                                "conversation_id": session_id
                            }
                        }):
                    text = getattr(l, "content", l)
                    if text is None or "" == text:
                        continue
                    text = str(text)
                    full_response += text
                    logger.info(f"生成的文本片段: {text}")
                    chunk = {
                        'choices': [
                            {
                                'delta': {'content': text},
                                'finish_reason': None,
                            },
                        ],
                        'replace': False,
                        'filtered': False,
                        'filter_reason': None,
                    }
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)

                filtered_result = filter_chat_response(query_prompt, format_response(full_response))
                final_text = filtered_result['content']
                if filtered_result['filtered']:
                    replace_chunk = build_stream_replace_signal(final_text, filtered_result['reason'])
                    yield f"data: {json.dumps(replace_chunk, ensure_ascii=False)}\n\n"

                # 生成最后一个片段，表示流式响应的结束
                final_chunk = {
                    "choices": [
                        {
                            "delta": {},
                            "finish_reason": "stop"
                        }
                    ],
                    'filtered': filtered_result['filtered'],
                    'filter_reason': filtered_result['reason'],
                    'replace': False,
                }
                yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"

                # 保存聊天记录
                formatted_response = final_text

                # 构建新的消息
                user_message = {
                    "role": "user",
                    "content": query_prompt,
                    "token_count": estimate_token_count(query_prompt),
                    "model": "",  # 实际应用中应该记录模型
                    "created_at": int(time.time())
                }
                assistant_message = {
                    "role": "assistant",
                    "content": formatted_response,
                    "token_count": estimate_token_count(formatted_response),
                    "model": Config.MODEL_NAME,  # 实际应用中应该记录模型
                    "created_at": int(time.time())
                }

                # 保存到SQLite数据库（在后台线程中执行，避免阻塞事件循环）
                try:
                    import concurrent.futures
                    # 使用外部函数中定义的user_id变量
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        await asyncio.get_event_loop().run_in_executor(
                            executor,
                            lambda: _history_store.add_message(user_id, session_id, user_message,
                                                               assistant_message)
                        )
                    logger.info("聊天记录保存成功")
                except Exception as e:
                    logger.error(f"保存聊天记录失败: {str(e)}")

            # 返回fastapi.responses中StreamingResponse对象，流式传输数据
            # media_type设置为text/event-stream以符合SSE(Server-SentEvents) 格式
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream; charset=utf-8",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        # 处理非流式响应处理
        else:
            # 对于非流式响应，使用invoke方法而不是stream方法
            context = "\n".join([doc.page_content for doc in retriever])
            result = with_message_history.invoke(
                {"query": query_prompt, "context": context, "emotional_prompt": emotional_prompt},
                config={
                    "configurable": {
                        "user_id": user_id,
                        "conversation_id": session_id
                    }
                }
            )

            # 确保result是一个字符串
            if hasattr(result, "content"):
                result_content = result.content
            else:
                result_content = str(result)

            formatted_response = format_response(result_content)
            filtered_result = filter_chat_response(query_prompt, formatted_response)
            formatted_response = filtered_result['content']
            logger.info(f"格式化的搜索结果: {formatted_response}")
            response = type.ChatCompletionResponse(
                choices=[
                    type.ChatCompletionResponseChoice(
                        index=0,
                        message=type.Message(role="assistant", content=formatted_response),
                        finish_reason="stop"
                    )
                ],
                filtered=filtered_result['filtered'],
                filter_reason=filtered_result['reason'],
            )

            # 保存聊天记录
            # 构建新的消息
            user_message = {
                "role": "user",
                "content": query_prompt,
                "token_count": estimate_token_count(query_prompt),
                "model": "",  # 实际应用中应该记录模型
                "created_at": int(time.time())
            }
            assistant_message = {
                "role": "assistant",
                "content": formatted_response,
                "token_count": estimate_token_count(formatted_response),
                "model": Config.MODEL_NAME,  # 实际应用中应该记录模型
                "created_at": int(time.time())
            }

            # 保存到SQLite数据库（在后台线程中执行，避免阻塞事件循环）
            try:
                import concurrent.futures
                # 使用外部函数中定义的user_id变量
                with concurrent.futures.ThreadPoolExecutor() as executor:
                        await asyncio.get_event_loop().run_in_executor(
                            executor,
                            lambda: _history_store.add_message(user_id, session_id, user_message,
                                                               assistant_message)
                        )
                logger.info("聊天记录保存成功")
            except Exception as e:
                logger.error(f"保存聊天记录失败: {str(e)}")

            logger.info(f"发送响应内容: \n{response}")
            # 返回fastapi.responses中JSONResponse对象
            # model_dump()方法通常用于将Pydantic模型实例的内容转换为一个标准的Python字典，以便进行序列化
            return JSONResponse(content=response.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("处理聊天完成时出错")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/message")
async def add_chat(req: type.ChatMessageVo):
    """新增聊天记录"""
    try:
        # 这里简化处理，实际应该根据userId和sessionId保存消息
        return type.standard_response()
    except Exception as e:
        return type.standard_response(code=500, msg=f"新增聊天记录失败: {str(e)}")


@router.get("/system/message/list")
async def get_chat_list(sessionId: str, userId: str = "88823a1b-c1ce-4aa7-ba6e-a937cf4baa1d", pageNum: int = 1,
                        pageSize: int = 20):
    """获取聊天记录列表"""
    try:
        # 获取会话历史
        messages = _history_store.get_session_history(sessionId)
        if not messages:
            return type.standard_response(rows=[])

        # 模拟分页
        start = (pageNum - 1) * pageSize
        end = start + pageSize
        paginated_messages = messages[start:end]

        # 转换为前端需要的格式
        chat_messages = []
        for msg in paginated_messages:
            # 将assistant角色转换为system角色
            role = msg.get("role")
            if role == "assistant":
                role = "system"
            chat_messages.append({
                "id": msg.get("id", str(uuid.uuid4())),
                "sessionId": sessionId,
                "userId": userId,
                "role": role,
                "content": msg.get("content"),
                "createTime": msg.get("created_at")
            })

        return type.standard_response(rows=chat_messages)
    except Exception as e:
        return type.standard_response(code=500, msg=f"获取聊天记录失败: {str(e)}")


@router.get("/system/model/modelList")
async def get_model_list():
    """获取模型列表"""
    try:
        # 模拟模型列表
        models = [
            {
                "id": 1,
                "category": "chat",
                "modelName": "gpt-4",
                "modelDescribe": "gpt4模型，适合复杂对话和任务",
                "modelPrice": 0.01,
                "modelType": "chat",
                "modelShow": True,

            }
        ]
        return type.standard_response(data=models)
    except Exception as e:
        return type.standard_response(code=500, msg=f"获取模型列表失败: {str(e)}")
