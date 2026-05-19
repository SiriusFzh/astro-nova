"""NovaForge 科研笔记生成工具

将论文精读内容转换为 NovaForge 格式的结构化笔记，输出 LaTeX 和 Markdown。

用法:
  generate_note(arxiv_id="2301.00001", title="...", sections={...})
    → 生成 .tex + .md 文件
"""
import os
import json
from datetime import date
from typing import Optional

from astro_nova.providers.base import LLMMessage
from astro_nova.providers.manager import manager as provider_manager
from astro_nova.tools.registry import Tool, registry
from astro_nova.utils.logger import logger

# 从 references/preamble.tex 读取导言区
PREAMBLE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "references", "preamble.tex")


def _load_preamble() -> str:
    try:
        with open(PREAMBLE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


# NovaForge 笔记存储目录
NOTES_DIR = os.path.join(os.path.expanduser("~"), ".astro-nova", "notes")


def generate_latex_note(
    arxiv_id: str,
    title: str,
    authors: list[str],
    journal: str,
    year: str,
    sections: dict[str, str],
) -> str:
    """生成 NovaForge 格式的 LaTeX 笔记

    Args:
        arxiv_id: arXiv ID
        title: 论文标题
        authors: 作者列表
        journal: 刊源 (arXiv / ApJ / MNRAS ...)
        year: 年份
        sections: 章节 dict, 如 {"研究背景": "...", "方法": "...", ...}

    Returns:
        LaTeX 源码字符串
    """
    preamble = _load_preamble()

    latex = preamble + "\n\n"
    latex += f"\\section{{{title}}}\n\n"

    # 文献卡片
    latex += f"\\paperinfo{{{title}}}{{{'、'.join(authors[:8])}}}{{{journal}}}{{{year}}}\n\n"

    # 各章节
    section_titles = [
        ("研究背景与问题", "一"),
        ("方法与技术路线", "二"),
        ("核心结果与发现", "三"),
        ("创新点与贡献", "四"),
        ("局限性与未来工作", "五"),
        ("与自身研究的关联", "六"),
    ]

    for sec_title, num in section_titles:
        content = sections.get(sec_title, "").strip()
        if content:
            latex += f"\\section{{{num}、{sec_title}}}\n\n"
            # 简单转换: markdown 标题 → lithead, 公式 → formula
            lines = content.split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("### "):
                    latex += f"\\lithead{{{stripped[4:]}}}\n\n"
                elif stripped.startswith("**") and stripped.endswith("**"):
                    latex += f"\\knowtitle{{{stripped.strip('*')}}}\n\n"
                elif stripped.startswith("$$"):
                    latex += f"\\formula{{{stripped.strip('$')}}}\n\n"
                elif stripped.startswith("> "):
                    latex += f"\\infobox{{{stripped[2:]}}}\n\n"
                else:
                    latex += stripped + "\n\n"

    return latex


def generate_markdown_note(
    arxiv_id: str,
    title: str,
    authors: list[str],
    journal: str,
    year: str,
    sections: dict[str, str],
) -> str:
    """生成 Markdown 版本笔记"""
    md = f"""# {title}

**文献卡片**
- arXiv: {arxiv_id}
- 作者: {', '.join(authors[:8])}
- 刊源: {journal}
- 年份: {year}

---

"""
    for sec_title, content in sections.items():
        if content.strip():
            md += f"## {sec_title}\n\n{content.strip()}\n\n---\n\n"
    return md


async def generate_note(
    arxiv_id: str,
    title: str,
    content: str = "",
    output_format: str = "latex",
    sections: Optional[dict[str, str]] = None,
) -> dict:
    """生成 NovaForge 格式科研笔记

    从精读内容（markdown）自动转换为 LaTeX 笔记，或直接传入已分好章节的 dict。

    Args:
        arxiv_id: arXiv ID
        title: 论文标题
        content: 精读笔记 Markdown 全文（若提供，通过 LLM 自动提取章节）
        output_format: "latex" / "markdown" / "both"
        sections: 可选，预分好的章节 dict

    Returns:
        {"arxiv_id": ..., "latex": "..." , "md": "...", "file_paths": {...}}
    """
    os.makedirs(NOTES_DIR, exist_ok=True)
    note_dir = os.path.join(NOTES_DIR, arxiv_id)
    os.makedirs(note_dir, exist_ok=True)

    result = {
        "arxiv_id": arxiv_id,
        "title": title,
        "latex": "",
        "md": "",
        "file_paths": {},
    }

    # 如果没有预分章节但提供了全文，用 LLM 提取
    if not sections and content:
        provider = provider_manager.get_provider("write") or provider_manager.get_provider("chat")
        if provider:
            try:
                resp = await provider.chat([
                    LLMMessage(role="system", content="""从论文精读笔记中提取 6 个章节的内容，返回 JSON:
{
  "研究背景与问题": "...",
  "方法与技术路线": "...",
  "核心结果与发现": "...",
  "创新点与贡献": "...",
  "局限性与未来工作": "...",
  "与自身研究的关联": "..."
}"""),
                    LLMMessage(role="user", content=f"论文标题: {title}\n\n笔记内容:\n{content}"),
                ])
                import re
                match = re.search(r"\{.*\}", resp.content, re.DOTALL)
                if match:
                    sections = json.loads(match.group())
            except Exception as e:
                logger.warning(f"LLM 章节提取失败: {e}")

    sections = sections or {}
    authors = []
    journal = "arXiv"
    year = ""

    # 生成 LaTeX
    latex = generate_latex_note(arxiv_id, title, authors, journal, year, sections)
    md = generate_markdown_note(arxiv_id, title, authors, journal, year, sections)

    # 保存文件
    tex_path = os.path.join(note_dir, f"{arxiv_id}.tex")
    md_path = os.path.join(note_dir, f"{arxiv_id}.md")

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    result["latex"] = latex
    result["md"] = md
    result["file_paths"] = {"tex": tex_path, "md": md_path}

    logger.info(f"笔记已保存: {tex_path}")
    return result


def register_tools():
    registry.register(Tool(
        name="generate_note",
        description="将论文精读内容转换为 NovaForge 格式的科研笔记（LaTeX + Markdown），并保存到本地",
        parameters={
            "type": "object",
            "properties": {
                "arxiv_id": {"type": "string", "description": "arXiv 论文 ID"},
                "title": {"type": "string", "description": "论文标题"},
                "content": {"type": "string", "description": "精读笔记 Markdown 全文（可选，与 sections 二选一）"},
                "output_format": {
                    "type": "string",
                    "enum": ["latex", "markdown", "both"],
                    "description": "输出格式",
                },
            },
            "required": ["arxiv_id", "title"],
        },
        handler=generate_note,
    ))
