"""编排 Agent — 多智能体调度中心，负责任务分解、分配、汇总"""

import asyncio
from typing import AsyncIterator

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.llm import build_llm
from agents.researcher import ResearcherAgent
from agents.coder import CoderAgent
from agents.analyst import AnalystAgent


# ---------------------------------------------------------------------------
# Agent 注册表
# ---------------------------------------------------------------------------
AGENT_REGISTRY = {
    "researcher": ResearcherAgent(),
    "coder": CoderAgent(),
    "analyst": AnalystAgent(),
}

# ---------------------------------------------------------------------------
# 编排 Prompt
# ---------------------------------------------------------------------------
ORCHESTRATOR_PROMPT = PromptTemplate.from_template(
    """你是一个多智能体系统的总调度官（Orchestrator）。你可以将复杂任务分解并分配给以下专业 Agent：

{agent_descriptions}

<规则>
1. 分析用户任务，决定由哪个 Agent 处理（可多个）
2. 如需多个 Agent 协作，按依赖顺序调度
3. 将任务分解为子任务，指定执行者，等待结果后汇总
4. 输出格式：

PLAN:
- [Agent名称] 负责: [子任务描述]
- [Agent名称] 负责: [子任务描述]

然后对每个子任务输出：
DELEGATE [Agent名称]: [具体指令]

收到结果后输出：
FINAL SUMMARY: [汇总最终答案]
</规则>

<对话历史>
{chat_history}
</对话历史>

<用户任务>
{input}
</用户任务>

请制定执行计划："""
)


# ---------------------------------------------------------------------------
# 编排器
# ---------------------------------------------------------------------------
class Orchestrator:
    """多智能体编排器：分析任务 → 分配子Agent → 汇总结果"""

    def __init__(self):
        self.llm = build_llm()
        self.plan_chain = ORCHESTRATOR_PROMPT | self.llm | StrOutputParser()

    def _get_agent_descriptions(self) -> str:
        return "\n".join(
            f"- **{a.name}**: {a.description}" for a in AGENT_REGISTRY.values()
        )

    def run(self, task: str, chat_history: str = "") -> str:
        """同步执行编排流程。"""
        # 1. 生成执行计划
        plan = self.plan_chain.invoke({
            "input": task,
            "chat_history": chat_history,
            "agent_descriptions": self._get_agent_descriptions(),
        })

        # 2. 解析计划，提取子任务
        sub_tasks = self._parse_plan(plan)

        # 3. 执行子任务
        results = {}
        for agent_name, instruction in sub_tasks:
            agent = AGENT_REGISTRY.get(agent_name)
            if agent:
                results[agent_name] = agent.run(instruction)
            else:
                results[agent_name] = f"Agent '{agent_name}' 未找到"

        # 4. 汇总结果
        return self._summarize(task, plan, results)

    def _parse_plan(self, plan: str) -> list[tuple[str, str]]:
        """从计划文本中提取 (agent_name, instruction) 对。"""
        tasks = []
        for line in plan.split("\n"):
            line = line.strip()
            if line.startswith("DELEGATE "):
                # 格式: DELEGATE agent_name: instruction
                content = line[len("DELEGATE "):]
                if ":" in content:
                    name, instruction = content.split(":", 1)
                    tasks.append((name.strip().lower(), instruction.strip()))
        return tasks

    def _summarize(self, task: str, plan: str, results: dict) -> str:
        """汇总所有 Agent 结果。"""
        results_text = "\n\n".join(
            f"【{name}】执行结果:\n{output}" for name, output in results.items()
        )

        summary_prompt = f"""请根据以下子任务执行结果，对原始任务给出最终的综合回答。

原始任务: {task}

执行计划:
{plan}

执行结果:
{results_text}

请给出完整的最终答案（整合所有 Agent 的发现）："""

        return self.llm.invoke(summary_prompt).content
