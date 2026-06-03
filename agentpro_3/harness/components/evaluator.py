"""V: 评估器 — 轨迹记录 + 中途停检 + 目标验证"""

import time

from harness.base import BaseEvaluator
from harness.schema import StepResult, EvaluationResult


class TicketingEvaluator(BaseEvaluator):
    """购票场景评估器。

    中途停检规则：
    - 连续 3 次工具调用失败 → 终止
    - 连续 2 次相同的工具调用（相同参数）→ 终止（死循环）
    - 总步数超限 → 终止（引擎层控制）

    成功评估规则：
    - 最终回答包含"支付成功/出票成功/已购买" → 成功
    - 轨迹中锁座成功但无支付记录 → 部分成功
    - 用户明确表示放弃/取消 → 用户取消
    """

    def __init__(self):
        self._trajectory: list[StepResult] = []
        self._start_time = time.time()

    # ------------------------------------------------------------------
    # BaseEvaluator 接口
    # ------------------------------------------------------------------
    def log_step(self, step: StepResult) -> None:
        self._trajectory.append(step)

    def should_stop(self, step: StepResult, trajectory: list[StepResult]) -> bool:
        """中途停检"""
        all_steps = trajectory if trajectory else self._trajectory

        # 规则1: 连续 3 次失败（工具调用失败 或 LLM调用异常）
        recent = all_steps[-3:]
        if len(recent) >= 3:
            all_failed = True
            for s in recent:
                # 检查工具调用失败
                tool_failed = any(
                    "失败" in obs or "错误" in obs or "Error" in obs
                    for obs in s.observations
                ) if s.observations else False
                # 检查 LLM 调用异常（无工具调用且 thought 包含异常）
                llm_error = (
                    not s.tool_calls
                    and ("异常" in s.thought or "error" in s.thought.lower())
                )
                if not tool_failed and not llm_error:
                    all_failed = False
                    break
            if all_failed:
                return True

        # 规则2: 连续 2 次相同工具+相同参数调用（死循环检测）
        if len(all_steps) >= 2:
            last_two = all_steps[-2:]
            tc1 = [(tc.name, str(tc.args)) for tc in last_two[0].tool_calls]
            tc2 = [(tc.name, str(tc.args)) for tc in last_two[1].tool_calls]
            if tc1 and tc1 == tc2:
                return True

        return False

    def evaluate_success(self, trajectory: list[StepResult],
                         final_answer: str) -> EvaluationResult:
        """评估任务是否成功"""
        all_steps = trajectory if trajectory else self._trajectory

        # 检查是否有支付成功记录
        has_payment = False
        has_lock_seat = False
        user_cancelled = False

        for step in all_steps:
            for obs in step.observations:
                if "支付成功" in obs or "pay 成功" in obs:
                    has_payment = True
                if "锁座成功" in obs or "座位已锁定" in obs:
                    has_lock_seat = True

        # 检查用户是否取消
        cancel_keywords = ["取消", "不要了", "算了", "放弃", "不买了"]
        if any(kw in final_answer for kw in cancel_keywords):
            user_cancelled = True

        if has_payment:
            return EvaluationResult(
                success=True,
                success_reason="支付成功，购票完成",
                trajectory=all_steps,
            )
        elif has_lock_seat:
            return EvaluationResult(
                success=False,
                success_reason="部分成功：座位已锁定但未完成支付",
                trajectory=all_steps,
            )
        elif user_cancelled:
            return EvaluationResult(
                success=None,
                success_reason="用户主动取消",
                trajectory=all_steps,
            )
        else:
            # 检查最终回答是否积极
            positive = any(kw in final_answer for kw in [
                "已购买", "成功", "推荐", "以下是", "找到"
            ])
            return EvaluationResult(
                success=positive,
                success_reason="基于对话内容判断" if positive else "未能完成购票流程",
                trajectory=all_steps,
            )

    def get_report(self) -> dict:
        """获取评估报告"""
        elapsed = time.time() - self._start_time
        return {
            "total_steps": len(self._trajectory),
            "total_elapsed_seconds": round(elapsed, 2),
            "tool_call_count": sum(
                len(s.tool_calls) for s in self._trajectory
            ),
            "failed_steps": sum(
                1 for s in self._trajectory
                if any("失败" in obs or "错误" in obs for obs in s.observations)
            ),
        }
