"""RAG 专用路由 — 文档问答"""

from fastapi import APIRouter

from models.schemas import RAGQueryRequest, RAGQueryResponse
from rag.chain import rag_query

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query_endpoint(req: RAGQueryRequest):
    """RAG 检索问答。"""
    answer = rag_query(
        question=req.question,
        chat_history="",
        use_rerank=req.use_rerank,
    )
    return RAGQueryResponse(question=req.question, answer=answer)
