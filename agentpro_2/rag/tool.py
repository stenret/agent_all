"""RAG 知识库检索工具 — 供 Agent 调用"""

from langchain_core.tools import Tool

from rag.retriever import hybrid_search
from rag.chain import _format_docs


def knowledge_search_func(query: str) -> str:
    """从本地知识库检索相关内容。"""
    docs = hybrid_search(query)
    if not docs:
        return "[知识库] 未找到相关文档。建议尝试网页搜索或直接回答。"
    return _format_docs(docs)


knowledge_search_tool = Tool(
    name="knowledge_search",
    description=(
        "本地知识库检索工具。当用户询问可能已存储在知识库中的信息时使用。"
        "输入搜索关键词，返回相关文档片段。"
        "如果返回'未找到相关文档'，请使用 web_search 工具或直接回答。"
    ),
    func=knowledge_search_func,
)
