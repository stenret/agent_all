"""HTTP API 调用工具 — 允许 Agent 调用外部 API"""

import json
from langchain_core.tools import Tool
import httpx


def api_caller_func(params_json: str) -> str:
    """调用外部 HTTP API。

    输入 JSON 格式：{"method":"GET","url":"https://...","headers":{},"body":{}}
    """
    try:
        params = json.loads(params_json)
    except json.JSONDecodeError:
        return "错误：输入必须是合法 JSON"

    method = params.get("method", "GET").upper()
    url = params.get("url", "")
    headers = params.get("headers", {})
    body = params.get("body", None)

    if not url:
        return "错误：缺少 URL"

    try:
        with httpx.Client(timeout=30) as client:
            if method == "GET":
                resp = client.get(url, headers=headers)
            elif method == "POST":
                resp = client.post(url, headers=headers, json=body)
            elif method == "PUT":
                resp = client.put(url, headers=headers, json=body)
            elif method == "DELETE":
                resp = client.delete(url, headers=headers)
            else:
                return f"错误：不支持的 HTTP 方法 {method}"

            return f"状态码: {resp.status_code}\n响应:\n{resp.text[:2000]}"
    except Exception as e:
        return f"API 调用失败: {e}"


api_caller_tool = Tool(
    name="api_caller",
    description=(
        "HTTP API 调用工具。输入 JSON: "
        '{"method":"GET/POST/PUT/DELETE","url":"...","headers":{},"body":{}}。'
        "用于调用外部 REST API 获取数据。"
    ),
    func=api_caller_func,
)
