"""数据库查询工具 — 允许 Agent 通过 SQL 查询本地数据库"""

from langchain_core.tools import Tool
from sqlalchemy import text

from core.database import SessionLocal


def db_query_func(sql: str) -> str:
    """执行只读 SQL 查询并返回结果。"""
    # 安全检查：只允许 SELECT
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT"):
        return "错误：仅允许 SELECT 查询"

    try:
        with SessionLocal() as session:
            result = session.execute(text(sql))
            rows = result.fetchall()
            if not rows:
                return "查询结果为空"
            cols = list(result.keys())
            lines = [", ".join(cols)]
            for row in rows[:50]:  # 最多返回 50 行
                lines.append(", ".join(str(v) for v in row))
            return "\n".join(lines)
    except Exception as e:
        return f"数据库查询失败: {e}"


db_query_tool = Tool(
    name="database_query",
    description=(
        "数据库查询工具，执行只读 SQL 查询（仅支持 SELECT）。"
        "用于查询对话记录、文档索引等结构化数据。"
    ),
    func=db_query_func,
)
