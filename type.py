import uuid ,time
from pydantic import BaseModel, Field
from typing import List, Optional, Dict



class Message(BaseModel):
    role :str
    content :str
class ChatRequest(BaseModel):
    messages: List[Message]
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    model: Optional[str] = None
    stream: Optional[bool] = True

# 定义ChatCompletionResponseChoice类
class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None

# 定义ChatCompletionResponse类
class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    choices: List[ChatCompletionResponseChoice]
    system_fingerprint: Optional[str] = None
class CreateSessionRequest(BaseModel):
    sessionTitle: str
    userId: Optional[str] = "88823a1b-c1ce-4aa7-ba6e-a937cf4baa1d"
    sessionContent: Optional[str] = None
    remark: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    id: str
    userId: Optional[str] = "88823a1b-c1ce-4aa7-ba6e-a937cf4baa1d"
    sessionTitle: Optional[str] = None
    sessionContent: Optional[str] = None
    remark: Optional[str] = None


class ChatMessageVo(BaseModel):
    id: Optional[str] = None
    sessionId: str
    userId: Optional[str] = "88823a1b-c1ce-4aa7-ba6e-a937cf4baa1d"
    role: str
    content: str
    createTime: Optional[int] = None


class SessionListRequest(BaseModel):
    userId: Optional[str] = "88823a1b-c1ce-4aa7-ba6e-a937cf4baa1d"
    pageNum: int = 1
    pageSize: int = 25
    isAsc: str = "desc"
    orderByColumn: str = "createTime"


class MessageListRequest(BaseModel):
    sessionId: str
    userId: Optional[str] = "88823a1b-c1ce-4aa7-ba6e-a937cf4baa1d"
    pageNum: int = 1
    pageSize: int = 20

def standard_response(code: int = 200, msg: str = "ok", data: Optional[dict] = None, rows: Optional[list] = None):
    """标准响应结构"""
    response = {"code": code, "msg": msg}
    if data is not None:
        response["data"] = data
    if rows is not None:
        response["rows"] = rows
    return response

