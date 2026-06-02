"""LangChain 工具集：Python 代码沙箱、网页搜索、计算器"""

import math
from langchain_core.tools import Tool
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_community.utilities import SerpAPIWrapper

from config import config


# ---------- 1. Python 代码沙箱 ----------
python_repl = PythonREPLTool(
    name="python_repl",
    description=(
        "Python 代码执行沙箱。输入一段有效的 Python 代码，返回执行结果。"
        "适用于：数学计算、数据处理、算法实现、复杂逻辑等。"
        "注意：无法通过网络访问，不可执行长时间阻塞操作。"
    ),
)

python_repl.handle_validation_error = True


# ---------- 2. 网页搜索 (SerpAPI) ----------
_search_wrapper: SerpAPIWrapper | None = None


def _get_search():
    global _search_wrapper
    if _search_wrapper is None:
        _search_wrapper = SerpAPIWrapper(
            serpapi_api_key=config.SERPAPI_API_KEY,
            params={"engine": "google", "gl": "cn", "hl": "zh-cn"},
        )
    return _search_wrapper


def search_tool_func(query: str) -> str:
    """执行一次网页搜索，返回摘要结果。"""
    try:
        wrapper = _get_search()
        return wrapper.run(query)
    except Exception as e:
        return f"搜索失败: {e}"


web_search = Tool(
    name="web_search",
    description=(
        "网页搜索引擎，当需要获取实时信息、事实核查、最新新闻、"
        "百科知识等时使用。输入搜索关键词，返回相关网页摘要。"
    ),
    func=search_tool_func,
)


# ---------- 3. 计算器 ----------
def calculator_func(expression: str) -> str:
    """安全的数学表达式求值，支持 math 模块常用函数。"""
    allowed_names = {
        k: v
        for k, v in math.__dict__.items()
        if not k.startswith("_")
    }
    allowed_names["__builtins__"] = {}

    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


calculator = Tool(
    name="calculator",
    description=(
        "数学表达式计算器。输入数学表达式（如 '2+3*4'、'sqrt(16)'、"
        "'sin(pi/2)'、'factorial(5)'），返回计算结果。"
        "支持 math 模块的所有函数。"
    ),
    func=calculator_func,
)


# ---------- 工具列表 ----------
ALL_TOOLS = [python_repl, web_search, calculator]
