"""检索器 — 向量检索 + 混合检索 + 重排序"""

from typing import Sequence
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_core.documents.compressor import BaseDocumentCompressor

from config import config
from rag.vector_store import get_vector_store


# ---------------------------------------------------------------------------
# 轻量重排序器
# ---------------------------------------------------------------------------
class SimpleReranker:
    """基于关键词重叠 + 位置权重的本地重排序器（无额外 API 依赖）。"""

    def rerank(
        self, query: str, docs: list[Document], top_k: int | None = None
    ) -> list[Document]:
        k = top_k or config.RETRIEVAL_TOP_K
        if not docs:
            return []

        query_terms = set(query.lower().split())

        scored = []
        for i, doc in enumerate(docs):
            content = doc.page_content.lower()
            term_score = sum(1 for t in query_terms if t in content) / max(len(query_terms), 1)
            position_score = 1.0 / (i + 1)
            length_score = min(len(doc.page_content) / 500, 1.0)
            final_score = term_score * 0.5 + position_score * 0.3 + length_score * 0.2
            scored.append((final_score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:k]]


# ---------------------------------------------------------------------------
# 构建检索器
# ---------------------------------------------------------------------------
def build_retriever(
    top_k: int | None = None,
    use_rerank: bool | None = None,
) -> BaseRetriever:
    """构建检索器，可选重排序。"""
    store = get_vector_store()
    k = top_k or config.RETRIEVAL_TOP_K
    rerank = use_rerank if use_rerank is not None else config.RERANK_ENABLED

    base_retriever = store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k * 2 if rerank else k},
    )

    if rerank:
        reranker = SimpleReranker()

        class RerankCompressor(BaseDocumentCompressor):
            class Config:
                arbitrary_types_allowed = True

            def compress_documents(
                self,
                documents: Sequence[Document],
                query: str,
                callbacks=None,
            ) -> Sequence[Document]:
                return reranker.rerank(query, list(documents), top_k=k)

        return ContextualCompressionRetriever(
            base_compressor=RerankCompressor(),
            base_retriever=base_retriever,
        )

    return base_retriever


# ---------------------------------------------------------------------------
# 混合检索（向量 + 关键词）
# ---------------------------------------------------------------------------
def hybrid_search(query: str, top_k: int | None = None) -> list[Document]:
    """混合检索：向量检索 + 关键词加权。"""
    store = get_vector_store()
    k = top_k or config.RETRIEVAL_TOP_K

    docs = store.similarity_search(query, k=k)

    if config.HYBRID_SEARCH_ENABLED:
        query_terms = set(query.lower().split())
        for doc in docs:
            content = doc.page_content.lower()
            hits = sum(1 for t in query_terms if t in content)
            doc.metadata["keyword_hits"] = hits
        docs.sort(key=lambda d: d.metadata.get("keyword_hits", 0), reverse=True)

    return docs[:k]
