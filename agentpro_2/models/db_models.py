"""SQLAlchemy 数据库模型"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from core.database import Base


class Conversation(Base):
    """对话记录表"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False)
    role = Column(String(16), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Conversation {self.session_id}:{self.role}>"


class DocumentIndex(Base):
    """文档索引表 — 追踪已入库的文档"""
    __tablename__ = "document_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    chunk_count = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DocumentIndex {self.filename}>"
