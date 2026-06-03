"""NanoEngine — Agent Harness 执行引擎

Think → Act → Observe 循环 + ETCSLV 六组件治理

设计原则：
- 引擎对 prompt、memory、权限、I/O 零感知
- 所有行为通过注入的 ETCSLV 组件实现
- 中环评估 + 适时放弃 + 状态快照
"""

import time
import uuid

from harness.base import (
    LLMProtocol, BaseToolRegistry, BaseContextManager,
    BaseStateStore, BaseHookManager, BaseEvaluator,
)
from harness.schema import (
    AgentMessage, ToolCall, StepResult, EngineResult,
    EvaluationResult, HookStage,
)


class NanoEngine:
    """Agent Harness 执行引擎

    使用示例:
        engine = NanoEngine(
            llm=my_llm_adapter,
            tools=my_tool_registry,
            context=my_context_manager,
            state=my_state_store,
            hooks=my_hook_manager,
            evaluator=my_evaluator,
        )
        result = engine.run(session_id="user-123", query="帮我订一张票")
    """

    def __init__(
        self,
        llm: LLMProtocol,
        tools: BaseToolRegistry,
        context: BaseContextManager,
        state: BaseStateStore,
        hooks: BaseHookManager,
        evaluator: BaseEvaluator,
    ):
        self.llm = llm
        self.tools = tools
        self.context = context
        self.state = state
        self.hooks = hooks
        self.evaluator = evaluator

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    def run(
        self,
        session_id: str,
        query: str,
        max_steps: int = 10,
        resume: bool = True,
    ) -> EngineResult:
        """执行 Agent 主循环。

        Args:
            session_id: 会话标识
            query: 用户输入
            max_steps: 最大执行步数
            resume: 是否尝试从上次状态恢复
        """
        start_time = time.time()
        trajectory: list[StepResult] = []

        # ---- 1. 生命周期：任务开始 ----
        ctx = {"session_id": session_id, "query": query}
        ctx = self.hooks.trigger(HookStage.ON_TASK_START, ctx)

        # ---- 2. 尝试恢复状态 ----
        if resume:
            saved = self.state.load_state(session_id)
            if saved:
                trajectory = saved.get("trajectory", [])
                # 从保存状态恢复上下文
                for msg_dict in saved.get("messages", []):
                    self.context.add_message(AgentMessage(**msg_dict))

        # ---- 3. 添加用户消息 ----
        user_msg = AgentMessage(role="user", content=query)
        self.context.add_message(user_msg)

        # ---- 4. Think→Act→Observe 循环 ----
        final_answer = ""
        step_num = len(trajectory)

        while step_num < max_steps:
            step_num += 1
            step_start = time.time()

            # --- Think: 调用 LLM ---
            messages = self.context.get_full_context()
            tool_schemas = self.tools.get_tool_schemas()

            try:
                llm_response = self.llm.chat(messages, tool_schemas)
            except Exception as e:
                step = StepResult(
                    step_num=step_num,
                    thought=f"LLM 调用失败: {e}",
                    should_stop=True,
                    stop_reason=f"LLM error: {e}",
                    elapsed_ms=(time.time() - step_start) * 1000,
                )
                trajectory.append(step)
                break

            # 解析 LLM 响应
            thought = llm_response.get("content", "")
            raw_tool_calls = llm_response.get("tool_calls", [])
            finish_reason = llm_response.get("finish_reason", "stop")

            tool_calls = [
                ToolCall(name=tc["name"], args=tc["args"], call_id=tc.get("id", str(uuid.uuid4())))
                for tc in raw_tool_calls
            ]

            # --- 生命周期：思考完成 ---
            ctx = self.hooks.trigger(HookStage.ON_THOUGHT_READY, {
                "session_id": session_id,
                "step_num": step_num,
                "thought": thought,
                "tool_calls": [tc.to_dict() for tc in tool_calls],
            })

            # --- 判断：是最终回答还是需要工具调用 ---
            if finish_reason == "stop" and not tool_calls:
                final_answer = thought
                step = StepResult(
                    step_num=step_num,
                    thought=thought,
                    tool_calls=[],
                    observations=[],
                    elapsed_ms=(time.time() - step_start) * 1000,
                )
                trajectory.append(step)
                # 添加 assistant 消息
                self.context.add_message(AgentMessage(role="assistant", content=final_answer))
                break

            # --- Act: 执行工具调用 ---
            observations: list[str] = []

            # 先添加 assistant 消息（含工具调用），OpenAI 要求 assistant → tool 的顺序
            assistant_msg = AgentMessage(
                role="assistant",
                content=thought,
                tool_call=tool_calls[0] if tool_calls else None,
            )
            self.context.add_message(assistant_msg)

            for tc in tool_calls:
                # 生命周期：动作执行前
                ctx = self.hooks.trigger(HookStage.ON_BEFORE_ACTION, {
                    "session_id": session_id,
                    "step_num": step_num,
                    "tool_name": tc.name,
                    "tool_args": tc.args,
                })

                try:
                    obs = self.tools.call(tc.name, tc.args)
                except Exception as e:
                    obs = f"工具执行失败 [{tc.name}]: {e}"

                observations.append(obs)

                # 生命周期：动作执行后
                ctx = self.hooks.trigger(HookStage.ON_AFTER_ACTION, {
                    "session_id": session_id,
                    "step_num": step_num,
                    "tool_name": tc.name,
                    "tool_args": tc.args,
                    "observation": obs,
                })

                # 添加工具结果到上下文（必须在 assistant 消息之后）
                self.context.add_message(AgentMessage(
                    role="tool",
                    content=obs,
                    tool_call_id=tc.call_id,
                ))

            # --- 记录本步结果 ---
            step = StepResult(
                step_num=step_num,
                thought=thought,
                tool_calls=tool_calls,
                observations=observations,
                elapsed_ms=(time.time() - step_start) * 1000,
            )
            trajectory.append(step)

            # --- S: 保存状态快照 ---
            self._save_checkpoint(session_id, trajectory)

            # --- V: 记录轨迹 ---
            self.evaluator.log_step(step)

            # --- V: 中途停检 ---
            if self.evaluator.should_stop(step, trajectory):
                step.should_stop = True
                step.stop_reason = "evaluator signaled stop"
                break

            # --- C: 检查是否需要压缩上下文 ---
            if self.context.get_token_count() > 6000:
                self.context.compact(keep_last_n=6)

            # --- 生命周期：步结束 ---
            ctx = self.hooks.trigger(HookStage.ON_STEP_END, {
                "session_id": session_id,
                "step_num": step_num,
                "step": step.to_dict(),
            })

        # ---- 5. 如果循环耗尽仍未得出最终答案 ----
        if not final_answer and trajectory:
            # 尝试用 LLM 基于轨迹生成最终答案
            final_answer = self._generate_final_answer_from_trajectory(query, trajectory)

        # ---- 6. V: 评估成功 ----
        eval_result = self.evaluator.evaluate_success(trajectory, final_answer)
        if trajectory:
            eval_result.trajectory = trajectory

        # ---- 7. 生命周期：任务结束 ----
        ctx = self.hooks.trigger(HookStage.ON_TASK_END, {
            "session_id": session_id,
            "final_answer": final_answer,
            "steps": len(trajectory),
            "evaluation": eval_result.to_dict(),
        })

        # ---- 8. 清理状态 ----
        self.state.delete_state(session_id)

        return EngineResult(
            session_id=session_id,
            query=query,
            final_answer=final_answer,
            steps=trajectory,
            evaluation=eval_result,
            total_elapsed_ms=(time.time() - start_time) * 1000,
        )

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _save_checkpoint(self, session_id: str, trajectory: list[StepResult]) -> None:
        """保存执行检查点（用于崩溃恢复）"""
        messages = []
        for msg_dict in self.context.get_full_context():
            # 简化存储，仅保留关键字段
            messages.append({
                "role": msg_dict.get("role", ""),
                "content": str(msg_dict.get("content", ""))[:500],
                "tool_call_id": msg_dict.get("tool_call_id", ""),
            })
        self.state.save_state(session_id, {
            "trajectory": [s.to_dict() for s in trajectory],
            "messages": messages,
        })

    def _generate_final_answer_from_trajectory(
        self, query: str, trajectory: list[StepResult]
    ) -> str:
        """当循环耗尽时，基于轨迹生成最终答案。"""
        summary_parts = []
        for s in trajectory:
            summary_parts.append(f"Step {s.step_num}: {s.thought}")
            for obs in s.observations:
                summary_parts.append(f"  观察: {obs[:200]}")

        summary = "\n".join(summary_parts)
        try:
            response = self.llm.chat([
                {"role": "system", "content": "根据以下执行轨迹，给用户一个最终回答。"},
                {"role": "user", "content": f"任务: {query}\n\n轨迹:\n{summary}\n\n请给出最终回答:"},
            ], tools=None)
            return response.get("content", "抱歉，执行超时，请重试。")
        except Exception:
            return "抱歉，执行过程中遇到问题，请重新尝试。"
