"""Agent 路由 — 单独调用指定 Agent"""

from fastapi import APIRouter

from models.schemas import AgentRunRequest, AgentRunResponse
from agents import get_agent

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(req: AgentRunRequest):
    """调用指定 Agent 执行任务。

    可选 agent_type:
    - show_searcher: 演出搜索
    - ticket_agent: 选座购票
    - customer_service: 订单查询/退票
    - orchestrator: 智能编排（自动识别意图）
    """
    agent = get_agent(req.agent_type)
    if not agent:
        return AgentRunResponse(
            agent_type=req.agent_type,
            result=f"未知 Agent: {req.agent_type}。可选: show_searcher, ticket_agent, customer_service, orchestrator",
        )

    result = agent.run(task=req.task, session_id=req.session_id)

    return AgentRunResponse(
        agent_type=req.agent_type,
        result=result.final_answer,
        steps=len(result.steps),
        evaluation=result.evaluation.to_dict() if result.evaluation else None,
    )
