"""Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field


# ==================== 对话 ====================
class ChatRequest(BaseModel):
    session_id: str = Field(default="default", description="会话 ID")
    message: str = Field(..., min_length=1, description="用户消息")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    status: str = "ok"


# ==================== RAG 查询 ====================
class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="问题")
    session_id: str = Field(default="default")
    use_rerank: bool = Field(default=True, description="是否重排序")


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[str] = []


# ==================== 文档上传 ====================
class DocumentUploadResponse(BaseModel):
    filename: str
    chunk_count: int
    status: str = "ok"


# ==================== Agent 调用 ====================
class AgentRunRequest(BaseModel):
    agent_type: str = Field(..., description="researcher / coder / analyst / orchestrator")
    task: str = Field(..., min_length=1)
    session_id: str = Field(default="default")


class AgentRunResponse(BaseModel):
    agent_type: str
    result: str


# ==================== 工作流 ====================
class WorkflowRunRequest(BaseModel):
    workflow_type: str = Field(..., description="rag / multi_agent")
    task: str = Field(..., min_length=1)
    session_id: str = Field(default="default")


class WorkflowRunResponse(BaseModel):
    workflow_type: str
    result: str


# ==================== 会话 ====================
class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: list[dict]


# ==================== 健康检查 ====================
class HealthResponse(BaseModel):
    status: str = "healthy"
    model: str
    version: str = "2.0.0"
    vector_store_docs: int = 0
