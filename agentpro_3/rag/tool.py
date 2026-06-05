"""RAG 知识库检索工具 — 供 Agent Harness 调用"""

from rag.retriever import hybrid_search


def _format_docs(docs: list) -> str:
    """将检索到的文档拼接为上下文字符串。"""
    if not docs:
        return "[知识库] 未找到相关文档。"
    parts = []
    for i, doc in enumerate(docs, 1):
        src = doc.metadata.get("source", "未知来源")
        parts.append(f"[文档{i} | 来源: {src}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def knowledge_search(query: str) -> str:
    """从本地知识库检索相关内容。

    当用户询问演出详情、场馆信息、购票须知等已入库的知识时调用此工具。
    如果返回"未找到相关文档"，请使用其他工具或直接回答。
    """
    docs = hybrid_search(query)
    return _format_docs(docs)
