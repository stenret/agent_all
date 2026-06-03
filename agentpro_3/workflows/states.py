"""工作流状态定义"""

from typing import TypedDict


class TicketingWorkflowState(TypedDict, total=False):
    """购票工作流状态"""
    session_id: str
    task: str  # 用户任务
    intent: str  # 识别的意图: search / buy / after_sales
    show_id: str
    seats: str
    order_id: str
    result: str
    final_answer: str
