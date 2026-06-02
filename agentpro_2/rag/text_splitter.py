"""文本分割器 — 多种分割策略"""

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)


def get_text_splitter(
    strategy: str = "recursive",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
):
    """获取文本分割器。

    Args:
        strategy: 'recursive' 通用递归分割 / 'markdown' Markdown 结构分割
        chunk_size: 分块大小
        chunk_overlap: 重叠大小
    """
    if strategy == "markdown":
        return MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ],
        )
    # 默认：递归字符分割
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
        keep_separator=True,
    )


def split_documents(
    docs: list,
    strategy: str = "recursive",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list:
    """将文档列表分割为 chunk。"""
    splitter = get_text_splitter(strategy, chunk_size, chunk_overlap)

    if strategy == "markdown":
        # Markdown 分割器不能直接 split_documents
        result = []
        for doc in docs:
            chunks = splitter.split_text(doc.page_content)
            for chunk in chunks:
                result.append(chunk)
        return result

    return splitter.split_documents(docs)
