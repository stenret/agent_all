"""Vector embeddings — 使用 FastEmbed 本地模型，无需联网"""

import os

# 优先使用本地缓存，避免首次使用时联网下载超时
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from config import config

_embeddings: FastEmbedEmbeddings | None = None


def build_embeddings() -> FastEmbedEmbeddings:
    """创建本地 FastEmbed 向量编码器（延迟单例）。

    默认模型: BAAI/bge-small-zh-v1.5（中英文双语，约 130MB）。
    通过 HF_ENDPOINT 镜像加速国内下载；设置 HF_HUB_OFFLINE=1 强制离线。
    """
    global _embeddings
    if _embeddings is None:
        if config.HF_ENDPOINT:
            os.environ["HF_ENDPOINT"] = config.HF_ENDPOINT

        _embeddings = FastEmbedEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            cache_dir="./data/models",
        )
    return _embeddings
