"""Agent Harness — ETCSLV 六元治理模型

H = (E, T, C, S, L, V)
- E: Execution Loop (NanoEngine)
- T: Tool Registry (DictToolRegistry)
- C: Context Manager (SimpleContextManager)
- S: State Store (JsonStateStore)
- L: Lifecycle Hooks (SimpleHookManager)
- V: Evaluator (TicketingEvaluator)
"""

from harness.schema import (
    ToolCall, LLMResponse, AgentMessage,
    StepResult, EvaluationResult, EngineResult, HookStage,
)
from harness.base import (
    LLMProtocol, BaseToolRegistry, BaseContextManager,
    BaseStateStore, BaseHookManager, BaseEvaluator,
)
from harness.engine import NanoEngine
from harness.prompt import PromptManager, DEFAULT_PROMPTS
from harness.components.tools import DictToolRegistry, tool, infer_schema
from harness.components.context import SimpleContextManager
from harness.components.state import JsonStateStore
from harness.components.hooks import SimpleHookManager
from harness.components.evaluator import TicketingEvaluator

__all__ = [
    # Schema
    "ToolCall", "LLMResponse", "AgentMessage",
    "StepResult", "EvaluationResult", "EngineResult", "HookStage",
    # Base
    "LLMProtocol", "BaseToolRegistry", "BaseContextManager",
    "BaseStateStore", "BaseHookManager", "BaseEvaluator",
    # Engine
    "NanoEngine",
    # Prompt
    "PromptManager", "DEFAULT_PROMPTS",
    # Components
    "DictToolRegistry", "tool", "infer_schema",
    "SimpleContextManager", "JsonStateStore",
    "SimpleHookManager", "TicketingEvaluator",
]
