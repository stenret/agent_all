"""对话路由 — 基于 Harness 引擎的智能对话（支持多轮记忆）"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.schemas import ChatRequest, ChatResponse
from models.db_models import Conversation
from core.database import get_db, SessionLocal
from agents.orchestrator import OrchestratorAgent

router = APIRouter(prefix="/chat", tags=["chat"])

# 全局 orchestrator + 会话级上下文记忆
_orchestrator = OrchestratorAgent()
_session_contexts: dict[str, list[dict]] = {}  # session_id → [{"role":"user"/"assistant", "content":...}]


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """智能对话入口 — 自动识别意图并调度对应能力，支持多轮对话。"""

    # 直接传递用户消息，引擎通过 resume 机制自动恢复历史上下文
    result = _orchestrator.run(
        task=req.message,
        session_id=req.session_id,
    )

    # 更新会话记忆（用于前端展示历史）
    history = _session_contexts.get(req.session_id, [])
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": result.final_answer[:600]})
    _session_contexts[req.session_id] = history

    # 持久化对话
    db.add(Conversation(session_id=req.session_id, role="user", content=req.message))
    db.add(Conversation(session_id=req.session_id, role="assistant", content=result.final_answer))
    db.commit()

    return ChatResponse(
        session_id=req.session_id,
        reply=result.final_answer,
        steps=len(result.steps),
        evaluation=result.evaluation.to_dict() if result.evaluation else None,
        elapsed_ms=result.total_elapsed_ms,
    )
