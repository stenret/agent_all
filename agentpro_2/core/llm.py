"""LLM 工厂 — 统一创建 DeepSeek 模型实例"""

from langchain_openai import ChatOpenAI
from langchain_core.callbacks.base import BaseCallbackHandler

from config import config


def build_llm(
    streaming: bool = False,
    callbacks: list[BaseCallbackHandler] | None = None,
    temperature: float | None = None,
) -> ChatOpenAI:
    """创建 DeepSeek ChatOpenAI 兼容实例。

    Args:
        streaming: 是否启用流式输出
        callbacks: 回调处理器列表
        temperature: 温度参数，默认用 config
    """
    return ChatOpenAI(
        model=config.DEEPSEEK_MODEL,
        openai_api_key=config.DEEPSEEK_API_KEY,
        openai_api_base=config.DEEPSEEK_BASE_URL,
        temperature=temperature or config.TEMPERATURE,
        streaming=streaming,
        callbacks=callbacks or [],
    )


class StreamCallback(BaseCallbackHandler):
    """捕获 LLM token 流"""

    def __init__(self):
        self.tokens: list[str] = []

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.tokens.append(token)
