"""C: 上下文管理 — 窗口编排 + 压缩策略"""

from harness.base import BaseContextManager
from harness.schema import AgentMessage


class SimpleContextManager(BaseContextManager):
    """简单的上下文管理器。

    特性：
    - 维护消息列表（OpenAI 格式）
    - 基于字符数的 token 估算（中文 ~2 chars/token, 英文 ~4 chars/token）
    - 压缩策略：保留最近 N 条完整消息 + 前面用摘要替代
    - 可注入 system prompt
    """

    def __init__(self, system_prompt: str = "", max_tokens: int = 8000):
        self._messages: list[AgentMessage] = []
        self._system_prompt = system_prompt
        self._max_tokens = max_tokens
        if system_prompt:
            self._messages.append(AgentMessage(role="system", content=system_prompt))

    # ------------------------------------------------------------------
    # BaseContextManager 接口
    # ------------------------------------------------------------------
    def add_message(self, msg: AgentMessage) -> None:
        self._messages.append(msg)

    def get_full_context(self) -> list[dict]:
        return [m.to_openai_format() for m in self._messages]

    def compact(self, keep_last_n: int = 4) -> None:
        """压缩上下文：保留 system + 最近 N 条消息，其余替换为摘要"""
        if len(self._messages) <= keep_last_n + 1:  # +1 for system
            return

        system_msgs = [m for m in self._messages if m.role == "system"]
        non_system = [m for m in self._messages if m.role != "system"]

        if len(non_system) <= keep_last_n:
            return

        # 生成早期消息摘要
        early = non_system[:-keep_last_n]
        summary_parts = []
        for msg in early:
            content_preview = msg.content[:100].replace("\n", " ")
            summary_parts.append(f"[{msg.role}]: {content_preview}")

        summary = "【历史对话摘要】\n" + "\n".join(summary_parts)

        # 重建消息列表
        self._messages = system_msgs + [
            AgentMessage(role="system", content=summary),
        ] + non_system[-keep_last_n:]

    def get_token_count(self) -> int:
        """基于字符数估算 token 数"""
        total_chars = sum(len(m.content) for m in self._messages)
        # 中文约 2 chars/token，英文约 4 chars/token，取平均 3
        return total_chars // 3

    def set_system_prompt(self, prompt: str) -> None:
        """更新 system prompt"""
        self._system_prompt = prompt
        # 移除旧 system 消息，添加新的
        self._messages = [m for m in self._messages if m.role != "system"]
        self._messages.insert(0, AgentMessage(role="system", content=prompt))

    def get_message_count(self) -> int:
        return len(self._messages)

    def clear(self) -> None:
        """清空上下文，保留 system prompt"""
        self._messages = []
        if self._system_prompt:
            self._messages.append(AgentMessage(role="system", content=self._system_prompt))
