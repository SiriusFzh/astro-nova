"""ArXiv PDF 下载工具 — PDF + HTML 双模式下载

PDF 下载失败时自动回退到 HTML 全文模式。
注册为 Tool 供 LLM 自主使用。

v3: 修复 arxiv 库 v4 API 兼容性（download_pdf 已移除），
     直连 PDF + pymupdf 提取正文，HTML5 fallback，摘要兜底。
"""
import os
import re
import logging
from typing import Optional
from pathlib import Path

from astro_nova.utils.logger import logger
from astro_nova.utils.proxy import create_https_connection


def _get_arxiv_pdf_url(arxiv_id: str) -> Optional[str]:
    """用官方 arxiv 库获取版本化的 PDF URL（如 xxx.pdf/2301.00001v1）

    arxiv v4 移除了 download_pdf()，我们用它获取准确的 versioned PDF URL，
    再用自己的 HTTP 下载。
    """
    try:
        import arxiv
        client = arxiv.Client(page_size=1, delay_seconds=1, num_retries=2)
        search = arxiv.Search(id_list=[arxiv_id])
        results = list(client.results(search))
        if results and results[0].pdf_url:
            return results[0].pdf_url
    except ImportError:
        logger.warning("arxiv 库未安装，跳过")
    except Exception as e:
        logger.warning(f"arxiv 库获取 URL 失败: {e}")
    return None


def _download_pdf(url: str, dest: str) -> Optional[str]:
    """用 http.client 下载 PDF 到本地（支持代理）"""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname
    path = parsed.path
    conn = create_https_connection(host, timeout=120)
    try:
        conn.request("GET", path, headers={"User-Agent": "AstroNova/1.0"})
        resp = conn.getresponse()
        if resp.status != 200:
            logger.warning(f"PDF 下载 HTTP {resp.status}: {url}")
            return None
        total = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
        logger.info(f"PDF 下载成功: {dest} ({total} bytes)")
        return dest
    except Exception as e:
        logger.warning(f"PDF 下载异常: {e}")
        return None
    finally:
        conn.close()


def _fetch_arxiv_html(arxiv_id: str) -> Optional[str]:
    """从 arXiv HTML5 页面提取论文全文（PDF 下载失败时的备选方案）"""
    conn = create_https_connection("arxiv.org", timeout=60)
    try:
        conn.request("GET", f"/abs/{arxiv_id}", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"})
        resp = conn.getresponse()
        if resp.status != 200:
            return None
        html = resp.read().decode("utf-8", errors="replace")
        # 提取摘要
        abstract = ""
        m = re.search(r'<blockquote class="abstract[^"]*"[^>]*>\s*([^<]+)', html, re.DOTALL)
        if m:
            abstract = m.group(1).strip()
            abstract = re.sub(r'<[^>]+>', '', abstract)
            abstract = abstract.replace("\n", " ").strip()
        return abstract
    except Exception as e:
        logger.warning(f"HTML 获取失败: {e}")
        return None
    finally:
        conn.close()


def _extract_html_text(html: str) -> str:
    """从 arXiv HTML5 页面中提取纯文本正文"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")
        if article:
            for math in article.find_all(["math", "script", "nav", "header", "footer", "aside"]):
                math.decompose()
            text = article.get_text(separator="\n")
        else:
            body = soup.find("body")
            if body:
                for tag in body.find_all(["script", "style", "nav", "header", "footer"]):
                    tag.decompose()
                text = body.get_text(separator="\n")
            else:
                return ""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        return "\n".join(lines)
    except ImportError:
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception:
        return ""


def _fetch_arxiv_html5(arxiv_id: str) -> Optional[str]:
    """获取 arXiv HTML5 全文

    直接尝试 /html/{id}v1 和 /html/{id} 两种 URL（按可靠性排序）。
    arXiv 对较新的论文可能只有带版本号的 HTML 页面。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    # 先生成带版本号的 URL，再试不带版本号的
    urls = []
    # 如果 ID 本身不带版本号，试 v1
    if "v" not in arxiv_id:
        urls.append(f"/html/{arxiv_id}v1")
    urls.append(f"/html/{arxiv_id}")

    for url in urls:
        conn = create_https_connection("arxiv.org", timeout=60)
        try:
            conn.request("GET", url, headers=headers)
            resp = conn.getresponse()
            if resp.status == 200:
                content = resp.read().decode("utf-8", errors="replace")
                text = _extract_html_text(content)
                if text and len(text) > 500:
                    logger.info(f"HTML5 获取成功 ({url}): {len(text)} chars")
                    return text
            elif resp.status in (301, 302, 307, 308):
                loc = resp.getheader("Location", "")
                if loc:
                    from urllib.parse import urlparse
                    follow = urlparse(loc).path
                    if follow != url:
                        conn.close()
                        conn = create_https_connection("arxiv.org", timeout=60)
                        conn.request("GET", follow, headers=headers)
                        resp2 = conn.getresponse()
                        if resp2.status == 200:
                            content = resp2.read().decode("utf-8", errors="replace")
                            text = _extract_html_text(content)
                            if text:
                                logger.info(f"HTML5 获取成功 (redirect {url} → {follow}): {len(text)} chars")
                                return text
        except Exception as e:
            logger.warning(f"HTML5 尝试失败 ({url}): {e}")
        finally:
            conn.close()

    return None


def _extract_pdf_text(pdf_path: str) -> Optional[str]:
    """从本地 PDF 提取文本 — 使用 pymupdf"""
    try:
        import fitz
    except ImportError:
        logger.warning("pymupdf (fitz) 未安装")
        return None

    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        if text.strip():
            return text
    except Exception as e:
        logger.warning(f"pymupdf 提取失败: {e}")
    return None


def download_and_extract(arxiv_id: str, output_dir: str = None) -> Optional[str]:
    """下载 PDF 并提取文本

    策略:
      1. 用 arxiv 库获取 versioned PDF URL → 直连下载 PDF → pymupdf 提取
      2. 失败 → 直接下载 https://arxiv.org/pdf/{id} → pymupdf 提取
      3. 失败 → arXiv HTML5 页面获取全文
      4. 失败 → 返回摘要

    Args:
        arxiv_id: arXiv 论文 ID
        output_dir: PDF 存储目录（默认 data/papers/）

    Returns:
        论文文本内容（str）或 None（全部失败）
    """
    from astro_nova.tools.arxiv_search import fetch_from_abstract
    from astro_nova.utils.paths import get_data_dir as _get_data_dir

    out = output_dir or _get_data_dir("papers")
    os.makedirs(out, exist_ok=True)

    # 获取元数据（用于摘要回退）
    meta = fetch_from_abstract(arxiv_id)
    title = meta.get("title", "") if meta else ""
    summary = meta.get("summary", "") if meta else ""

    pdf_path = os.path.join(out, f"{arxiv_id}.pdf")

    # Strategy 1: 用 arxiv 库获取 versioned URL → 自己下载 → pymupdf 提取
    versioned_url = _get_arxiv_pdf_url(arxiv_id)
    if versioned_url:
        logger.info(f"使用 versioned PDF URL: {versioned_url}")
        downloaded = _download_pdf(versioned_url, pdf_path)
        if downloaded:
            extracted = _extract_pdf_text(pdf_path)
            if extracted and len(extracted) > 500:
                logger.info(f"PDF 文本提取成功: {arxiv_id} ({len(extracted)} chars)")
                return extracted

    # Strategy 2: 直接下载 https://arxiv.org/pdf/{id}
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    logger.info(f"直接下载 PDF: {pdf_url}")
    downloaded = _download_pdf(pdf_url, pdf_path)
    if downloaded:
        extracted = _extract_pdf_text(pdf_path)
        if extracted and len(extracted) > 500:
            logger.info(f"PDF 文本提取成功: {arxiv_id} ({len(extracted)} chars)")
            return extracted

    # Strategy 3: arXiv HTML5 全文页面
    logger.info(f"尝试 HTML5 获取全文: {arxiv_id}")
    html_text = _fetch_arxiv_html5(arxiv_id)
    if html_text and len(html_text) > 500:
        logger.info(f"HTML5 获取成功: {arxiv_id} ({len(html_text)} chars)")
        return html_text

    # Strategy 4: 摘要回退
    if summary and len(summary) > 50:
        logger.info(f"使用摘要: {arxiv_id}")
        return f"Title: {title}\n\nAbstract: {summary}"

    return None
