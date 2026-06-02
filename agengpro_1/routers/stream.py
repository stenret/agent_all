"""流式聊天路由 — POST /stream"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models.schemas import StreamChatRequest
from agent.core import run_stream

router = APIRouter(prefix="/stream", tags=["stream"])


@router.post("")
async def stream_chat(req: StreamChatRequest):
    """流式对话：逐 token 返回 SSE (Server-Sent Events) 流。"""

    async def event_generator():
        async for token in run_stream(req.session_id, req.message):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
