"""Agent 基类 — 基于 Harness NanoEngine 的业务 Agent"""

from abc import ABC

from harness import (
    NanoEngine, DictToolRegistry, SimpleContextManager,
    JsonStateStore, SimpleHookManager, TicketingEvaluator,
    PromptManager, EngineResult,
)
from harness.schema import HookStage
from core.llm import DeepSeekAdapter
from config import config


class HarnessAgent(ABC):
    """基于 Agent Harness 的业务 Agent 基类。

    每个子类定义自己的:
    - name: Agent 名称
    - description: Agent 描述
    - system_prompt: 系统提示词
    - tools: DictToolRegistry 实例
    """

    name: str = "base"
    description: str = "基础 Agent"

    def __init__(self):
        self.llm = DeepSeekAdapter()
        self.context = SimpleContextManager(
            system_prompt=self._get_system_prompt(),
            max_tokens=config.CONTEXT_MAX_TOKENS,
        )
        self.state = JsonStateStore(config.STATE_DIR)
        self.hooks = SimpleHookManager(enable_logging=True)
        self.evaluator = TicketingEvaluator()
        self.tools = self._build_tools()

        self.engine = NanoEngine(
            llm=self.llm,
            tools=self.tools,
            context=self.context,
            state=self.state,
            hooks=self.hooks,
            evaluator=self.evaluator,
        )

    def _get_system_prompt(self) -> str:
        """子类可覆盖以自定义 system prompt。"""
        return PromptManager().render("system")

    def _build_tools(self) -> DictToolRegistry:
        """子类覆盖以注册工具。"""
        return DictToolRegistry()

    def run(self, task: str, session_id: str = "default", max_steps: int | None = None) -> EngineResult:
        """执行 Agent 任务。"""
        # 每次执行重建 context 以保持干净的会话
        self.context = SimpleContextManager(
            system_prompt=self._get_system_prompt(),
            max_tokens=config.CONTEXT_MAX_TOKENS,
        )
        self.evaluator = TicketingEvaluator()
        self.engine = NanoEngine(
            llm=self.llm,
            tools=self.tools,
            context=self.context,
            state=self.state,
            hooks=self.hooks,
            evaluator=self.evaluator,
        )

        return self.engine.run(
            session_id=session_id,
            query=task,
            max_steps=max_steps or config.MAX_STEPS,
            resume=False,
        )

    def get_audit_trail(self) -> list[dict]:
        return self.hooks.get_audit_trail()
