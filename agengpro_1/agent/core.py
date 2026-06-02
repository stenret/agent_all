"""Agent 核心 — 基于 LangChain 的 ReAct Agent，集成 DeepSeek 模型"""

from __future__ import annotations

from typing import AsyncIterator

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.base import BaseCallbackHandler

from config import config
from agent.tools import ALL_TOOLS
from agent.memory import memory_manager


# ---------------------------------------------------------------------------
# ReAct Prompt 模板
# ---------------------------------------------------------------------------
REACT_PROMPT = PromptTemplate.from_template(
    """你是一个智能助手，可以使用以下工具来完成用户的任务。

可用工具：
{tools}

工具名称：{tool_names}

严格按以下格式回复（不要在最终回答之外添加额外文字）：

Question: 用户的问题
Thought: 思考接下来应该做什么
Action: 要执行的动作，必须是 [{tool_names}] 中的一个
Action Input: 传递给动作的输入
Observation: 动作返回的结果
... (上述 Thought/Action/Action Input/Observation 可重复多次)
Thought: 我现在知道最终答案了
Final Answer: 对用户的最终回答

开始！

{chat_history}

Question: {input}
Thought: {agent_scratchpad}"""
)


# ---------------------------------------------------------------------------
# LLM 工厂
# ---------------------------------------------------------------------------
def build_llm(streaming: bool = False, callbacks: list | None = None) -> ChatOpenAI:
    """创建 DeepSeek ChatOpenAI 兼容实例。"""
    return ChatOpenAI(
        model=config.DEEPSEEK_MODEL,
        openai_api_key=config.DEEPSEEK_API_KEY,
        openai_api_base=config.DEEPSEEK_BASE_URL,
        temperature=config.TEMPERATURE,
        streaming=streaming,
        callbacks=callbacks or [],
        verbose=config.VERBOSE,
    )


# ---------------------------------------------------------------------------
# Agent 构建
# ---------------------------------------------------------------------------
def build_agent(
    session_id: str,
    streaming: bool = False,
    callbacks: list | None = None,
) -> AgentExecutor:
    """构建一个绑定会话记忆的 AgentExecutor。"""
    llm = build_llm(streaming=streaming, callbacks=callbacks)
    memory = memory_manager.get_or_create(session_id)

    agent = create_react_agent(
        llm=llm,
        tools=ALL_TOOLS,
        prompt=REACT_PROMPT,
    )

    return AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=ALL_TOOLS,
        memory=memory,
        verbose=config.VERBOSE,
        max_iterations=config.MAX_ITERATIONS,
        handle_parsing_errors=True,
        return_intermediate_steps=False,
    )


# ---------------------------------------------------------------------------
# 同步执行
# ---------------------------------------------------------------------------
def run_sync(session_id: str, user_input: str) -> str:
    """同步执行 Agent，返回最终结果字符串。"""
    executor = build_agent(session_id)
    result = executor.invoke({"input": user_input})
    output = result.get("output", "")
    # 持久化本轮对话
    memory_manager.save_context(session_id, user_input, output)
    return output


# ---------------------------------------------------------------------------
# 流式执行
# ---------------------------------------------------------------------------
class StreamCallback(BaseCallbackHandler):
    """捕获 LLM 的流式 token 输出。"""

    def __init__(self):
        self.queue: list[str] = []

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.queue.append(token)


async def run_stream(
    session_id: str, user_input: str
) -> AsyncIterator[str]:
    """异步流式执行 Agent，逐 token 产出。"""
    callback = StreamCallback()
    executor = build_agent(session_id, streaming=True, callbacks=[callback])

    # 在后台运行 agent.invoke；同时消费 callback 中的 token
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    full_output = ""

    def _invoke():
        nonlocal full_output
        result = executor.invoke({"input": user_input})
        full_output = result.get("output", "")
        return full_output

    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, _invoke)

    # 轮询式消费流式 token
    while not task.done() or callback.queue:
        if callback.queue:
            token = callback.queue.pop(0)
            yield token
        else:
            await asyncio.sleep(0.05)

    # 确保 task 完成
    await task

    # 保存对话记忆
    if full_output:
        memory_manager.save_context(session_id, user_input, full_output)
