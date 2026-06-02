"""FastAPI 应用入口"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from models.schemas import HealthResponse
from routers import chat, stream, session

# ---------------------------------------------------------------------------
# 创建 FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DeepSeek Agent API",
    description="基于 LangChain + DeepSeek 的智能 Agent，支持同步/流式对话",
    version="1.0.0",
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
app.include_router(stream.router)
app.include_router(session.router)


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(model=config.DEEPSEEK_MODEL)


@app.get("/")
async def root():
    return {"message": "DeepSeek Agent API is running. Visit /docs for Swagger UI."}


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
