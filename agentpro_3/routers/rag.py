"""RAG 路由 — 文档入库 + 知识库查询"""

import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from config import config
from rag.document_loader import load_file
from rag.text_splitter import split_documents
from rag.vector_store import add_documents, get_collection_stats
from rag.retriever import hybrid_search
from rag.tool import _format_docs

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 5


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    source_count: int


class IngestResponse(BaseModel):
    filename: str
    chunks: int
    message: str


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(req: RAGQueryRequest):
    """知识库检索查询。"""
    docs = hybrid_search(req.question, top_k=req.top_k)
    answer = _format_docs(docs)
    return RAGQueryResponse(
        question=req.question,
        answer=answer,
        source_count=len(docs),
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    """上传文档到知识库（支持 PDF/TXT/Markdown）。"""
    # 检查扩展名
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".pdf", ".txt", ".md", ".markdown"}:
        raise HTTPException(400, f"不支持的文件格式: {ext}")

    # 检查大小
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > config.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(400, f"文件过大: {size_mb:.1f}MB > {config.MAX_UPLOAD_SIZE_MB}MB")

    # 保存到 uploads
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(config.UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(content)

    # 加载 → 分割 → 入库
    docs = load_file(save_path)
    chunks = split_documents(docs)
    ids = add_documents(chunks)

    return IngestResponse(
        filename=file.filename,
        chunks=len(ids),
        message=f"成功入库 {len(ids)} 个文档块",
    )


@router.get("/stats")
async def rag_stats():
    """知识库统计信息。"""
    return get_collection_stats()
