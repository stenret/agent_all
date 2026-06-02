"""多智能体协作工作流 — 基于 LangGraph 的编排流水线

工作流: 接收任务 → 规划 → 并行调度 Agent → 收集结果 → 汇总输出
"""

from langgraph.graph import StateGraph, END

from workflows.states import MultiAgentWorkflowState
from agents.orchestrator import Orchestrator, AGENT_REGISTRY
from core.llm import build_llm

_orchestrator = Orchestrator()


# ---------------------------------------------------------------------------
# 节点函数
# ---------------------------------------------------------------------------
def plan_node(state: MultiAgentWorkflowState) -> dict:
    """规划节点：分析任务，生成执行计划。"""
    task = state["task"]
    chat_history = state.get("chat_history", "")

    plan = _orchestrator.plan_chain.invoke({
        "input": task,
        "chat_history": chat_history,
        "agent_descriptions": _orchestrator._get_agent_descriptions(),
    })

    sub_tasks = _orchestrator._parse_plan(plan)
    return {"plan": plan, "sub_tasks": sub_tasks}


def dispatch_node(state: MultiAgentWorkflowState) -> dict:
    """调度节点：依次将子任务分配给对应 Agent。"""
    sub_tasks = state.get("sub_tasks", [])
    results = {}

    for agent_name, instruction in sub_tasks:
        agent = AGENT_REGISTRY.get(agent_name.lower())
        if agent:
            results[agent_name] = agent.run(instruction)
        else:
            results[agent_name] = f"Agent '{agent_name}' 未注册"

    return {"results": results}


def summarise_node(state: MultiAgentWorkflowState) -> dict:
    """汇总节点：整合所有 Agent 的结果。"""
    llm = build_llm()
    results = state.get("results", {})

    results_text = "\n\n".join(
        f"【{name}】:\n{output}" for name, output in results.items()
    )

    summary_prompt = f"""请根据以下子任务执行结果，整合出一个完整、连贯的综合回答。

原始任务: {state['task']}

各 Agent 执行结果:
{results_text}

请给出完整的最终答案："""

    response = llm.invoke(summary_prompt)
    return {"final_answer": response.content}


# ---------------------------------------------------------------------------
# 路由：决定是否需要调度
# ---------------------------------------------------------------------------
def should_dispatch(state: MultiAgentWorkflowState) -> str:
    sub_tasks = state.get("sub_tasks", [])
    return "dispatch" if sub_tasks else "summarise"


# ---------------------------------------------------------------------------
# 构建多智能体工作流图
# ---------------------------------------------------------------------------
def build_multi_agent_workflow() -> StateGraph:
    """构建多智能体协作工作流：
    plan → dispatch → summarise → END
    """
    workflow = StateGraph(MultiAgentWorkflowState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("dispatch", dispatch_node)
    workflow.add_node("summarise", summarise_node)

    workflow.set_entry_point("plan")

    # 条件路由：有计划则调度，无则直接汇总
    workflow.add_conditional_edges(
        "plan",
        should_dispatch,
        {"dispatch": "dispatch", "summarise": "summarise"},
    )
    workflow.add_edge("dispatch", "summarise")
    workflow.add_edge("summarise", END)

    return workflow.compile()


# 全局编译好的多智能体工作流
multi_agent_workflow_app = build_multi_agent_workflow()
