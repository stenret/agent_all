"""检索器 — 向量检索 + 关键词检索 + 重排序优化"""

from typing import Sequence
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_core.documents.compressor import BaseDocumentCompressor

from config import config
from rag.vector_store import get_vector_store


# ---------------------------------------------------------------------------
# 简单重排序器（基于关键词匹配 + 位置打分）
# ---------------------------------------------------------------------------
class SimpleReranker:
    """基于关键词重叠 + 位置权重的轻量重排序器。

    不依赖额外 API，适合本地快速重排序。
    """

    def rerank(
        self, query: str, docs: list[Document], top_k: int | None = None
    ) -> list[Document]:
        """按相关性重新排序文档。"""
        k = top_k or config.RETRIEVAL_TOP_K
        if not docs:
            return []

        query_terms = set(query.lower().split())

        scored = []
        for i, doc in enumerate(docs):
            content = doc.page_content.lower()
            # 关键词命中得分
            term_score = sum(1 for t in query_terms if t in content) / max(len(query_terms), 1)
            # 位置奖励：向量检索的原始排名越靠前越好
            position_score = 1.0 / (i + 1)
            # 长度惩罚：太短的文档可能信息不足
            length_score = min(len(doc.page_content) / 500, 1.0)
            # 综合得分
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
    """Build a retriever with optional reranking.

    Args:
        top_k: number of documents to retrieve
        use_rerank: enable reranking (default from config)
    """
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
            """Wrap SimpleReranker as a LangChain-compatible compressor."""

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
    """混合检索：向量检索 + 简单关键词过滤。"""
    store = get_vector_store()
    k = top_k or config.RETRIEVAL_TOP_K

    # 向量检索
    docs = store.similarity_search(query, k=k)

    # 若开启混合检索，按关键词额外加权
    if config.HYBRID_SEARCH_ENABLED:
        query_terms = set(query.lower().split())
        for doc in docs:
            content = doc.page_content.lower()
            hits = sum(1 for t in query_terms if t in content)
            # 提升命中关键词的文档排名
            doc.metadata["keyword_hits"] = hits

        docs.sort(key=lambda d: d.metadata.get("keyword_hits", 0), reverse=True)

    return docs[:k]
