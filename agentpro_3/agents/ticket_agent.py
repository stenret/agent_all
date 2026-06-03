"""购票执行 Agent"""

from harness import DictToolRegistry
from harness.prompt import PromptManager

from agents.base import HarnessAgent
from tools.seat_manager import check_seats, lock_seats
from tools.order_manager import create_order
from tools.payment import pay_order


class TicketAgent(HarnessAgent):
    name = "ticket_agent"
    description = "购票执行专家：负责查看座位、锁定座位、创建订单、完成支付"

    def _get_system_prompt(self) -> str:
        from datetime import date
        today = date.today().strftime("%Y年%m月%d日")
        pm = PromptManager()
        pm.register("ticket_agent", f"""你是一个专业的演出票务购买助手。当前日期: {today}。

你的职责：
1. 帮助用户查看演出可用座位
2. 根据用户选择锁定座位
3. 创建订单并完成支付
4. 处理购票过程中的异常（座位被抢、支付失败等）

购票流程（严格按顺序）：
Step 1: check_seats — 查看座位情况
Step 2: lock_seats — 锁定用户指定的座位（需确认 show_id + 座位号）
Step 3: create_order — 创建订单
Step 4: pay_order — 执行支付

重要规则：
- 锁座前必须让用户确认要锁定的座位
- 锁座成功后必须在 5 分钟内完成支付
- 支付失败时告知用户可重试
- 不要凭空捏造演出信息，所有数据来自工具返回结果""")
        return pm.render("ticket_agent")

    def _build_tools(self) -> DictToolRegistry:
        registry = DictToolRegistry()
        registry.register(
            "check_seats",
            "查看演出可用座位。可指定分区查看详细座位，或不指定查看概览。",
            check_seats,
            {
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "演出ID"},
                    "section": {"type": "string", "description": "分区名称（可选）"},
                    "limit": {"type": "integer", "description": "最多显示座位数"},
                },
                "required": ["show_id"],
            },
        )
        registry.register(
            "lock_seats",
            "锁定指定座位（锁定后5分钟内需支付）。",
            lock_seats,
            {
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "演出ID"},
                    "seats": {"type": "string", "description": "座位列表，逗号分隔，如: A区-A-03,A区-A-04"},
                    "session_id": {"type": "string", "description": "会话ID"},
                },
                "required": ["show_id", "seats"],
            },
        )
        registry.register(
            "create_order",
            "创建购票订单（锁座成功后调用）。",
            create_order,
            {
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "演出ID"},
                    "seats": {"type": "string", "description": "已锁定的座位列表"},
                    "total_price": {"type": "number", "description": "总价格"},
                    "session_id": {"type": "string", "description": "会话ID"},
                },
                "required": ["show_id", "seats", "total_price"],
            },
        )
        registry.register(
            "pay_order",
            "支付订单。支持微信支付/支付宝/银行卡。",
            pay_order,
            {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单ID"},
                    "payment_method": {"type": "string", "description": "支付方式：微信支付/支付宝/银行卡"},
                },
                "required": ["order_id"],
            },
        )
        return registry
