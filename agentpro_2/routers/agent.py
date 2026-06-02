"""Agent 调用路由 — 单 Agent / 多 Agent 编排"""

from fastapi import APIRouter

from models.schemas import AgentRunRequest, AgentRunResponse
from agents.researcher import ResearcherAgent
from agents.coder import CoderAgent
from agents.analyst import AnalystAgent
from agents.orchestrator import Orchestrator

router = APIRouter(prefix="/agent", tags=["agent"])

_agents = {
    "researcher": ResearcherAgent(),
    "coder": CoderAgent(),
    "analyst": AnalystAgent(),
}
_orchestrator = Orchestrator()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(req: AgentRunRequest):
    """调用指定 Agent 执行任务。"""
    agent_type = req.agent_type.lower()

    if agent_type == "orchestrator":
        result = _orchestrator.run(req.task)
    elif agent_type in _agents:
        agent = _agents[agent_type]
        result = agent.run(req.task)
    else:
        result = f"未知 Agent 类型: {agent_type}，可选: {list(_agents.keys())} + orchestrator"

    return AgentRunResponse(agent_type=agent_type, result=result)
