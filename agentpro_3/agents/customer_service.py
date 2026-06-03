"""客服 Agent — 售后处理：订单查询、退票"""

from harness import DictToolRegistry
from harness.prompt import PromptManager

from agents.base import HarnessAgent
from tools.order_manager import query_order, refund


class CustomerServiceAgent(HarnessAgent):
    name = "customer_service"
    description = "客服专家：处理订单查询、退票、售后咨询"

    def _get_system_prompt(self) -> str:
        pm = PromptManager()
        pm.register("customer_service", """你是一个专业的演出票务客服助手。

你的职责：
1. 帮助用户查询订单状态
2. 处理退票申请
3. 解答票务相关问题
4. 安抚用户情绪，提供满意的解决方案

服务规范：
- 查询订单需要 order_id
- 退票仅支持已支付订单
- 退票后 3-5 个工作日内退款
- 对用户的问题保持耐心和专业态度""")
        return pm.render("customer_service")

    def _build_tools(self) -> DictToolRegistry:
        registry = DictToolRegistry()
        registry.register(
            "query_order",
            "查询订单状态。可通过订单ID精确查询或会话ID批量查询。",
            query_order,
            {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单ID"},
                    "session_id": {"type": "string", "description": "会话ID"},
                },
            },
        )
        registry.register(
            "refund",
            "退票。仅已支付订单可退票。",
            refund,
            {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单ID"},
                    "reason": {"type": "string", "description": "退票原因"},
                },
                "required": ["order_id"],
            },
        )
        return registry


class RefundTool:
    """退票工具包装"""
    pass
