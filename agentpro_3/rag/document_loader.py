"""文档加载器 — 支持 PDF / TXT / Markdown / 网页"""

import os
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    WebBaseLoader,
)

LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
    ".markdown": TextLoader,
}


def load_file(file_path: str) -> list:
    """加载单个文件，自动检测 UTF-8/GBK 编码。"""
    ext = Path(file_path).suffix.lower()
    if ext not in LOADER_MAP:
        raise ValueError(f"不支持的文件格式: {ext}，支持: {list(LOADER_MAP.keys())}")

    if ext == ".pdf":
        return LOADER_MAP[ext](file_path).load()

    for enc in ["utf-8", "gbk", "utf-8-sig"]:
        try:
            loader = TextLoader(file_path, encoding=enc)
            return loader.load()
        except (UnicodeDecodeError, RuntimeError):
            continue
    raise RuntimeError(f"无法解码文件: {file_path}")


def load_url(url: str) -> list:
    """加载网页内容。"""
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
