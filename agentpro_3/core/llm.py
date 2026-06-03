"""LLM 适配器 — 实现 Harness LLMProtocol，对接 DeepSeek"""

import json
from langchain_openai import ChatOpenAI

from harness.base import LLMProtocol
from config import config


class DeepSeekAdapter(LLMProtocol):
    """DeepSeek LLM 适配器，实现 Harness 的 LLMProtocol 接口。

    连接 Harness 引擎与 DeepSeek API（通过 LangChain ChatOpenAI 兼容层）。
    """

    def __init__(self, temperature: float | None = None):
        self._llm = ChatOpenAI(
            model=config.DEEPSEEK_MODEL,
            openai_api_key=config.DEEPSEEK_API_KEY,
            openai_api_base=config.DEEPSEEK_BASE_URL,
            temperature=temperature or config.TEMPERATURE,
            streaming=False,
        )
        # 绑定 tools 时使用
        self._raw_llm = self._llm

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """调用 LLM，返回统一格式响应。

        使用 LangChain 的 tool-calling 机制：
        - 如果有 tools，绑定后调用
        - 无 tools 时直接 chat
        """
        try:
            if tools:
                llm_with_tools = self._raw_llm.bind_tools(
                    [t["function"] for t in tools]
                )
                response = llm_with_tools.invoke(messages)
            else:
                response = self._raw_llm.invoke(messages)

            # 解析响应
            result = {
                "content": response.content if isinstance(response.content, str) else str(response.content),
                "tool_calls": [],
                "finish_reason": "stop",
            }

            # 检查是否有 tool_calls
            if hasattr(response, "tool_calls") and response.tool_calls:
                result["finish_reason"] = "tool_calls"
                for tc in response.tool_calls:
                    args = tc.get("args", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {"query": args}

                    result["tool_calls"].append({
                        "id": tc.get("id", ""),
                        "name": tc.get("name", ""),
                        "args": args,
                    })

            # 处理 AIMessage 类型的 content（可能是列表）
            if isinstance(response.content, list):
                parts = []
                for part in response.content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            parts.append(part.get("text", ""))
                        elif part.get("type") == "tool_use":
                            pass  # 已通过 tool_calls 处理
                    else:
                        parts.append(str(part))
                result["content"] = "\n".join(parts)

            return result

        except Exception as e:
            return {
                "content": f"LLM 调用异常: {e}",
                "tool_calls": [],
                "finish_reason": "error",
            }


def build_llm_adapter(temperature: float | None = None) -> DeepSeekAdapter:
    """工厂函数：创建 DeepSeek LLM 适配器。"""
    return DeepSeekAdapter(temperature=temperature)
