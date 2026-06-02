"""分析 Agent — 擅长数据分析、文档解读、数据库查询"""

from agents.base import BaseAgent
from tools.database_query import db_query_tool
from tools.calculator import calculator_tool


class AnalystAgent(BaseAgent):
    name = "analyst"
    description = "分析专家：擅长数据分析、文档解读、SQL 查询、统计计算"

    tools = [db_query_tool, calculator_tool]

    prompt_template = """你是一名资深数据分析师，具备以下能力：
- 查询数据库获取结构化数据
- 进行统计分析和数学计算
- 解读数据并提取洞察
- 撰写分析报告

可用工具：
{tools}

工具名称：{tool_names}

严格按 ReAct 格式回复：
Question: 用户的问题
Thought: 思考接下来应该做什么
Action: 动作（{tool_names} 之一）
Action Input: 动作输入
Observation: 结果
... (可重复)
Thought: 最终结论
Final Answer: 对用户的最终回答（用数据支撑你的结论）

Question: {input}
Thought: {agent_scratchpad}"""
