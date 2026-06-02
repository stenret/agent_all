"""基础 Agent 类 — 所有专业 Agent 的抽象基类"""

from abc import ABC, abstractmethod
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from core.llm import build_llm


class BaseAgent(ABC):
    """Agent 基类。子类需定义 name / description / tools / prompt_template。"""

    name: str = "base"
    description: str = "基础 Agent"
    tools: list = []
    prompt_template: str = ""

    def __init__(self):
        self._executor: AgentExecutor | None = None

    @property
    def executor(self) -> AgentExecutor:
        """懒加载 AgentExecutor。"""
        if self._executor is None:
            llm = build_llm()
            prompt = PromptTemplate.from_template(
                self.prompt_template,
                partial_variables={
                    "tools": self._format_tools(),
                    "tool_names": ", ".join(t.name for t in self.tools),
                },
            )
            agent = create_react_agent(llm=llm, tools=self.tools, prompt=prompt)
            self._executor = AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=5,
                handle_parsing_errors=True,
            )
        return self._executor

    def _format_tools(self) -> str:
        return "\n".join(f"- {t.name}: {t.description}" for t in self.tools)

    def run(self, task: str) -> str:
        """执行 Agent，返回结果。"""
        result = self.executor.invoke({"input": task})
        return result.get("output", "")
