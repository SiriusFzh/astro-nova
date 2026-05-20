"""ArXiv 论文获取工具 — HTML/PDF 双模式，供 LLM 直接调用

与 arxiv_download.py 的区别:
  - arxiv_download 是底层实现
  - arxiv_fetch 是 LLM 可调用的 Tool，支持指定格式 (pdf/html/text)
  - 获取后可直接传递给 paper_reader 进行 LLM 分析

典型 LLM 工作流:
  1. search_arxiv → LLM 决定看哪篇
  2. fetch_arxiv_paper(arxiv_id="...") → 获取全文
  3. read_arxiv_paper → LLM 分析
  4. generate_note → 生成 NovaForge 笔记
"""
from typing import Optional

from astro_nova.tools.arxiv_download import download_and_extract as _download_pdf
from astro_nova.tools.arxiv_search import fetch_by_id as _fetch_meta
from astro_nova.tools.registry import Tool, registry
from astro_nova.utils.logger import logger


async def fetch_arxiv_paper(
    arxiv_id: str,
    format: str = "auto",
) -> dict:
    """获取 arXiv 论文内容

    自动选择最佳格式:
      1. PDF → pymupdf 提取文本
      2. HTML (arXiv HTML5 回退)
      3. 摘要（最低保证）

    Args:
        arxiv_id: arXiv 论文 ID
        format: "auto" (自动) / "pdf" (优先 PDF) / "html" (优先 HTML) / "abstract" (仅摘要)

    Returns:
        {"arxiv_id": ..., "title": ..., "authors": [...],
         "text": "...", "source": "pdf|html|abstract", "has_full_text": bool}
    """
    # 获取元数据
    meta = _fetch_meta(arxiv_id)
    if not meta:
        return {"error": f"未找到 arXiv:{arxiv_id}"}

    title = meta.get("title", "")
    authors = meta.get("authors", [])
    summary = meta.get("summary", "")

    # 获取全文
    text = None
    source = "abstract"

    if format in ("auto", "pdf"):
        text = _download_pdf(arxiv_id)
        if text:
            source = "pdf"

    if not text and format in ("auto", "html"):
        # 尝试 HTML5 全文获取
        from astro_nova.tools.arxiv_download import _fetch_arxiv_html5
        try:
            text = _fetch_arxiv_html5(arxiv_id)
            if text:
                source = "html"
        except Exception as e:
            logger.warning(f"HTML 获取失败: {e}")

    if not text:
        text = summary
        source = "abstract"

    has_full_text = source in ("pdf", "html") and len(text or "") > 1000

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors[:8],
        "published": meta.get("published", ""),
        "categories": meta.get("categories", []),
        "text": text,
        "source": source,
        "has_full_text": has_full_text,
    }


def register_tools():
    registry.register(Tool(
        name="fetch_arxiv_paper",
        description="获取 arXiv 论文全文文本（自动 PDF→HTML→摘要三级回退），返回包含标题、作者、正文的结构化结果",
        parameters={
            "type": "object",
            "properties": {
                "arxiv_id": {
                    "type": "string",
                    "description": "arXiv 论文 ID，如 2301.00001",
                },
                "format": {
                    "type": "string",
                    "enum": ["auto", "pdf", "html", "abstract"],
                    "description": "获取格式: auto=自动, pdf=优先PDF, html=优先HTML, abstract=仅摘要",
                },
            },
            "required": ["arxiv_id"],
        },
        handler=fetch_arxiv_paper,
    ))
