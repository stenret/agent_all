"""Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field


# ---------- 同步聊天 ----------
class ChatRequest(BaseModel):
    session_id: str = Field(
        default="default",
        description="会话 ID，用于区分不同用户/会话的记忆",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="用户输入的消息",
    )


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    status: str = "ok"


# ---------- 流式聊天 ----------
class StreamChatRequest(BaseModel):
    session_id: str = Field(default="default")
    message: str = Field(..., min_length=1)


# ---------- 会话管理 ----------
class SessionClearRequest(BaseModel):
    session_id: str = Field(default="default")


class SessionClearResponse(BaseModel):
    session_id: str
    message: str


# ---------- 健康检查 ----------
class HealthResponse(BaseModel):
    status: str = "healthy"
    model: str
    version: str = "1.0.0"
