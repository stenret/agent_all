"""会话管理路由 — 查看/清除记忆"""

from fastapi import APIRouter
from models.schemas import SessionClearRequest, SessionClearResponse
from agent.memory import memory_manager

router = APIRouter(prefix="/session", tags=["session"])


@router.get("/{session_id}/history")
async def get_history(session_id: str):
    """获取指定会话的历史消息。"""
    history = memory_manager.load_history(session_id)
    return {
        "session_id": session_id,
        "history": [
            {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
            for msg in history
        ],
    }


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """清除指定会话的记忆。"""
    memory_manager.clear(session_id)
    return {"session_id": session_id, "message": "会话记忆已清除"}


@router.delete("/")
async def clear_all_sessions():
    """清除所有会话。"""
    memory_manager.clear_all()
    return {"message": "所有会话记忆已清除"}
