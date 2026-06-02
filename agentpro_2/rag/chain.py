"""RAG Chain — 检索增强生成流水线"""

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from core.llm import build_llm
from rag.retriever import build_retriever, hybrid_search


# ---------------------------------------------------------------------------
# RAG Prompt
# ---------------------------------------------------------------------------
RAG_PROMPT = PromptTemplate.from_template(
    """你是一个基于知识库的智能问答助手。请严格根据提供的上下文信息回答用户问题。

<上下文>
{context}
</上下文>

<规则>
1. 仅根据上下文回答，不要编造信息
2. 若上下文不足以回答问题，明确告知用户"知识库中暂无相关信息"
3. 回答简洁、准确、有条理
4. 引用上下文中的关键信息时，注明来源
</规则>

<对话历史>
{chat_history}
</对话历史>

<用户问题>
{question}
</用户问题>

请回答："""
)


# ---------------------------------------------------------------------------
# 格式化检索结果
# ---------------------------------------------------------------------------
def _format_docs(docs: list) -> str:
    """将检索到的文档拼接为上下文字符串。"""
    if not docs:
        return "暂无相关文档。"
    parts = []
    for i, doc in enumerate(docs, 1):
        src = doc.metadata.get("source", "未知来源")
        parts.append(f"[文档{i} | 来源: {src}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# RAG Chain
# ---------------------------------------------------------------------------
def build_rag_chain(use_rerank: bool = True):
    """构建 RAG 链：检索 → 格式化 → 生成。"""
    llm = build_llm()
    retriever = build_retriever(use_rerank=use_rerank)

    def retrieve_and_format(inputs: dict) -> dict:
        question = inputs["question"]
        docs = retriever.invoke(question) if hasattr(retriever, "invoke") else hybrid_search(question)
        return {
            "context": _format_docs(docs),
            "question": question,
            "chat_history": inputs.get("chat_history", ""),
        }

    chain = (
        RunnablePassthrough.assign(context_and_question=retrieve_and_format)
        | (lambda x: RAG_PROMPT.format(**x["context_and_question"]))
        | llm
        | StrOutputParser()
    )

    return chain


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------
def rag_query(
    question: str,
    chat_history: str = "",
    use_rerank: bool = True,
) -> str:
    """同步 RAG 查询。"""
    chain = build_rag_chain(use_rerank=use_rerank)
    return chain.invoke({"question": question, "chat_history": chat_history})
