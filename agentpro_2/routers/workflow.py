"""工作流路由 — LangGraph 工作流调用"""

from fastapi import APIRouter

from models.schemas import WorkflowRunRequest, WorkflowRunResponse
from workflows.rag_workflow import rag_workflow_app
from workflows.multi_agent_workflow import multi_agent_workflow_app

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/run", response_model=WorkflowRunResponse)
async def run_workflow(req: WorkflowRunRequest):
    """运行指定工作流。"""
    wf_type = req.workflow_type.lower()

    if wf_type == "rag":
        state = rag_workflow_app.invoke({
            "question": req.task,
            "chat_history": "",
        })
        result = state.get("answer", "")
    elif wf_type == "multi_agent":
        state = multi_agent_workflow_app.invoke({
            "task": req.task,
            "chat_history": "",
        })
        result = state.get("final_answer", "")
    else:
        result = f"未知工作流: {wf_type}，可选: rag / multi_agent"

    return WorkflowRunResponse(workflow_type=wf_type, result=result)
