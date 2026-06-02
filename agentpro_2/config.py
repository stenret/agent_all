"""应用配置管理"""

import os
from dotenv import load_dotenv

load_dotenv()

# 必须在任何 HuggingFace 相关导入之前设置镜像
_hf = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
os.environ["HF_ENDPOINT"] = _hf
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"


class Config:
    # ==================== DeepSeek LLM ====================
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # ==================== SerpAPI 搜索 ====================
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "your-serpapi-key")

    # ==================== Vector DB (ChromaDB) ====================
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "knowledge_base")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"
    )
    HF_ENDPOINT: str = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")

    # ==================== 检索优化 ====================
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    RERANK_ENABLED: bool = os.getenv("RERANK_ENABLED", "true").lower() == "true"
    HYBRID_SEARCH_ENABLED: bool = os.getenv("HYBRID_SEARCH_ENABLED", "true").lower() == "true"

    # ==================== 关系型数据库 ====================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

    # ==================== FastAPI ====================
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # ==================== Agent ====================
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "6"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    # ==================== 文件 ====================
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))


config = Config()
