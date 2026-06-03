"""应用配置管理"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ==================== DeepSeek LLM ====================
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # ==================== FastAPI ====================
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # ==================== Agent Harness ====================
    MAX_STEPS: int = int(os.getenv("MAX_STEPS", "10"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    STATE_DIR: str = os.getenv("STATE_DIR", "./data/state")
    CONTEXT_MAX_TOKENS: int = int(os.getenv("CONTEXT_MAX_TOKENS", "8000"))

    # ==================== 关系型数据库 ====================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/ticketing.db")

    # ==================== 订单 ====================
    SEAT_LOCK_TIMEOUT_SEC: int = int(os.getenv("SEAT_LOCK_TIMEOUT_SEC", "300"))


config = Config()
