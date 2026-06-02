"""RAG 工作流 — 基于 LangGraph 的检索增强生成流水线

工作流: 接收问题 → 检索 → 重排序 → 上下文组装 → LLM 生成 → 输出
"""

from langgraph.graph import StateGraph, END

from workflows.states import RAGWorkflowState
from rag.retriever import build_retriever, hybrid_search
from rag.chain import RAG_PROMPT
from core.llm import build_llm


# ---------------------------------------------------------------------------
# 节点函数
# ---------------------------------------------------------------------------
def retrieve_node(state: RAGWorkflowState) -> dict:
    """检索节点：从向量库检索相关文档。"""
    question = state["question"]
    docs = hybrid_search(question)
    return {"retrieved_docs": docs}


def rerank_node(state: RAGWorkflowState) -> dict:
    """重排序节点：对检索结果重排序。"""
    from rag.retriever import SimpleReranker

    reranker = SimpleReranker()
    docs = state.get("retrieved_docs", [])
    reranked = reranker.rerank(state["question"], docs)
    return {"retrieved_docs": reranked}


def format_context_node(state: RAGWorkflowState) -> dict:
    """格式化上下文。"""
    docs = state.get("retrieved_docs", [])
    if not docs:
        return {"context": "暂无相关文档。"}

    parts = []
    for i, doc in enumerate(docs, 1):
        src = doc.metadata.get("source", "未知来源")
        parts.append(f"[文档{i} | 来源: {src}]\n{doc.page_content}")

    return {"context": "\n\n---\n\n".join(parts)}


def generate_node(state: RAGWorkflowState) -> dict:
    """生成节点：LLM 基于上下文生成回答。"""
    llm = build_llm()
    prompt = RAG_PROMPT.format(
        context=state["context"],
        chat_history=state.get("chat_history", ""),
        question=state["question"],
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}


# ---------------------------------------------------------------------------
# 构建 RAG 工作流图
# ---------------------------------------------------------------------------
def build_rag_workflow() -> StateGraph:
    """构建 RAG 工作流：
    retrieve → rerank → format → generate → END
    """
    workflow = StateGraph(RAGWorkflowState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("format_context", format_context_node)
    workflow.add_node("generate", generate_node)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "format_context")
    workflow.add_edge("format_context", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


# 全局编译好的 RAG 工作流
rag_workflow_app = build_rag_workflow()
