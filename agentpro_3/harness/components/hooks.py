"""L: 生命周期钩子 — 横切注入：日志/策略/权限/审计"""

import logging
import time
from typing import Callable

from harness.base import BaseHookManager
from harness.schema import HookStage

logger = logging.getLogger("agent_harness.hooks")


class SimpleHookManager(BaseHookManager):
    """简单的钩子管理器。

    支持在每个生命周期阶段注册多个钩子函数。
    内置默认钩子：日志记录。
    """

    def __init__(self, enable_logging: bool = True):
        self._hooks: dict[HookStage, list[Callable[[dict], dict]]] = {
            stage: [] for stage in HookStage
        }
        self._audit_trail: list[dict] = []

        if enable_logging:
            self._register_defaults()

    # ------------------------------------------------------------------
    # BaseHookManager 接口
    # ------------------------------------------------------------------
    def trigger(self, stage: HookStage, context: dict) -> dict:
        """触发指定阶段的所有钩子，链式传递 context"""
        result = context
        for hook in self._hooks.get(stage, []):
            try:
                result = hook(result) or result
            except Exception as e:
                logger.warning(f"Hook error at {stage.value}: {e}")
        return result

    def register(self, stage: HookStage, hook: Callable[[dict], dict]) -> None:
        self._hooks[stage].append(hook)

    # ------------------------------------------------------------------
    # 默认钩子
    # ------------------------------------------------------------------
    def _register_defaults(self) -> None:
        """注册默认的日志和审计钩子"""
        self.register(HookStage.ON_TASK_START, self._log_task_start)
        self.register(HookStage.ON_BEFORE_ACTION, self._log_before_action)
        self.register(HookStage.ON_AFTER_ACTION, self._audit_action)
        self.register(HookStage.ON_TASK_END, self._log_task_end)

    def _log_task_start(self, ctx: dict) -> dict:
        logger.info(f"[TASK_START] session={ctx.get('session_id')} query={ctx.get('query', '')[:80]}")
        self._audit_trail.append({
            "type": "task_start",
            "timestamp": time.time(),
            "session_id": ctx.get("session_id"),
            "query": ctx.get("query", "")[:200],
        })
        return ctx

    def _log_before_action(self, ctx: dict) -> dict:
        logger.debug(f"[BEFORE_ACTION] step={ctx.get('step_num')} tool={ctx.get('tool_name')} args={ctx.get('tool_args')}")
        return ctx

    def _audit_action(self, ctx: dict) -> dict:
        """审计记录：所有工具调用 + 结果"""
        entry = {
            "type": "tool_call",
            "timestamp": time.time(),
            "session_id": ctx.get("session_id"),
            "step_num": ctx.get("step_num"),
            "tool_name": ctx.get("tool_name"),
            "tool_args": ctx.get("tool_args"),
            "observation": str(ctx.get("observation", ""))[:500],
        }
        self._audit_trail.append(entry)
        return ctx

    def _log_task_end(self, ctx: dict) -> dict:
        logger.info(f"[TASK_END] session={ctx.get('session_id')} steps={ctx.get('steps')} "
                    f"success={ctx.get('evaluation', {}).get('success')}")
        return ctx

    # ------------------------------------------------------------------
    # 审计查询
    # ------------------------------------------------------------------
    def get_audit_trail(self) -> list[dict]:
        return self._audit_trail

    def get_session_audit(self, session_id: str) -> list[dict]:
        return [e for e in self._audit_trail if e.get("session_id") == session_id]

    def clear_audit(self) -> None:
        self._audit_trail = []
