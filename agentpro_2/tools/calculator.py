"""安全计算器工具"""

import math
from langchain_core.tools import Tool


def calculator_func(expression: str) -> str:
    """安全数学表达式求值。"""
    allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    allowed["__builtins__"] = {}
    try:
        return str(eval(expression, {"__builtins__": {}}, allowed))
    except Exception as e:
        return f"计算错误: {e}"


calculator_tool = Tool(
    name="calculator",
    description="数学表达式计算器，支持 math 模块函数。输入如 '2+3*4'、'sqrt(16)'。",
    func=calculator_func,
)
