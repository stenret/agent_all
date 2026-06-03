"""🎫 智能演出购票助手 — 基于 Agent Harness (ETCSLV) 架构

H = (E, T, C, S, L, V)
- E: NanoEngine — Think→Act→Observe 执行循环 + 异常恢复
- T: DictToolRegistry — 类型化工具注册 + Schema 校验
- C: SimpleContextManager — 上下文窗口编排 + 压缩策略
- S: JsonStateStore — 跨轮次持久化 + 崩溃恢复
- L: SimpleHookManager — 生命周期钩子(日志/审计/权限)
- V: TicketingEvaluator — 中途停检 + 目标达成验证

技术栈:
- FastAPI + Uvicorn (Web 框架)
- LangChain ChatOpenAI (DeepSeek LLM 适配器)
- LangGraph (可选工作流)
- SQLAlchemy + SQLite (数据持久化)
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import config
from core.database import init_db
from models.schemas import HealthResponse
from routers import chat, agent, shows, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"[INIT] 数据库已初始化")
    print(f"[INIT] 预置 50+ 场演出、6 个城市、6 个场馆")
    print(f"[INIT] Agent Harness 引擎就绪 — ETCSLV 六元治理")
    yield


app = FastAPI(
    title="🎫 智能演出购票助手",
    description=(
        "基于 Agent Harness (ETCSLV) 架构的智能演出票务平台。\n\n"
        "**核心能力:**\n"
        "- 🔍 多条件搜索 50+ 场演出（演唱会/话剧/音乐剧/展览/体育）\n"
        "- 🎫 查看实时座位 → 锁定 → 下单 → 支付 完整购票流程\n"
        "- 📋 订单查询、退票等售后服务\n"
        "- 🤖 智能 Agent 自动识别意图并调度\n\n"
        "**架构特性 (Agent Harness):**\n"
        "- E: 健壮执行循环 + 错误恢复\n"
        "- T: 类型化工具注册表 + Schema 校验\n"
        "- C: 上下文窗口压缩\n"
        "- S: 状态快照 + 崩溃恢复\n"
        "- L: 审计钩子(全操作记录)\n"
        "- V: 中途停检 + 目标验证"
    ),
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(agent.router)
app.include_router(shows.router)
app.include_router(orders.router)

# 静态文件（前端 UI）
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(model=config.DEEPSEEK_MODEL)


@app.get("/")
async def root():
    """返回前端 UI 页面"""
    from fastapi.responses import FileResponse
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
