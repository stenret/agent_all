"""同步聊天路由 — POST /chat"""

from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from agent.core import run_sync

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """同步对话：发送消息，等待完整回复后返回。"""
    reply = run_sync(req.session_id, req.message)
    return ChatResponse(session_id=req.session_id, reply=reply)
