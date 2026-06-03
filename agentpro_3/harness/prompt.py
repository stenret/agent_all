"""Prompt 管理器 — YAML/字典模板加载与渲染"""

from typing import Any


class PromptManager:
    """管理 Agent 的 prompt 模板，支持变量替换。"""

    def __init__(self, templates: dict[str, str] | None = None):
        self._templates: dict[str, str] = templates or {}

    def register(self, name: str, template: str) -> None:
        self._templates[name] = template

    def get(self, name: str) -> str:
        if name not in self._templates:
            raise KeyError(f"Prompt template '{name}' not found. Available: {list(self._templates.keys())}")
        return self._templates[name]

    def render(self, name: str, **variables: Any) -> str:
        """渲染模板，替换 {variable} 占位符。"""
        template = self.get(name)
        try:
            return template.format(**variables)
        except KeyError as e:
            missing = e.args[0]
            raise KeyError(f"Missing variable '{missing}' in prompt '{name}'") from e


# ---------------------------------------------------------------------------
# 购票系统默认 Prompt 模板
# ---------------------------------------------------------------------------
DEFAULT_PROMPTS = {
    "system": """你是一个专业的演出票务助手，负责帮助用户搜索演出、查看座位、购买门票。

你的工作原则：
1. 准确理解用户需求（想看什么类型、什么时间、预算多少）
2. 先查询再推荐，不要编造演出信息
3. 购票前必须确认用户对座位和价格满意
4. 每一步操作都要向用户说明

当前可用的工具会在每次对话中提供给你。请根据用户需求选择合适的工具。

<重要规则>
- 搜索演出使用 search_shows 工具
- 查看座位使用 check_seats 工具
- 锁定座位使用 lock_seats 工具（锁定后有5分钟支付时间）
- 支付使用 pay_order 工具
- 查询订单使用 query_order 工具
- 退票使用 refund 工具
- 不要重复调用已成功的工具
- 如果工具返回错误，分析原因后重新尝试或告知用户
</重要规则>""",

    "ticket_agent": """你是一个演出票务购买专家。你的职责是帮助用户完成从搜索到支付的全流程。

{system_prompt}

<当前上下文>
用户需求: {query}
</当前上下文>

请一步一步执行：先搜索演出 → 确认用户选择 → 查看座位 → 锁定 → 支付。""",

    "show_searcher": """你是一个演出信息搜索专家。你的职责是帮助用户找到合适的演出。

{system_prompt}

<当前上下文>
用户需求: {query}
</当前上下文>

请搜索演出并给出推荐。注意：如果有多个匹配结果，列出 TOP 5 供用户选择。""",

    "customer_service": """你是一个演出票务客服专家。你的职责是处理售后问题：订单查询、退票、投诉建议。

{system_prompt}

<当前上下文>
用户问题: {query}
</当前上下文>

请耐心处理用户的问题。涉及退票时，确认用户身份后按流程处理。""",
}
