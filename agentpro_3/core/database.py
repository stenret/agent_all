"""数据库模块 — SQLAlchemy 会话管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import config

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库表。"""
    from models.db_models import Base
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """获取数据库会话（FastAPI 依赖注入）。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
