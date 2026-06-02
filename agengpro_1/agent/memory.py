"""多轮对话记忆模块 — ConversationBufferMemory 会话管理"""

from __future__ import annotations

from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage


class SessionMemoryManager:
    """管理多个会话的 ConversationBufferMemory，支持会话隔离和自动清理。"""

    def __init__(self):
        self._stores: dict[str, ConversationBufferMemory] = {}

    def get_or_create(self, session_id: str) -> ConversationBufferMemory:
        """获取或创建一个会话的记忆实例。"""
        if session_id not in self._stores:
            self._stores[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                input_key="input",
            )
        return self._stores[session_id]

    def load_history(self, session_id: str) -> list:
        """加载指定会话的历史消息。"""
        memory = self._stores.get(session_id)
        if memory is None:
            return []
        return memory.load_memory_variables({}).get("chat_history", [])

    def save_context(self, session_id: str, user_input: str, ai_output: str):
        """保存一轮对话到记忆。"""
        memory = self.get_or_create(session_id)
        # ConversationBufferMemory 的 save_context 需要实际的输入/输出键
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(ai_output)

    def clear(self, session_id: str):
        """清除指定会话的记忆。"""
        self._stores.pop(session_id, None)

    def clear_all(self):
        """清除所有会话。"""
        self._stores.clear()


# 全局单例
memory_manager = SessionMemoryManager()
