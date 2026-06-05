"""向量存储 — 基于 ChromaDB 的持久化向量数据库"""

from langchain_chroma import Chroma

from config import config
from core.embeddings import build_embeddings

_vector_store: Chroma | None = None


def get_vector_store() -> Chroma:
    """获取或初始化 ChromaDB 向量存储（持久化）。"""
    global _vector_store
    if _vector_store is None:
        embeddings = build_embeddings()
        _vector_store = Chroma(
            collection_name=config.CHROMA_COLLECTION,
            embedding_function=embeddings,
            persist_directory=config.CHROMA_PERSIST_DIR,
        )
    return _vector_store


def add_documents(docs: list) -> list[str]:
    """批量写入文档到向量库，返回文档 ID 列表。"""
    store = get_vector_store()
    return store.add_documents(docs)


def delete_by_ids(ids: list[str]) -> None:
    """按 ID 删除文档。"""
    store = get_vector_store()
    store.delete(ids=ids)


def get_collection_stats() -> dict:
    """获取向量库统计信息。"""
    store = get_vector_store()
    count = store._collection.count()
    return {"total_documents": count, "collection": config.CHROMA_COLLECTION}
