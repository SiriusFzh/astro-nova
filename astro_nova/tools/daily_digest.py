"""每日 arXiv 天文论文 Digest — 自动爬取 + 去重 + LLM 中文摘要

工作流程:
  1. 每日自动抓取 arXiv 所有 astro-ph 分类的最新论文
  2. 与近 7 天对比去重
  3. 调用 LLM 生成结构化中文摘要 (TL;DR / motivation / method / result / conclusion)
  4. 生成 Markdown 日报

参考自: https://github.com/dw-dengwei/daily-arXiv-ai-enhanced
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from astro_nova.utils.logger import logger

# ── 天文学全部分类 ──
ASTRO_CATEGORIES = [
    "astro-ph.GA",   # 星系天体物理
    "astro-ph.HE",   # 高能天体物理
    "astro-ph.CO",   # 宇宙学
    "astro-ph.SR",   # 太阳与恒星物理
    "astro-ph.EP",   # 行星科学
    "astro-ph.IM",   # 仪器与方法
]

# 也包括不带子分类的 astro-ph
ALL_CATEGORIES = ASTRO_CATEGORIES + ["astro-ph"]

# 存储目录
from astro_nova.utils.paths import get_data_dir as _get_data_dir
DIGEST_DIR = Path(_get_data_dir("digest"))


def ensure_dirs():
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)


# ── Step 1: 爬取最新论文 ──

def fetch_latest_papers(categories: list[str] = None, max_per_cat: int = 20) -> list[dict]:
    """从 arXiv 爬取各分类最新论文（HTML 方式，绕过 API rate limit）

    Args:
        categories: arXiv 分类列表，默认所有 astro-ph 子分类
        max_per_cat: 每个分类最多爬取数

    Returns:
        [{"id": "...", "title": "...", "authors": [...],
          "summary": "...", "categories": [...], "pdf_url": "...", ...}]
    """
    from astro_nova.tools.arxiv_search import fetch_by_category

    categories = categories or ASTRO_CATEGORIES
    papers = []
    seen_ids = set()

    for cat in categories:
        try:
            cat_papers = fetch_by_category(cat, max_per_cat)
            for p in cat_papers:
                pid = p["arxiv_id"]
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                papers.append({
                    "id": pid,
                    "title": p["title"],
                    "authors": p["authors"],
                    "summary": p["summary"],
                    "categories": p["categories"],
                    "primary_category": cat,
                    "pdf_url": p["pdf_url"],
                    "abs_url": f"https://arxiv.org/abs/{pid}",
                    "published": p.get("published", ""),
                    "updated": "",
                    "comment": "",
                })
        except Exception as e:
            logger.warning(f"爬取 {cat} 失败: {e}")

    logger.info(f"arXiv 爬取完成: {len(categories)} 个分类, {len(papers)} 篇论文")
    return papers


# ── Step 2: 去重 ──

def deduplicate(papers: list[dict], days_back: int = 7) -> list[dict]:
    """对比历史数据去重

    Args:
        papers: 今日新爬取的论文
        days_back: 向前追溯天数

    Returns:
        去重后的新论文列表
    """
    ensure_dirs()

    # 收集历史 ID
    history_ids = set()
    for i in range(1, days_back + 1):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        hist_file = DIGEST_DIR / f"{date_str}.jsonl"
        if hist_file.exists():
            with open(hist_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            item = json.loads(line)
                            history_ids.add(item.get("id", ""))
                        except json.JSONDecodeError:
                            pass

    new_papers = [p for p in papers if p["id"] not in history_ids]
    logger.info(f"去重: {len(papers)} → {len(new_papers)} 篇新论文 (排除 {len(papers)-len(new_papers)} 篇历史重复)")
    return new_papers


# ── Step 3: LLM 增强 ──

from pydantic import BaseModel, Field


class PaperStructure(BaseModel):
    """论文结构化摘要 — LLM 输出格式"""
    tldr: str = Field(description="TL;DR 一句话总结（中文，20字以内）")
    motivation: str = Field(description="研究动机与背景（中文，50-100字）")
    method: str = Field(description="方法/技术路线（中文，50-100字）")
    result: str = Field(description="核心结果与发现（中文，50-100字）")
    conclusion: str = Field(description="结论与意义（中文，50-100字）")


DIGEST_SYSTEM_PROMPT = """你是一个天文学论文分析助手。
请用中文简洁、准确地总结论文的核心内容。

输出格式要求（JSON）：
  - tldr: 一句话总结（20字内）
  - motivation: 研究动机与背景
  - method: 方法/技术路线
  - result: 核心结果与发现
  - conclusion: 结论与意义

要求：
- 每个字段 50-100 字
- 保留关键数值
- 学术严谨，不添加原文没有的内容
- 用中文输出"""


async def enhance_paper(paper: dict, provider=None) -> dict:
    """用 LLM 对单篇论文进行结构化摘要

    Args:
        paper: 论文数据
        provider: LLM Provider（不传则从管理器获取）

    Returns:
        增强后的论文数据（含 AI 字段）
    """
    if provider is None:
        from astro_nova.providers.manager import manager
        provider = manager.get_provider("chat")

    if not provider:
        paper["AI"] = {
            "tldr": "（无可用 LLM）",
            "motivation": "", "method": "", "result": "", "conclusion": "",
        }
        return paper

    try:
        from astro_nova.providers.base import LLMMessage

        resp = await provider.chat([
            LLMMessage(role="system", content=DIGEST_SYSTEM_PROMPT),
            LLMMessage(role="user", content=f"Title: {paper['title']}\n\nAuthors: {', '.join(paper['authors'][:5])}\n\nAbstract: {paper['summary']}"),
        ])
        text = resp.content

        # 尝试提取 JSON
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            ai_data = json.loads(match.group())
        else:
            ai_data = {"tldr": text[:100], "motivation": "", "method": "", "result": "", "conclusion": ""}

        paper["AI"] = ai_data
    except Exception as e:
        logger.warning(f"LLM 增强失败: {paper.get('id', '')}: {e}")
        paper["AI"] = {"tldr": "增强失败", "motivation": "", "method": "", "result": "", "conclusion": ""}

    return paper


async def enhance_all(papers: list[dict], max_workers: int = 3) -> list[dict]:
    """并行增强所有论文"""
    import asyncio
    from astro_nova.providers.manager import manager

    provider = manager.get_provider("chat")
    if not provider:
        for p in papers:
            p["AI"] = {"tldr": "（无可用 LLM）", "motivation": "", "method": "", "result": "", "conclusion": ""}
        return papers

    sem = asyncio.Semaphore(max_workers)

    async def _enhance_one(p):
        async with sem:
            return await enhance_paper(p, provider)

    tasks = [_enhance_one(p) for p in papers]
    results = await asyncio.gather(*tasks)
    return list(results)


# ── Step 4: 存储 & 生成日报 ──

def save_digest(papers: list[dict]) -> str:
    """保存当天论文到 JSONL 文件

    Returns:
        文件路径
    """
    ensure_dirs()
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = DIGEST_DIR / f"{date_str}.jsonl"

    with open(file_path, "w", encoding="utf-8") as f:
        for p in papers:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    logger.info(f"日报已保存: {file_path} ({len(papers)} 篇)")
    return str(file_path)


def generate_markdown(papers: list[dict]) -> str:
    """生成 Markdown 日报

    Args:
        papers: 增强后的论文列表

    Returns:
        Markdown 字符串
    """
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 按分类分组
    by_cat: dict[str, list] = {}
    for p in papers:
        cat = p.get("primary_category") or (p.get("categories") or [""])[0]
        by_cat.setdefault(cat, []).append(p)

    # 分类排序（按预定义顺序）
    cat_order = {c: i for i, c in enumerate(ASTRO_CATEGORIES)}
    sorted_cats = sorted(by_cat.keys(), key=lambda c: cat_order.get(c, 999))

    # 生成 TOC
    md = f"# 🌌 天文学每日 arXiv Digest — {date_str}\n\n"
    md += f"**共 {len(papers)} 篇论文** | 涵盖 {len(sorted_cats)} 个分类\n\n"
    md += "## 目录\n\n"
    for cat in sorted_cats:
        papers_in_cat = by_cat[cat]
        md += f"- [{cat}](#{cat}) — {len(papers_in_cat)} 篇\n"

    # 生成正文
    for cat in sorted_cats:
        papers_in_cat = by_cat[cat]
        md += f"\n---\n\n## {cat}\n\n"
        for i, p in enumerate(papers_in_cat, 1):
            ai = p.get("AI", {}) or {}
            tldr = ai.get("tldr", "")
            motivation = ai.get("motivation", "")
            method = ai.get("method", "")
            result = ai.get("result", "")
            conclusion = ai.get("conclusion", "")
            authors = ", ".join(p["authors"][:5])
            if len(p["authors"]) > 5:
                authors += " et al."

            md += f"### {i}. [{p['title']}]({p['abs_url']})\n"
            md += f"*{authors}* | `{p['id']}`\n\n"

            if tldr:
                md += f"**TL;DR:** {tldr}\n\n"

            md += "<details>\n<summary>详细信息</summary>\n\n"
            if motivation:
                md += f"**动机:** {motivation}\n\n"
            if method:
                md += f"**方法:** {method}\n\n"
            if result:
                md += f"**结果:** {result}\n\n"
            if conclusion:
                md += f"**结论:** {conclusion}\n\n"
            md += f"**分类:** {', '.join(p['categories'][:5])}\n\n"
            md += f"</details>\n\n"

    md += f"\n---\n*由 AstroNova + NovaForge 自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    return md


# ── 主流程 ──

async def run_daily_digest(
    categories: list[str] = None,
    max_per_cat: int = 50,
    enhance: bool = True,
) -> dict:
    """运行每日 Digest 完整流程

    爬取 → 去重 → LLM 增强 → 保存 → 生成 Markdown

    Returns:
        {"date": "...", "total": N, "new": N, "file": "...", "markdown": "..."}
    """
    categories = categories or ASTRO_CATEGORIES
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 1. 爬取
    logger.info(f"开始爬取 arXiv 天文论文: {categories}")
    all_papers = fetch_latest_papers(categories, max_per_cat)

    # 2. 去重
    new_papers = deduplicate(all_papers)

    # 3. LLM 增强
    if enhance and new_papers:
        logger.info(f"LLM 增强 {len(new_papers)} 篇论文...")
        new_papers = await enhance_all(new_papers)

    # 4. 保存
    file_path = save_digest(new_papers)

    # 5. 生成 Markdown
    markdown = generate_markdown(new_papers)

    logger.info(f"每日 Digest 完成: {date_str}, 总计 {len(all_papers)}, 新增 {len(new_papers)}")
    return {
        "date": date_str,
        "total": len(all_papers),
        "new": len(new_papers),
        "file": file_path,
        "markdown": markdown,
        "papers": [
            {
                "id": p["id"],
                "title": p["title"],
                "authors": p["authors"][:3],
                "categories": p["categories"][:3],
                "abs_url": p["abs_url"],
                "tldr": p.get("AI", {}).get("tldr", ""),
                "primary_category": p.get("primary_category", ""),
            }
            for p in new_papers
        ],
    }


def list_digest_dates() -> list[str]:
    """列出所有已有日报的日期"""
    ensure_dirs()
    dates = []
    for f in sorted(DIGEST_DIR.glob("*.jsonl"), reverse=True):
        dates.append(f.stem)
    return dates


def register_tools():
    """注册 Digest 工具到 ToolRegistry"""
    from astro_nova.tools.registry import Tool, registry

    registry.register(Tool(
        name="run_daily_digest",
        description="爬取 arXiv 今日最新天文论文（所有 astro-ph 分类），去重后生成中文摘要日报",
        parameters={
            "type": "object",
            "properties": {
                "max_per_cat": {"type": "integer", "description": "每个分类最大数量"},
                "enhance": {"type": "boolean", "description": "是否用 LLM 生成摘要"},
            },
        },
        handler=lambda max_per_cat=20, enhance=True, **kw: run_daily_digest(max_per_cat=max_per_cat, enhance=enhance),
    ))

    registry.register(Tool(
        name="list_digest_dates",
        description="列出所有已有的 arXiv 日报日期",
        parameters={"type": "object", "properties": {}},
        handler=lambda **kw: list_digest_dates(),
    ))

    registry.register(Tool(
        name="load_digest",
        description="加载指定日期的 arXiv 日报",
        parameters={
            "type": "object",
            "properties": {
                "date_str": {"type": "string", "description": "日期，格式 YYYY-MM-DD"},
            },
            "required": ["date_str"],
        },
        handler=lambda date_str, **kw: load_digest(date_str),
    ))


def load_digest(date_str: str) -> Optional[list[dict]]:
    """加载指定日期的日报数据"""
    file_path = DIGEST_DIR / f"{date_str}.jsonl"
    if not file_path.exists():
        return None
    papers = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                papers.append(json.loads(line))
    return papers
