"""ArXiv PDF 下载工具 — 封装现有 scripts/arxiv_download.py"""
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

try:
    from arxiv_download import download_pdf, extract_text, fetch_and_extract
except ImportError:
    download_pdf = None
    extract_text = None
    fetch_and_extract = None


def download_and_extract(arxiv_id: str, output_dir: str = None) -> Optional[str]:
    """下载 PDF 并提取文本"""
    if fetch_and_extract is None:
        return None
    out = output_dir or os.path.join(os.path.expanduser("~"), ".astro-nova", "papers")
    return fetch_and_extract(arxiv_id, out)


def extract_pdf_text(pdf_path: str) -> Optional[str]:
    """从本地 PDF 提取文本"""
    if extract_text is None:
        return None
    return extract_text(pdf_path)
