"""ArXiv 搜索工具 — HTML 抓取实现（绕过 export.arxiv.org API 的 rate limit）"""
import re
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional
from bs4 import BeautifulSoup

from astro_nova.utils.logger import logger
from astro_nova.utils.proxy import get_proxy_opener

ARXIV_BASE = "https://arxiv.org"
SEARCH_URL = f"{ARXIV_BASE}/search/"
LIST_URL = f"{ARXIV_BASE}/list/{{cat}}/new"
TIMEOUT = 60  # 每个请求的超时秒数（中国访问 arxiv.org 较慢）

# 代理感知的 opener（初始化一次，后续复用）
_opener = None


def _get_opener():
    global _opener
    if _opener is None:
        _opener = get_proxy_opener()
    return _opener


def _fetch_html(url: str) -> Optional[str]:
    """获取 HTML 页面，带超时和错误处理（支持代理）"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "AstroNova/1.0 (research assistant; astro@example.com)",
        })
        with _get_opener().open(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        logger.warning(f"arXiv 请求失败: {url[:80]} — {e}")
        return None
    except Exception as e:
        logger.warning(f"arXiv 请求异常: {url[:80]} — {e}")
        return None


def _parse_search_results(html: str) -> list[dict]:
    """从 arXiv 搜索页面 HTML 解析论文列表"""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for item in soup.select("li.arxiv-result"):
        try:
            # arXiv ID
            id_tag = item.select_one("p.list-title a")
            if not id_tag:
                continue
            href = id_tag.get("href", "")
            aid = re.search(r"(\d{4}\.\d{4,5})", href)
            if not aid:
                continue
            arxiv_id = aid.group(1)

            # Title
            title_tag = item.select_one("p.title.is-5.mathjax")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Authors
            auth_tag = item.select_one("p.authors")
            authors = []
            if auth_tag:
                for a in auth_tag.select("a"):
                    authors.append(a.get_text(strip=True))

            # Abstract
            abs_tag = item.select_one("span.abstract-short")
            abstract = abs_tag.get_text(strip=True) if abs_tag else ""

            # Categories
            cat_tags = item.select("div.list-title span")
            categories = []
            for ct in cat_tags:
                t = ct.get_text(strip=True)
                if t.startswith("arXiv:"):
                    continue
                if "." in t and len(t) < 30:
                    categories.append(t)

            # Published date
            date_tag = item.select_one("p.is-size-7")
            published = date_tag.get_text(strip=True) if date_tag else ""

            results.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors[:8],
                "summary": abstract[:500],
                "categories": categories,
                "published": published,
                "pdf_url": f"{ARXIV_BASE}/pdf/{arxiv_id}",
            })
        except Exception as e:
            logger.warning(f"解析论文条目失败: {e}")
            continue

    return results


def _parse_list_results(html: str) -> list[dict]:
    """从 arXiv 分类列表页（/list/{cat}/new）解析论文"""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # 新版 list 页面：每个条目是 <dl> 中的 <dt>/<dd> 对
    dts = soup.select("dl dt")
    dds = soup.select("dl dd")

    for dt, dd in zip(dts, dds):
        try:
            # arXiv ID
            id_link = dt.select_one("a[href*='/abs/']")
            if not id_link:
                continue
            href = id_link.get("href", "")
            aid = re.search(r"(\d{4}\.\d{4,5})", href)
            if not aid:
                continue
            arxiv_id = aid.group(1)

            # Title (from dd .list-title)
            title_tag = dd.select_one(".list-title")
            title = title_tag.get_text(strip=True).replace("Title:", "").strip() if title_tag else ""

            # Authors
            auth_tag = dd.select_one(".list-authors")
            authors = []
            if auth_tag:
                for a in auth_tag.select("a"):
                    authors.append(a.get_text(strip=True))

            # Abstract
            abs_tag = dd.select_one(".mathjax")
            # The abstract text is in the text after removing mathjax children
            abstract = ""
            if abs_tag:
                abstract = abs_tag.get_text(strip=True)[:500]

            # Categories
            cat_tag = dd.select_one(".list-categories")
            categories = cat_tag.get_text(strip=True).replace("Categories:", "").strip().split() if cat_tag else []

            results.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors[:8],
                "summary": abstract[:500],
                "categories": categories,
                "published": "",
                "pdf_url": f"{ARXIV_BASE}/pdf/{arxiv_id}",
            })
        except Exception as e:
            logger.warning(f"解析列表条目失败: {e}")
            continue

    return results


def search_arxiv(
    query: str,
    max_results: int = 10,
    categories: list[str] = None,
    days_back: Optional[int] = None,
) -> list[dict]:
    """搜索 arXiv（HTML 方式），返回论文列表

    Args:
        query: 搜索关键词
        max_results: 返回结果数量
        categories: 分类过滤（如 ["astro-ph.HE", "astro-ph.GA"]）
        days_back: 距今天数过滤（暂未实现）

    Returns:
        [{arxiv_id, title, authors, summary, categories, pdf_url}]
    """
    # 构建搜索 URL
    url = f"{SEARCH_URL}?searchtype=all&query={urllib.parse.quote(query)}"

    logger.info(f"arXiv 搜索: {query}")
    html = _fetch_html(url)
    if not html:
        logger.error(f"arXiv 搜索页面无法访问: {url[:60]}")
        return []

    papers = _parse_search_results(html)

    # 分类过滤
    if categories:
        filtered = []
        for p in papers:
            cat_match = any(
                p.get("arxiv_id", "").startswith(c.split(".")[0])
                or any(c in pc for pc in p.get("categories", []))
                for c in categories
            )
            if cat_match:
                filtered.append(p)
        papers = filtered

    return papers[:max_results]


def fetch_by_id(arxiv_id: str) -> Optional[dict]:
    """按 ID 获取单篇论文信息"""
    aid = parse_arxiv_id(arxiv_id)
    # 用搜索接口查单篇
    url = f"{SEARCH_URL}?searchtype=all&query={urllib.parse.quote(aid)}"
    html = _fetch_html(url)
    if not html:
        return None

    papers = _parse_search_results(html)
    if not papers:
        # 尝试直接从 abs 页面获取
        return fetch_from_abstract(aid)

    for p in papers:
        if p["arxiv_id"] == aid:
            if p.get("title"):
                return p
            # 标题为空 → 尝试从 abs 页面获取
            abs_result = fetch_from_abstract(aid)
            if abs_result and abs_result.get("title"):
                return abs_result
            return p
    # 未精确匹配 → 用第一篇或 abs 页面
    abs_result = fetch_from_abstract(aid)
    if abs_result and abs_result.get("title"):
        return abs_result
    return papers[0] if papers else None


def fetch_by_category(category: str, max_results: int = 50) -> list[dict]:
    """按分类获取最新论文（从 /list/{cat}/new 页面）

    Args:
        category: arXiv 分类 (如 astro-ph.HE)
        max_results: 最大数量

    Returns:
        [{arxiv_id, title, authors, summary, categories, pdf_url}]
    """
    url = LIST_URL.format(cat=category)
    logger.info(f"arXiv 分类列表: {category}")
    html = _fetch_html(url)
    if not html:
        # 尝试不带 /new 的版本
        url = f"{ARXIV_BASE}/list/{category}"
        html = _fetch_html(url)
    if not html:
        return []

    papers = _parse_list_results(html)
    return papers[:max_results]


def fetch_from_abstract(arxiv_id: str) -> Optional[dict]:
    """从 arXiv 摘要页面获取论文信息"""
    aid = parse_arxiv_id(arxiv_id)
    url = f"{ARXIV_BASE}/abs/{aid}"
    html = _fetch_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_tag = soup.select_one("h1.title")
    title = title_tag.get_text(strip=True).replace("Title:", "").strip() if title_tag else ""

    # Authors
    auth_tag = soup.select_one("div.authors")
    authors = []
    if auth_tag:
        for a in auth_tag.select("a"):
            authors.append(a.get_text(strip=True))

    # Abstract
    abs_tag = soup.select_one("blockmark.abstract")
    if not abs_tag:
        # Try the mathjax class
        abs_tag = soup.select_one(".abstract")
    abstract = abs_tag.get_text(strip=True).replace("Abstract:", "").strip()[:500] if abs_tag else ""

    return {
        "arxiv_id": aid,
        "title": title,
        "authors": authors[:8],
        "summary": abstract[:500],
        "categories": [],
        "published": "",
        "pdf_url": f"{ARXIV_BASE}/pdf/{aid}",
    }


def parse_arxiv_id(raw: str) -> str:
    """从 URL 或纯 ID 中提取 arXiv ID"""
    s = raw.strip().rstrip("/")
    m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", s)
    if m:
        return m.group(1)
    if "/abs/" in s:
        return s.split("/abs/")[-1].split("v")[0]
    return s.split("v")[0] if "v" in s else s
