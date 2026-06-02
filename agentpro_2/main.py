"""FastAPI 应用入口 — Enterprise RAG + Multi-Agent 系统"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from core.database import init_db
from rag.vector_store import get_collection_stats
from models.schemas import HealthResponse
from routers import chat, rag, agent, workflow, document


# ---------------------------------------------------------------------------
# 生命周期
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库，关闭时清理资源。"""
    init_db()
    print(f"[INIT] 数据库已初始化")
    print(f"[INIT] 向量库: {get_collection_stats()}")
    yield


# ---------------------------------------------------------------------------
# 创建 FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Enterprise RAG + Multi-Agent System",
    description=(
        "企业级智能 Agent 平台：RAG 检索增强生成 · 多智能体协作 · "
        "LangGraph 工作流 · 向量数据库 · 工具调用"
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(workflow.router)
app.include_router(document.router)


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health():
    stats = get_collection_stats()
    return HealthResponse(
        model=config.DEEPSEEK_MODEL,
        vector_store_docs=stats["total_documents"],
    )


@app.get("/")
async def root():
    return {
        "message": "Enterprise RAG + Multi-Agent System",
        "docs": "/docs",
        "endpoints": {
            "chat": "/chat",
            "rag_query": "/rag/query",
            "agent_run": "/agent/run",
            "workflow_run": "/workflow/run",
            "documents": "/documents/upload  /list  /stats",
        },
    }


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
