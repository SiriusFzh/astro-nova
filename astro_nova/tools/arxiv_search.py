"""ArXiv 搜索工具 — 封装现有 scripts/arxiv_search.py"""
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

try:
    from arxiv_search import Paper as ScrapiPaper, search_papers, fetch_by_id as _fetch
except ImportError:
    ScrapiPaper = None
    search_papers = None
    _fetch = None


def search_arxiv(
    query: str,
    max_results: int = 10,
    categories: list[str] = None,
    days_back: Optional[int] = None,
) -> list[dict]:
    """搜索 ArXiv，返回 dict 列表"""
    if search_papers is None:
        return [{"error": "arxiv 库未安装，请执行: pip install arxiv"}]

    cats = categories or ["astro-ph"]
    results = search_papers(query, max_results=max_results, categories=cats, days_back=days_back)
    return [
        {
            "arxiv_id": p.arXiv_ID,
            "title": p.Title,
            "authors": p.Authors[:5],
            "published": p.Published[:10] if p.Published else "",
            "categories": p.Categories,
            "summary": p.Summary[:300],
            "pdf_url": p.PDF_Link,
        }
        for p in results
    ]


def fetch_by_id(arxiv_id: str) -> Optional[dict]:
    """按 ID 获取单篇论文"""
    if _fetch is None:
        return None
    p = _fetch(arxiv_id)
    if not p:
        return None
    return {
        "arxiv_id": p.arXiv_ID,
        "title": p.Title,
        "authors": p.Authors[:5],
        "published": p.Published[:10] if p.Published else "",
        "categories": p.Categories,
        "summary": p.Summary[:500],
        "pdf_url": p.PDF_Link,
        "doi": p.DOI,
    }
