"""演出搜索 Agent"""

from harness import DictToolRegistry
from harness.prompt import PromptManager

from agents.base import HarnessAgent
from tools.show_search import search_shows, get_show_detail


class ShowSearcherAgent(HarnessAgent):
    name = "show_searcher"
    description = "演出搜索专家：帮助用户按城市、类型、日期、价格搜索匹配的演出，支持详情查看"

    def _get_system_prompt(self) -> str:
        from datetime import date
        today = date.today().strftime("%Y年%m月%d日")
        pm = PromptManager()
        pm.register("show_searcher", f"""你是一个专业的演出搜索助手。当前日期: {today}。

你的职责：
1. 根据用户需求搜索演出（按城市、类型、日期、预算等）
2. 列出最匹配的演出供用户选择
3. 提供详细的演出信息帮助用户决策
4. 对售罄的演出诚实告知并推荐替代方案

工具使用指引：
- search_shows: 多条件搜索演出（keyword/type/city/date/max_price）
- get_show_detail: 根据 show_id 查看演出详情（座位分区、价格等）

交互规范：
- 如果搜索结果很多，列 TOP 5 并询问用户偏好
- 如果搜索结果为空，建议用户放宽条件
- 用户选定后，提示"如需购票，请告知，我将为您转接购票服务"
- 不要执行购票操作
- 搜索日期请用{today.split("年")[0]}年""")
        return pm.render("show_searcher")

    def _build_tools(self) -> DictToolRegistry:
        registry = DictToolRegistry()
        registry.register(
            "search_shows",
            "多条件搜索演出。按关键词、类型(演唱会/话剧/音乐剧/音乐会/脱口秀/展览/体育)、城市(北京/上海/广州/深圳/成都/杭州)、日期范围、最高票价筛选。",
            search_shows,
            {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词"},
                    "show_type": {"type": "string", "description": "演出类型"},
                    "city": {"type": "string", "description": "城市"},
                    "date_from": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                    "date_to": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
                    "max_price": {"type": "number", "description": "最高票价"},
                    "limit": {"type": "integer", "description": "返回条数，默认5"},
                },
            },
        )
        registry.register(
            "get_show_detail",
            "获取演出详细信息，包括场馆地址、座位分区、票价档位。",
            get_show_detail,
            {
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "演出ID"},
                },
                "required": ["show_id"],
            },
        )
        return registry
