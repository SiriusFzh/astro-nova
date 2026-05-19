"""文本分块 — 支持按段落/大小分割，带重叠"""
import re
from typing import Generator


def split_paragraphs(text: str) -> list[str]:
    """按空行分割段落，过滤掉过短的片段。"""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if len(p.strip()) > 50]


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[str]:
    """将文本分割为固定大小的块，带重叠。

    Args:
        text: 输入文本
        chunk_size: 每块最大字符数
        chunk_overlap: 相邻块重叠字符数
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end == text_len:
            break

        next_start = end - chunk_overlap
        # 尝试在句子边界断开
        if next_start > start:
            # 找上一个句号/换行
            cut = text.rfind(". ", start + chunk_size - chunk_overlap * 2, end)
            if cut == -1:
                cut = text.rfind("\n", start + chunk_size - chunk_overlap * 2, end)
            if cut != -1 and cut > start:
                chunks[-1] = text[start:cut + 1].strip()
                start = cut + 1
                continue

        start = next_start

    return chunks


def chunk_document(text: str, strategy: str = "smart", **kwargs) -> list[str]:
    """智能分块入口。

    Args:
        text: 输入文本
        strategy: "smart"=先按段落再按大小, "simple"=直接按大小
    """
    if strategy == "smart":
        paragraphs = split_paragraphs(text)
        if len(paragraphs) <= 1:
            return chunk_text(text, **kwargs)

        chunks = []
        for para in paragraphs:
            if len(para) <= kwargs.get("chunk_size", 1000):
                chunks.append(para)
            else:
                chunks.extend(chunk_text(para, **kwargs))
        return chunks
    else:
        return chunk_text(text, **kwargs)
