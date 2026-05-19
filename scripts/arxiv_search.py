"""
astro-nova / scripts / arxiv_search.py
ArXiv API 搜索工具 — 搜索天文学论文，返回结构化元数据
覆盖: 天体物理、天文技术、天体测量、行星科学、太阳物理、宇宙学、空间物理等

依赖: pip install arxiv requests

用法:
    python arxiv_search.py search "neutron star mergers" --max 10
    python arxiv_search.py fetch 2301.00001
    python arxiv_search.py search "天文仪器" --cat astro-ph.IM physics.ins-det --days 30
"""

import argparse
import datetime
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    import arxiv
except ImportError:
    print("请先安装 arxiv 库: pip install arxiv", file=sys.stderr)
    sys.exit(1)

ARXIV_CATEGORIES = {
    # ── 天文学全部分支 ──
    "astro-ph": "天文学全部分支",
    "astro-ph.GA": "天体物理-星系与天体测量",
    "astro-ph.CO": "天体物理-宇宙学",
    "astro-ph.EP": "天体物理-系外行星与行星科学",
    "astro-ph.HE": "天体物理-高能天体物理",
    "astro-ph.IM": "天体物理-仪器、方法与天文技术",
    "astro-ph.SR": "天体物理-太阳与恒星",
    # ── 相关领域 ──
    "gr-qc": "广义相对论与引力波",
    "hep-ph": "高能物理-唯象学",
    "physics.space-ph": "空间物理",
    "physics.ao-ph": "大气与海洋物理（天文台址）",
    "physics.ins-det": "仪器与探测器（天文探测）",
    "physics.atm-clus": "原子与分子团簇",
    "physics.plasm-ph": "等离子体物理",
    "cs.AI": "人工智能（天文应用）",
    "cs.LG": "机器学习（天文应用）",
    "stat.ML": "统计学习（天文应用）",
}


@dataclass
class Paper:
    """单篇论文的数据结构"""
    arXiv_ID: str
    Title: str
    Authors: list
    Published: str
    Updated: str
    Summary: str
    Categories: list
    DOI: Optional[str] = None
    Primary_Category: str = ""
    PDF_Link: str = ""
    Relevance_Score: Optional[float] = None  # LLM 相关度评分

    def to_dict(self):
        return asdict(self)


def search_papers(
    query: str,
    max_results: int = 20,
    categories: list = None,
    sort_by: str = "relevance",
    days_back: Optional[int] = None,
) -> list[Paper]:
    """
    搜索 ArXiv 论文。

    参数:
        query: 搜索关键词
        max_results: 最大返回数 (默认 20)
        categories: 限定分类, 如 ["astro-ph.HE", "astro-ph.GA"]
        sort_by: "relevance" | "submittedDate" | "updatedDate"
        days_back: 仅返回最近 N 天的论文

    返回:
        list[Paper]
    """
    # 构建搜索 query
    search_parts = [query]
    if categories:
        cat_filter = " OR ".join(f"cat:{c}" for c in categories)
        search_parts.append(f"({cat_filter})")

    full_query = " AND ".join(search_parts) if len(search_parts) > 1 else search_parts[0]

    sort_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "submittedDate": arxiv.SortCriterion.SubmittedDate,
        "updatedDate": getattr(arxiv.SortCriterion, "LastUpdatedDate", arxiv.SortCriterion.SubmittedDate),
    }

    client = arxiv.Client()
    search = arxiv.Search(
        query=full_query,
        max_results=max_results,
        sort_by=sort_map.get(sort_by, arxiv.SortCriterion.Relevance),
    )

    results = []
    cutoff = None
    if days_back:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days_back)

    for result in client.results(search):
        pub_date = result.published.replace(tzinfo=None)

        if cutoff and pub_date < cutoff:
            continue

        paper = Paper(
            arXiv_ID=result.entry_id.replace("http://arxiv.org/abs/", "").replace("https://arxiv.org/abs/", "").split("v")[0],
            Title=result.title.replace("\n", " ").strip(),
            Authors=[a.name for a in result.authors],
            Published=result.published.isoformat(),
            Updated=result.updated.isoformat(),
            Summary=result.summary.replace("\n", " ").strip(),
            Categories=[c for c in result.categories],
            DOI=str(result.doi) if result.doi else None,
            Primary_Category=result.primary_category,
            PDF_Link=result.pdf_url,
        )
        results.append(paper)

    return results


def fetch_by_id(arxiv_id: str) -> Optional[Paper]:
    """按 arXiv ID 获取单篇论文元数据。"""
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    try:
        result = next(client.results(search))
    except StopIteration:
        return None

    return Paper(
        arXiv_ID=arxiv_id,
        Title=result.title.replace("\n", " ").strip(),
        Authors=[a.name for a in result.authors],
        Published=result.published.isoformat(),
        Updated=result.updated.isoformat(),
        Summary=result.summary.replace("\n", " ").strip(),
        Categories=[c for c in result.categories],
        DOI=str(result.doi) if result.doi else None,
        Primary_Category=result.primary_category,
        PDF_Link=result.pdf_url,
    )


def format_paper_list(papers: list[Paper]) -> str:
    """将论文列表格式化为可读文本。"""
    lines = []
    for i, p in enumerate(papers, 1):
        score = f" [相关度: {p.Relevance_Score:.1f}/10]" if p.Relevance_Score else ""
        cat = ", ".join(p.Categories[:3])
        extra = f" (+{len(p.Categories)-3} more)" if len(p.Categories) > 3 else ""

        lines.extend([
            f"{'='*70}",
            f"  #{i}{score}",
            f"  Title: {p.Title}",
            f"  Authors: {', '.join(p.Authors[:5])}{' et al.' if len(p.Authors) > 5 else ''}",
            f"  arXiv: {p.arXiv_ID}  |  {p.Published[:10]}  |  [{cat}]{extra}",
            f"  PDF: {p.PDF_Link}",
            f"  DOI: {p.DOI}" if p.DOI else "",
            f"  ---",
            f"  {p.Summary[:300]}...",
            "",
        ])
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="ArXiv 论文搜索工具 (天文学全领域)")
    sub = parser.add_subparsers(dest="command", required=True)

    # search 子命令
    p_search = sub.add_parser("search", help="搜索论文")
    p_search.add_argument("query", help="搜索关键词")
    p_search.add_argument("--max", type=int, default=20, help="最大结果数")
    p_search.add_argument("--cat", nargs="+", default=["astro-ph"],
                          help="限定分类, 如 astro-ph.HE astro-ph.GA")
    p_search.add_argument("--sort", choices=["relevance", "submittedDate", "updatedDate"],
                          default="relevance", help="排序方式")
    p_search.add_argument("--days", type=int, default=None, help="仅最近 N 天")
    p_search.add_argument("--json", action="store_true", help="JSON 格式输出")

    # fetch 子命令
    p_fetch = sub.add_parser("fetch", help="按 ID 获取单篇")
    p_fetch.add_argument("arxiv_id", help="arXiv ID, 如 2301.00001")
    p_fetch.add_argument("--json", action="store_true", help="JSON 格式输出")

    # categories 子命令
    p_cat = sub.add_parser("categories", help="列出所有天文学相关分类")

    args = parser.parse_args()

    if args.command == "categories":
        print("ArXiv 天文学相关分类:")
        for code, desc in ARXIV_CATEGORIES.items():
            print(f"  {code:20s} {desc}")
        return

    if args.command == "search":
        papers = search_papers(
            query=args.query,
            max_results=args.max,
            categories=args.cat,
            sort_by=args.sort,
            days_back=args.days,
        )
        if args.json:
            print(json.dumps([p.to_dict() for p in papers], ensure_ascii=False, indent=2))
        else:
            print(f"\n找到 {len(papers)} 篇论文 (分类: {', '.join(args.cat)}):\n")
            print(format_paper_list(papers))

    elif args.command == "fetch":
        paper = fetch_by_id(args.arxiv_id)
        if not paper:
            print(f"未找到 arXiv:{args.arxiv_id}", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(paper.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(format_paper_list([paper]))


if __name__ == "__main__":
    main()
