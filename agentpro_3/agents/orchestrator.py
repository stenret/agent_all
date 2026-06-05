"""编排 Agent — 多 Agent 调度，自动识别任务类型并路由"""

from harness import DictToolRegistry, EngineResult

from agents.base import HarnessAgent
from agents.show_searcher import ShowSearcherAgent
from agents.ticket_agent import TicketAgent
from agents.customer_service import CustomerServiceAgent


class OrchestratorAgent(HarnessAgent):
    """任务编排器：自动识别用户意图，路由到对应 Agent。

    支持：
    - 搜索演出 → ShowSearcherAgent
    - 选座购票 → TicketAgent
    - 订单/退票 → CustomerServiceAgent
    - 复杂任务 → 顺序调用多个 Agent
    """

    name = "orchestrator"
    description = "智能编排器：自动识别用户需求，调度搜索/购票/客服 Agent 协作完成任务"

    def __init__(self):
        super().__init__()
        self._searcher = ShowSearcherAgent()
        self._ticket = TicketAgent()
        self._cs = CustomerServiceAgent()

    def _get_system_prompt(self) -> str:
        from datetime import date
        today = date.today().strftime("%Y年%m月%d日")
        return f"""你是票务系统的操作员。当前: {today}。

你必须主动调用工具，禁止说"建议去官网/大麦网"，禁止说"系统异常/技术错误"。

工具:
- search_shows: 搜索演出 → 获得 show_id
- get_show_detail(show_id): 查看详情
- check_seats(show_id, section): 查看座位，返回具体座位号如 "C区-H-01"
- lock_seats(show_id, seats): 锁定座位，seats格式如 "C区-H-01"（从check_seats结果中选）
- create_order(show_id, seats, total_price): 创建订单
- pay_order(order_id): 支付
- query_order(order_id): 查询订单
- refund(order_id): 退票
- knowledge_search(query): 知识库检索

购票流程（严格遵守）:
1. 如果用户没指定演出 → 先 search_shows
2. 如果用户没指定分区 → 先 check_seats(show_id) 看概览，然后选最便宜分区
3. 然后 check_seats(show_id, "分区名") 看具体座位号
4. 从可用座位中选一个（如 "C区-H-01"），调用 lock_seats(show_id, "C区-H-01")
5. 锁座成功后 → create_order → pay_order

规则:
1. 对话历史中已有 show_id 直接用，不要重复搜索
2. 用户说"买"/"购票"→ 必须实际调用 check_seats→lock_seats→create_order→pay_order
3. 锁座后自动创建订单并支付，不要停下来问"要不要支付"
4. 支付方式默认微信支付
5. 如果历史中有多个 show，优先选余票最多的
6. 选座时自动选该分区第一个可用座位，不要问用户选哪个"""

    def _build_tools(self) -> DictToolRegistry:
        registry = DictToolRegistry()

        # 注册搜演出的工具
        from tools.show_search import search_shows, get_show_detail
        registry.register(
            "search_shows",
            "多条件搜索演出",
            search_shows,
            {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "show_type": {"type": "string"},
                    "city": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "max_price": {"type": "number"},
                    "limit": {"type": "integer"},
                },
            },
        )
        registry.register(
            "get_show_detail",
            "获取演出详情",
            get_show_detail,
            {
                "type": "object",
                "properties": {"show_id": {"type": "string"}},
                "required": ["show_id"],
            },
        )

        # 注册选座购票的工具
        from tools.seat_manager import check_seats, lock_seats
        from tools.order_manager import create_order
        from tools.payment import pay_order
        registry.register("check_seats", "查看座位", check_seats,
                          {"type": "object", "properties": {"show_id": {"type": "string"}, "section": {"type": "string"}}, "required": ["show_id"]})
        registry.register("lock_seats", "锁定座位", lock_seats,
                          {"type": "object", "properties": {"show_id": {"type": "string"}, "seats": {"type": "string"}, "session_id": {"type": "string"}}, "required": ["show_id", "seats"]})
        registry.register("create_order", "创建订单", create_order,
                          {"type": "object", "properties": {"show_id": {"type": "string"}, "seats": {"type": "string"}, "total_price": {"type": "number"}, "session_id": {"type": "string"}}, "required": ["show_id", "seats", "total_price"]})
        registry.register("pay_order", "支付订单", pay_order,
                          {"type": "object", "properties": {"order_id": {"type": "string"}, "payment_method": {"type": "string"}}, "required": ["order_id"]})

        # 注册客服工具
        from tools.order_manager import query_order, refund
        registry.register("query_order", "查询订单", query_order,
                          {"type": "object", "properties": {"order_id": {"type": "string"}, "session_id": {"type": "string"}}})
        registry.register("refund", "退票", refund,
                          {"type": "object", "properties": {"order_id": {"type": "string"}, "reason": {"type": "string"}}, "required": ["order_id"]})

        # 注册 RAG 知识库检索工具
        from rag.tool import knowledge_search
        registry.register(
            "knowledge_search",
            "知识库检索：查询演出百科、场馆攻略、购票须知等已入库的文档知识。输入搜索关键词返回相关内容。",
            knowledge_search,
            {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "搜索关键词"}},
                "required": ["query"],
            },
        )

        return registry

    def run(self, task: str, session_id: str = "default", max_steps: int | None = None) -> EngineResult:
        """Orchestrator 直接使用自身的 engine + 全部工具来执行。

        引擎会自动根据 system prompt 引导来选择合适的工具链。
        """
        return super().run(task, session_id, max_steps)
