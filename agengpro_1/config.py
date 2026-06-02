"""应用配置管理 — 从环境变量加载配置，提供默认值"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # DeepSeek API
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")  # deepseek-chat / deepseek-coder

    # SerpAPI
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "your-serpapi-key")

    # FastAPI
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Agent
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "6"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    VERBOSE: bool = os.getenv("VERBOSE", "true").lower() == "true"


config = Config()
