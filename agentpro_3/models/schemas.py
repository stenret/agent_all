"""Pydantic 数据模型 — API 请求/响应"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 对话
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    session_id: str = Field(default="default", description="会话ID")
    message: str = Field(..., min_length=1, description="用户消息")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    steps: int = 0
    evaluation: dict | None = None
    elapsed_ms: float = 0.0


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------
class AgentRunRequest(BaseModel):
    agent_type: str = Field(..., description="show_searcher / ticket_agent / customer_service / orchestrator")
    task: str = Field(..., min_length=1)
    session_id: str = Field(default="default")


class AgentRunResponse(BaseModel):
    agent_type: str
    result: str
    steps: int = 0
    evaluation: dict | None = None


# ---------------------------------------------------------------------------
# 演出
# ---------------------------------------------------------------------------
class ShowSearchRequest(BaseModel):
    keyword: str = Field(default="", description="搜索关键词")
    show_type: str = Field(default="", description="演出类型")
    city: str = Field(default="", description="城市")
    date_from: str = Field(default="", description="开始日期")
    date_to: str = Field(default="", description="结束日期")
    max_price: float = Field(default=0, description="最高票价")
    limit: int = Field(default=5, ge=1, le=20)


class ShowDetailRequest(BaseModel):
    show_id: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# 座位
# ---------------------------------------------------------------------------
class SeatCheckRequest(BaseModel):
    show_id: str = Field(..., min_length=1)
    section: str = Field(default="")


class SeatLockRequest(BaseModel):
    show_id: str = Field(..., min_length=1)
    seats: str = Field(..., min_length=1, description="座位列表，逗号分隔")
    session_id: str = Field(default="default")


# ---------------------------------------------------------------------------
# 订单
# ---------------------------------------------------------------------------
class PayRequest(BaseModel):
    order_id: str = Field(..., min_length=1)
    payment_method: str = Field(default="微信支付")


class OrderQueryRequest(BaseModel):
    order_id: str = Field(default="")
    session_id: str = Field(default="")


class RefundRequest(BaseModel):
    order_id: str = Field(..., min_length=1)
    reason: str = Field(default="")


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "healthy"
    model: str
    version: str = "3.0.0"
    framework: str = "Agent Harness (ETCSLV)"


# ---------------------------------------------------------------------------
# 会话
# ---------------------------------------------------------------------------
class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: list[dict]
