"""购票工作流 — 基于 LangGraph 的完整购票流程

流程: 意图识别 → 搜索演出 → 选座 → 下单 → 支付 → 出票
"""

from langgraph.graph import StateGraph, END

from workflows.states import TicketingWorkflowState
from agents.show_searcher import ShowSearcherAgent
from agents.ticket_agent import TicketAgent
from agents.customer_service import CustomerServiceAgent
from core.llm import build_llm_adapter


_searcher = ShowSearcherAgent()
_ticket = TicketAgent()
_cs = CustomerServiceAgent()
_llm = build_llm_adapter()


# ---------------------------------------------------------------------------
# 节点
# ---------------------------------------------------------------------------
def intent_node(state: TicketingWorkflowState) -> dict:
    """意图识别节点"""
    task = state["task"]
    response = _llm.chat([
        {"role": "system", "content": "判断用户意图，只输出一个词: search(搜索演出) / buy(购票) / after_sales(查询订单或退票) / other"},
        {"role": "user", "content": task},
    ], tools=None)
    intent = response.get("content", "other").strip().lower()
    if "search" in intent:
        intent = "search"
    elif "buy" in intent or "购" in intent or "买" in intent:
        intent = "buy"
    elif "after" in intent or "退" in intent or "查" in intent:
        intent = "after_sales"
    else:
        intent = "search"
    return {"intent": intent}


def search_node(state: TicketingWorkflowState) -> dict:
    """搜索演出节点"""
    result = _searcher.run(state["task"], state.get("session_id", "default"))
    return {"result": result.final_answer}


def buy_node(state: TicketingWorkflowState) -> dict:
    """购票节点"""
    result = _ticket.run(state["task"], state.get("session_id", "default"))
    return {"result": result.final_answer}


def after_sales_node(state: TicketingWorkflowState) -> dict:
    """售后节点"""
    result = _cs.run(state["task"], state.get("session_id", "default"))
    return {"result": result.final_answer}


def finalize_node(state: TicketingWorkflowState) -> dict:
    """汇总输出"""
    return {"final_answer": state.get("result", "处理完成")}


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------
def route_by_intent(state: TicketingWorkflowState) -> str:
    intent = state.get("intent", "search")
    if intent == "buy":
        return "buy"
    elif intent == "after_sales":
        return "after_sales"
    return "search"


# ---------------------------------------------------------------------------
# 构建工作流
# ---------------------------------------------------------------------------
def build_ticketing_workflow():
    workflow = StateGraph(TicketingWorkflowState)

    workflow.add_node("intent", intent_node)
    workflow.add_node("search", search_node)
    workflow.add_node("buy", buy_node)
    workflow.add_node("after_sales", after_sales_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("intent")

    workflow.add_conditional_edges(
        "intent", route_by_intent,
        {"search": "search", "buy": "buy", "after_sales": "after_sales"},
    )
    workflow.add_edge("search", "finalize")
    workflow.add_edge("buy", "finalize")
    workflow.add_edge("after_sales", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


ticketing_workflow_app = build_ticketing_workflow()
