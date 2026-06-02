"""工作流状态定义 — 所有 LangGraph 工作流的共享状态"""

from typing import TypedDict, Annotated
from operator import add


class RAGWorkflowState(TypedDict):
    """RAG 工作流状态"""
    question: str
    chat_history: str
    retrieved_docs: list
    context: str
    answer: str


class MultiAgentWorkflowState(TypedDict):
    """多智能体协作工作流状态"""
    task: str
    chat_history: str
    plan: str
    sub_tasks: list  # [(agent_name, instruction)]
    results: Annotated[dict, add]  # {agent_name: result}
    final_answer: str
    current_agent: str
