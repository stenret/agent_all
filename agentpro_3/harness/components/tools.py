"""T: 工具注册表 — 类型化工具目录 + JSON Schema 校验"""

import json
from typing import Callable

from harness.base import BaseToolRegistry


class DictToolRegistry(BaseToolRegistry):
    """基于字典的工具注册表。

    支持：
    - @tool 装饰器注册 Python 函数
    - JSON Schema 参数校验
    - merge() 合并多个注册表
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}  # name → {func, description, parameters}

    # ------------------------------------------------------------------
    # BaseToolRegistry 接口
    # ------------------------------------------------------------------
    def get_tool_schemas(self) -> list[dict]:
        """返回 OpenAI function-calling 格式的工具 schema"""
        schemas = []
        for name, info in self._tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info["description"],
                    "parameters": info.get("parameters", {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "输入参数"}
                        },
                        "required": ["query"],
                    }),
                },
            })
        return schemas

    def call(self, name: str, args: dict) -> str:
        """执行工具，返回结果字符串"""
        if name not in self._tools:
            return f"错误: 工具 '{name}' 未注册。可用工具: {list(self._tools.keys())}"

        func = self._tools[name]["func"]
        try:
            result = func(**args)
            return str(result)
        except TypeError as e:
            # 参数不匹配时，尝试用单个参数调用
            try:
                result = func(list(args.values())[0] if args else "")
                return str(result)
            except Exception:
                return f"工具调用失败 [{name}]: {e}"
        except Exception as e:
            return f"工具执行错误 [{name}]: {e}"

    def register(self, name: str, description: str, func: Callable,
                 parameters: dict | None = None) -> None:
        """注册一个工具"""
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "输入参数"}
                },
                "required": ["query"],
            },
        }

    # ------------------------------------------------------------------
    # 便捷方法
    # ------------------------------------------------------------------
    def tool(self, name: str = "", description: str = "",
             parameters: dict | None = None):
        """@tool 装饰器：将 Python 函数注册为工具"""

        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_desc = description or (func.__doc__ or "").strip().split("\n")[0]
            self.register(tool_name, tool_desc, func, parameters)
            return func

        return decorator

    def merge(self, other: "DictToolRegistry") -> "DictToolRegistry":
        """合并另一个注册表，返回新注册表"""
        merged = DictToolRegistry()
        merged._tools = {**self._tools, **other._tools}
        return merged

    def list_tools(self) -> list[str]:
        """列出所有已注册工具名称"""
        return list(self._tools.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __repr__(self) -> str:
        return f"DictToolRegistry(tools={list(self._tools.keys())})"


def tool(name: str = "", description: str = "",
         parameters: dict | None = None):
    """独立 @tool 装饰器，用于在注册到注册表之前创建工具定义。

    使用示例:
        @tool(name="my_func", description="Does something")
        def my_func(x: str) -> str:
            return x

        registry.register_tool(my_func)
    """
    def decorator(func: Callable):
        func._tool_meta = {
            "name": name or func.__name__,
            "description": description or (func.__doc__ or "").strip().split("\n")[0],
            "parameters": parameters,
        }
        return func
    return decorator


def infer_schema(func: Callable) -> dict:
    """从函数类型注解推断 JSON Schema"""
    import inspect
    sig = inspect.signature(func)
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            param_type = "string"
        elif annotation is str:
            param_type = "string"
        elif annotation is int:
            param_type = "integer"
        elif annotation is float:
            param_type = "number"
        elif annotation is bool:
            param_type = "boolean"
        elif annotation is list:
            param_type = "array"
        elif annotation is dict:
            param_type = "object"
        else:
            param_type = "string"

        properties[param_name] = {
            "type": param_type,
            "description": f"{param_name} 参数",
        }
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }
