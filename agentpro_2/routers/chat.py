"""Unified chat — Agent with RAG + tools + multi-turn memory"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from models.schemas import ChatRequest, ChatResponse, SessionHistoryResponse
from models.db_models import Conversation
from core.database import get_db, SessionLocal
from core.llm import build_llm

# All tools
from rag.tool import knowledge_search_tool
from tools.search import web_search_tool
from tools.calculator import calculator_tool
from tools.python_repl import python_repl_tool
from tools.api_caller import api_caller_tool
from tools.database_query import db_query_tool

ALL_TOOLS = [
    knowledge_search_tool,
    web_search_tool,
    calculator_tool,
    python_repl_tool,
    api_caller_tool,
    db_query_tool,
]

router = APIRouter(prefix="/chat", tags=["chat"])

# ---------------------------------------------------------------------------
# Agent Prompt — lets the agent decide how to answer
# ---------------------------------------------------------------------------
CHAT_PROMPT = PromptTemplate.from_template("""You are an intelligent assistant with access to a set of tools.
You can search a local knowledge base, search the web, run Python code, do math, call APIs, and query a database.

**IMPORTANT decision flow:**
1. If the question is about stored documents/internal knowledge → use `knowledge_search`
2. If knowledge_search returns nothing → try `web_search` or answer from your own knowledge
3. If it's math/computation → use `calculator` or `python_repl`
4. If it's about database data → use `database_query`
5. For general questions → answer directly using your own knowledge, NO tool needed

Available tools:
{tools}

Tool names: {tool_names}

Use this EXACT format:
Question: the user's question
Thought: what should I do next?
Action: one of [{tool_names}]
Action Input: the input to the action
Observation: result from the tool
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: your final answer to the user

Begin!

Conversation history:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}""")

# In-memory conversation memory (per session)
from langchain_classic.memory import ConversationBufferMemory

_memories: dict[str, ConversationBufferMemory] = {}


def _get_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in _memories:
        _memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True, input_key="input"
        )
    return _memories[session_id]


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------
@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """Unified agent: RAG + web search + calculator + code + API + DB."""

    # Build agent
    llm = build_llm()
    memory = _get_memory(req.session_id)
    agent = create_react_agent(llm=llm, tools=ALL_TOOLS, prompt=CHAT_PROMPT)
    executor = AgentExecutor.from_agent_and_tools(
        agent=agent, tools=ALL_TOOLS, memory=memory,
        verbose=True, max_iterations=8, handle_parsing_errors=True,
    )

    # Run
    result = executor.invoke({"input": req.message})
    reply = result.get("output", "Sorry, something went wrong.")

    # Persist to DB
    db.add(Conversation(session_id=req.session_id, role="user", content=req.message))
    db.add(Conversation(session_id=req.session_id, role="assistant", content=reply))
    db.commit()

    return ChatResponse(session_id=req.session_id, reply=reply)


# ---------------------------------------------------------------------------
# GET /chat/{session_id}/history
# ---------------------------------------------------------------------------
@router.get("/{session_id}/history")
async def get_history(session_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id)
        .order_by(Conversation.created_at.asc())
        .all()
    )
    return SessionHistoryResponse(
        session_id=session_id,
        messages=[
            {"role": r.role, "content": r.content, "time": str(r.created_at)}
            for r in records
        ],
    )


# ---------------------------------------------------------------------------
# GET /chat/sessions — list all sessions
# ---------------------------------------------------------------------------
from sqlalchemy import func, distinct


@router.get("/sessions")
async def list_sessions(db: Session = Depends(get_db)):
    """List all session IDs with message counts and last activity."""
    rows = (
        db.query(
            Conversation.session_id,
            func.count(Conversation.id).label("msg_count"),
            func.max(Conversation.created_at).label("last_active"),
        )
        .group_by(Conversation.session_id)
        .order_by(func.max(Conversation.created_at).desc())
        .all()
    )
    return [
        {
            "session_id": r.session_id,
            "message_count": r.msg_count,
            "last_active": str(r.last_active),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /chat/all — all conversations (with optional limit)
# ---------------------------------------------------------------------------
@router.get("/all")
async def get_all_conversations(
    limit: int = 50,
    session_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Get all or filtered conversations.

    Query params:
        limit: max records (default 50)
        session_id: filter by session (optional, returns all if omitted)
    """
    q = db.query(Conversation)
    if session_id:
        q = q.filter(Conversation.session_id == session_id)
    records = q.order_by(Conversation.created_at.desc()).limit(limit).all()

    return {
        "total": len(records),
        "conversations": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "role": r.role,
                "content": r.content,
                "time": str(r.created_at),
            }
            for r in records
        ],
    }
