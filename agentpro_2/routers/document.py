"""文档管理路由 — 上传、索引、查询"""

import os
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from models.schemas import DocumentUploadResponse
from models.db_models import DocumentIndex
from core.database import get_db
from rag.document_loader import load_file
from rag.text_splitter import split_documents
from rag.vector_store import add_documents, get_collection_stats
from config import config

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传文档 → 分割 → 向量化 → 存入 ChromaDB + 数据库索引。"""
    # 保存到本地
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(config.UPLOAD_DIR, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 加载文档
    docs = load_file(file_path)

    # 分割
    chunks = split_documents(docs)

    # 写入向量库
    add_documents(chunks)

    # 写入数据库索引
    doc_index = DocumentIndex(
        filename=file.filename,
        file_path=file_path,
        chunk_count=len(chunks),
        metadata_json={"size_bytes": len(content)},
    )
    db.add(doc_index)
    db.commit()

    return DocumentUploadResponse(filename=file.filename, chunk_count=len(chunks))


@router.get("/list")
async def list_documents(db: Session = Depends(get_db)):
    """列出所有已索引的文档。"""
    docs = db.query(DocumentIndex).order_by(DocumentIndex.uploaded_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "chunk_count": d.chunk_count,
            "uploaded_at": str(d.uploaded_at),
        }
        for d in docs
    ]


@router.get("/stats")
async def document_stats():
    """获取向量库统计信息。"""
    return get_collection_stats()
