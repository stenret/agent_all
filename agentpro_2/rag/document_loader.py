"""文档加载器 — 支持 PDF / TXT / Markdown / 网页"""

import os
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    WebBaseLoader,
)

# Supported extensions → loader (md files use TextLoader)
LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
    ".markdown": TextLoader,
}


def load_file(file_path: str) -> list:
    """Load a single file, return Document list. Auto-detects UTF-8/GBK encoding."""
    ext = Path(file_path).suffix.lower()
    if ext not in LOADER_MAP:
        raise ValueError(f"Unsupported format: {ext}, supported: {list(LOADER_MAP.keys())}")

    if ext == ".pdf":
        return LOADER_MAP[ext](file_path).load()

    # Text-based files: try utf-8 first, fallback to gbk
    for enc in ["utf-8", "gbk", "utf-8-sig"]:
        try:
            loader = TextLoader(file_path, encoding=enc)
            return loader.load()
        except (UnicodeDecodeError, RuntimeError):
            continue
    raise RuntimeError(f"Cannot decode file with any encoding: {file_path}")


def load_url(url: str) -> list:
    """加载网页内容，返回 Document 列表。"""
    loader = WebBaseLoader(url)
    return loader.load()


def load_directory(dir_path: str) -> list:
    """批量加载目录下所有支持的文档。"""
    all_docs = []
    for root, _, files in os.walk(dir_path):
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in LOADER_MAP:
                try:
                    docs = load_file(os.path.join(root, fname))
                    all_docs.extend(docs)
                except Exception as e:
                    print(f"[WARN] 加载失败 {fname}: {e}")
    return all_docs
