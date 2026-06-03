"""SQLAlchemy 数据库模型"""

from sqlalchemy import Column, String, Text, Float, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase
import datetime


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False)
    role = Column(String(16), nullable=False)  # user / assistant / system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False)
    action_type = Column(String(32), nullable=False)  # tool_call / task_start / task_end
    tool_name = Column(String(64), default="")
    tool_args = Column(Text, default="")
    observation = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
