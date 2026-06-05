"""Agent Harness 数据结构定义 — H=(E,T,C,S,L,V)"""

import json
from dataclasses import dataclass, field
from enum import Enum


class HookStage(Enum):
    """生命周期钩子阶段"""
    ON_TASK_START = "on_task_start"
    ON_THOUGHT_READY = "on_thought_ready"
    ON_BEFORE_ACTION = "on_before_action"
    ON_AFTER_ACTION = "on_after_action"
    ON_STEP_END = "on_step_end"
    ON_TASK_END = "on_task_end"


@dataclass
class ToolCall:
    """工具调用"""
    name: str
    args: dict
    call_id: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "args": self.args, "call_id": self.call_id}


@dataclass
class LLMResponse:
    """LLM 响应"""
    thought: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    final_answer: str | None = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    @property
    def has_final_answer(self) -> bool:
        return self.final_answer is not None and len(self.final_answer.strip()) > 0


@dataclass
class AgentMessage:
    """Agent 消息"""
    role: str  # user / assistant / system / tool
    content: str
    tool_call: ToolCall | None = None
    tool_call_id: str = ""

    def to_openai_format(self) -> dict:
        msg: dict = {"role": self.role, "content": self.content}
        if self.tool_call:
            msg["tool_calls"] = [{
                "id": self.tool_call.call_id,
                "type": "function",
                "function": {
                    "name": self.tool_call.name,
                    "arguments": json.dumps(self.tool_call.args, ensure_ascii=False),
                }
            }]
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        return msg


@dataclass
class StepResult:
    """单步执行结果"""
    step_num: int
    thought: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    should_stop: bool = False
    stop_reason: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "step_num": self.step_num,
            "thought": self.thought,
            "tool_calls": [tc.to_dict() if hasattr(tc, "to_dict") else tc for tc in self.tool_calls],
            "observations": self.observations,
            "should_stop": self.should_stop,
            "stop_reason": self.stop_reason,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass
class EvaluationResult:
    """评估结果"""
    should_stop: bool = False
    stop_reason: str = ""
    success: bool | None = None
    success_reason: str = ""
    trajectory: list[StepResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "should_stop": self.should_stop,
            "stop_reason": self.stop_reason,
            "success": self.success,
            "success_reason": self.success_reason,
            "steps": len(self.trajectory),
            "trajectory": [s.to_dict() for s in self.trajectory],
        }


@dataclass
class EngineResult:
    """引擎执行结果"""
    session_id: str
    query: str
    final_answer: str = ""
    steps: list[StepResult] = field(default_factory=list)
    evaluation: EvaluationResult = field(default_factory=EvaluationResult)
    total_elapsed_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "query": self.query,
            "final_answer": self.final_answer,
            "total_steps": len(self.steps),
            "evaluation": self.evaluation.to_dict(),
            "total_elapsed_ms": self.total_elapsed_ms,
            "error": self.error,
        }
