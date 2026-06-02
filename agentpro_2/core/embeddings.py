"""Vector embeddings — using fastembed (lightweight, no config files needed)"""

import os
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from config import config

_embeddings: FastEmbedEmbeddings | None = None


def build_embeddings() -> FastEmbedEmbeddings:
    """Create a local FastEmbed embedding instance (lazy singleton).

    Default model: BAAI/bge-small-en-v1.5 (~130MB).
    Uses HF_ENDPOINT mirror for China users.
    """
    global _embeddings
    if _embeddings is None:
        # Force HuggingFace mirror for China network
        if config.HF_ENDPOINT:
            os.environ["HF_ENDPOINT"] = config.HF_ENDPOINT

        _embeddings = FastEmbedEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            cache_dir="./data/models",
        )
    return _embeddings
