"""Agent 注册与管理"""

from agents.show_searcher import ShowSearcherAgent
from agents.ticket_agent import TicketAgent
from agents.customer_service import CustomerServiceAgent
from agents.orchestrator import OrchestratorAgent

# 单例
_searcher = ShowSearcherAgent()
_ticket = TicketAgent()
_cs = CustomerServiceAgent()
_orchestrator = OrchestratorAgent()

AGENT_REGISTRY = {
    "show_searcher": _searcher,
    "ticket_agent": _ticket,
    "customer_service": _cs,
    "orchestrator": _orchestrator,
}


def get_agent(agent_type: str):
    """获取 Agent 实例。"""
    return AGENT_REGISTRY.get(agent_type.lower())
