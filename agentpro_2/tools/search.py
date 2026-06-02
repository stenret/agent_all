"""网页搜索工具 — 基于 SerpAPI"""

from langchain_core.tools import Tool
from langchain_community.utilities import SerpAPIWrapper

from config import config

_search_wrapper: SerpAPIWrapper | None = None


def _get_search():
    global _search_wrapper
    if _search_wrapper is None:
        _search_wrapper = SerpAPIWrapper(
            serpapi_api_key=config.SERPAPI_API_KEY,
            params={"engine": "google", "gl": "cn", "hl": "zh-cn"},
        )
    return _search_wrapper


def search_func(query: str) -> str:
    try:
        return _get_search().run(query)
    except Exception as e:
        return f"搜索失败: {e}"


web_search_tool = Tool(
    name="web_search",
    description="网页搜索引擎，用于获取实时信息、事实核查、最新新闻等。输入搜索关键词。",
    func=search_func,
)
