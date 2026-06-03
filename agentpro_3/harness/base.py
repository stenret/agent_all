"""Agent Harness 抽象接口 — ETCSLV 六组件"""

from abc import ABC, abstractmethod
from typing import Callable

from harness.schema import AgentMessage, StepResult, EvaluationResult, HookStage


class LLMProtocol(ABC):
    """LLM 调用协议：Harness 引擎通过此接口与任意 LLM 交互"""

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """发送消息到 LLM，返回原始响应字典。

        Returns:
            {
                "content": str,           # 模型文本输出
                "tool_calls": [           # 工具调用列表（可能为空）
                    {"id": str, "name": str, "args": dict}
                ],
                "finish_reason": str,     # stop / tool_calls / length
            }
        """
        ...


class BaseToolRegistry(ABC):
    """T: 工具注册表 — 类型化工具目录 + schema校验"""

    @abstractmethod
    def get_tool_schemas(self) -> list[dict]:
        """返回 OpenAI function-calling 格式的工具 schema 列表"""
        ...

    @abstractmethod
    def call(self, name: str, args: dict) -> str:
        """执行指定工具，返回观察结果字符串"""
        ...

    @abstractmethod
    def register(self, name: str, description: str, func: Callable,
                 parameters: dict | None = None) -> None:
        """注册一个工具"""
        ...


class BaseContextManager(ABC):
    """C: 上下文管理 — 窗口编排 + 压缩策略"""

    @abstractmethod
    def add_message(self, msg: AgentMessage) -> None:
        """添加消息到上下文"""
        ...

    @abstractmethod
    def get_full_context(self) -> list[dict]:
        """获取完整上下文（OpenAI 格式消息列表）"""
        ...

    @abstractmethod
    def compact(self, keep_last_n: int = 4) -> None:
        """压缩上下文：保留最近 N 条完整消息，其余用摘要替代"""
        ...

    @abstractmethod
    def get_token_count(self) -> int:
        """估算当前上下文 token 数"""
        ...


class BaseStateStore(ABC):
    """S: 状态存储 — 跨轮次持久化 + 崩溃恢复"""

    @abstractmethod
    def save_state(self, session_id: str, state: dict) -> None:
        """保存会话状态快照"""
        ...

    @abstractmethod
    def load_state(self, session_id: str) -> dict | None:
        """加载会话状态，用于崩溃恢复"""
        ...

    @abstractmethod
    def delete_state(self, session_id: str) -> None:
        """删除会话状态"""
        ...

    @abstractmethod
    def list_sessions(self) -> list[str]:
        """列出所有会话 ID"""
        ...


class BaseHookManager(ABC):
    """L: 生命周期钩子 — 横切注入：日志/策略/权限/审计"""

    @abstractmethod
    def trigger(self, stage: HookStage, context: dict) -> dict:
        """触发指定阶段的所有钩子，返回可能被修改的 context"""
        ...

    @abstractmethod
    def register(self, stage: HookStage, hook: Callable[[dict], dict]) -> None:
        """注册一个钩子到指定阶段"""
        ...


class BaseEvaluator(ABC):
    """V: 评估器 — 轨迹记录 + 中途停检 + 目标验证"""

    @abstractmethod
    def log_step(self, step: StepResult) -> None:
        """记录一步执行轨迹"""
        ...

    @abstractmethod
    def should_stop(self, step: StepResult, trajectory: list[StepResult]) -> bool:
        """中途停检：判断是否应该提前终止（如死循环、工具反复失败）"""
        ...

    @abstractmethod
    def evaluate_success(self, trajectory: list[StepResult],
                         final_answer: str) -> EvaluationResult:
        """任务完成后评估是否成功"""
        ...

    @abstractmethod
    def get_report(self) -> dict:
        """获取完整的评估报告"""
        ...
