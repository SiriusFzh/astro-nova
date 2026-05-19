"""文档加载器 — 支持 PDF/TXT/MD/HTML"""
import os
import re
import html
from pathlib import Path
from typing import Optional

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None


def load_pdf(filepath: str) -> Optional[str]:
    """用 pymupdf 提取 PDF 文本。"""
    if fitz is None:
        return None
    try:
        doc = fitz.open(filepath)
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()
        return "\n\n".join(pages) if pages else None
    except Exception:
        return None


def load_text(filepath: str) -> str:
    """读取纯文本文件。"""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def load_html(filepath: str) -> str:
    """HTML 转纯文本。"""
    raw = load_text(filepath)
    text = re.sub(r"<style[^>]*>.*?</style>", "", raw, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_document(filepath: str) -> Optional[str]:
    """自动检测类型并加载文档。"""
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        text = load_pdf(filepath)
        if text is None:
            # pymupdf 失败时尝试用文本模式提取
            try:
                import io
                from pdfminer.high_level import extract_text
                text = extract_text(filepath)
            except ImportError:
                pass
        return text
    elif ext in (".txt", ".md", ".text"):
        return load_text(filepath)
    elif ext == ".html":
        return load_html(filepath)
    return None


def scan_directory(dirpath: str, extensions: set = None) -> list[dict]:
    """扫描目录下所有支持的文件，返回 [{path, title}]"""
    if extensions is None:
        extensions = {".pdf", ".txt", ".md", ".html"}
    results = []
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in extensions:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, dirpath)
                results.append({"path": full, "title": rel})
    return results
