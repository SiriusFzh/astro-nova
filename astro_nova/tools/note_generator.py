"""NovaForge 科研笔记生成工具

将论文精读内容转换为 NovaForge 格式的结构化笔记。
使用完整嵌入的 NovaForge 模板引擎，支持:
  - 自动获取 arXiv 论文元数据
  - LLM 将精读内容按 7 节结构整理
  - 生成 LaTeX（完整 NovaForge preamble）+ Markdown
  - 编译为 PDF（需本地 xelatex）
  - 输出到 ~/.astro-nova/notes/<arxiv_id>/
  - 软件内 PDF 预览

用法（LLM 工具调用）:
  generate_note(arxiv_id="2301.00001", title="...", sections={...})
    → 自动完成: 获取元数据 → 填充模板 → 编译 → 存储

推荐工作流:
  1. search_arxiv → 找到论文
  2. fetch_paper_text → 下载全文
  3. read_arxiv_paper → LLM 分析
  4. generate_note → LLM 整理 + NovaForge 生成
  (全部由 LLM 在对话中自主完成)
"""
import json
import os
import re
from datetime import date
from typing import Optional

from astro_nova.novaforge import NovaForgeEngine, MODES
from astro_nova.providers.base import LLMMessage
from astro_nova.providers.manager import manager as provider_manager
from astro_nova.tools.arxiv_download import download_and_extract as _fetch_text
from astro_nova.tools.arxiv_search import fetch_by_id
from astro_nova.tools.registry import Tool, registry
from astro_nova.utils.logger import logger

# NovaForge 引擎实例
engine = NovaForgeEngine()

# 输出目录
NOTES_DIR = engine.get_output_dir()


async def generate_note(
    arxiv_id: str,
    title: str,
    content: str = "",
    sections: Optional[dict[str, str]] = None,
    mode: str = "research-note",
    compile_pdf: bool = True,
) -> dict:
    """生成 NovaForge 格式科研笔记

    这是 NovaForge 生成的主入口。它:
    1. 从 arXiv 获取论文元数据
    2. 如果 content 为空，自动下载 arXiv 论文全文
    3. 如果提供了 content 但没提供 sections，用 LLM 自动提取章节
    4. LLM 提取失败或没有 LLM 时，使用原始 content 作为笔记正文
    5. 用 NovaForge 引擎生成 LaTeX + Markdown
    6. 编译 PDF（可选）
    7. 保存到 data/notes/<arxiv_id>/

    Args:
        arxiv_id: arXiv ID（用于命名目录和获取元数据）
        title: 论文标题
        content: 精读内容（paper_reader 输出的结构化 Markdown）
        sections: 可选的预分章节 dict
        mode: NovaForge 模板模式（默认 research-note）
        compile_pdf: 是否编译 PDF

    Returns:
        {"arxiv_id": ..., "title": ..., "mode": ...,
         "latex": ..., "md": ...,
         "tex_path": ..., "md_path": ..., "pdf_path": ...,
         "pdf_available": bool, "files": {...}}
    """
    # Step 1: 获取 arXiv 元数据（允许失败）
    meta = None
    try:
        meta = fetch_by_id(arxiv_id)
    except Exception as e:
        logger.warning(f"获取 arXiv 元数据失败: {e}")

    authors = meta.get("authors", []) if meta else []
    authors_str = "、".join(authors[:8]) if authors else ""
    published = meta.get("published", "") if meta else ""
    year = published[:4] if len(published) >= 4 else ""
    categories = meta.get("categories", []) if meta else []
    categories_str = ", ".join(categories[:5]) if categories else ""
    journal = f"arXiv ({categories_str})" if categories_str else "arXiv"

    # Step 2: 自动获取论文正文（如果调用方没提供 content 或 content 太短/是错误信息）
    needs_fetch = (
        not content
        or len(content) < 200
        or content.startswith("错误:")
        or content.startswith("LLM 分析失败")
    )
    if needs_fetch:
        logger.info(f"自动下载 arXiv 论文全文: {arxiv_id} (content={len(content) if content else 0}chars)")
        try:
            fetched = _fetch_text(arxiv_id)
            if fetched and len(fetched) > 500:
                content = fetched
                logger.info(f"论文全文获取成功: {len(content)} chars")
        except Exception as e:
            logger.warning(f"论文全文下载失败: {e}")

    # Step 3: 如果没有预分章节但提供了全文，用 LLM 提取
    sections_from_llm = False
    if not sections and content:
        try:
            llm_sections = await _extract_sections_with_llm(title, authors_str, content)
            if llm_sections and any(v.strip() for v in llm_sections.values()):
                sections = llm_sections
                sections_from_llm = True
        except Exception as e:
            logger.warning(f"LLM 章节提取失败: {e}")

    sections = sections or {}

    # Step 4: 如果 LLM 提取失败或没有 LLM，使用原始 content 作为 core
    if not sections_from_llm and content:
        # 如果 sections 中有任意非空字段，保留；否则全部用原始内容
        has_any_content = any(v.strip() for v in sections.values())
        if not has_any_content:
            sections = {"core": content[:8000]} if content else {}
            logger.info("LLM 未提取到章节，使用原始全文作为 core")

    # Step 5: 用 NovaForge 引擎生成
    data = {
        "title": title,
        "title_short": title[:60].replace("\n", " "),
        "arxiv_id": arxiv_id,
        "authors": authors_str,
        "published": published,
        "categories": categories_str,
        "journal": journal,
        "year": year,
        "sections": {
            "core": sections.get("core") or sections.get("研究背景与问题", ""),
            "methods": sections.get("methods") or sections.get("方法与技术路线", ""),
            "results": sections.get("results") or sections.get("核心结果与发现", ""),
            "innovation": sections.get("innovation") or sections.get("创新点与贡献", ""),
            "limitations": sections.get("limitations") or sections.get("局限性与未来工作", ""),
            "thoughts": sections.get("thoughts") or sections.get("个人思考与启发", ""),
        },
    }

    result = engine.generate(mode=mode, **data)

    # 编译 PDF
    if compile_pdf and result["tex_path"]:
        pdf_path = engine.compile_latex(result["tex_path"])
        if pdf_path:
            result["pdf_path"] = pdf_path
            result["pdf_available"] = True
            result["files"]["pdf"] = pdf_path

    logger.info(f"笔记已保存: {result['tex_path']}")
    return result


async def _extract_sections_with_llm(title: str, authors: str, content: str) -> dict:
    """用 LLM 从精读笔记中提取 7 节内容"""
    provider = provider_manager.get_provider("write") or provider_manager.get_provider("chat")
    if not provider:
        return {}

    resp = await provider.chat([
        LLMMessage(role="system", content=r"""你是一个科研笔记整理助手。
从论文精读笔记中提取内容，按以下 7 个章节整理为 JSON：

{
  "core": "研究背景与科学问题、研究目标",
  "methods": "方法/技术路线/数据来源",
  "results": "核心结果与发现（含定量数据）",
  "innovation": "创新点与贡献",
  "limitations": "局限性与未来工作",
  "thoughts": "个人思考与对自身研究的启发"
}

要求：
- 保留原文中的关键数值和定量结果
- 每个章节内容详细充实，不少于 50 字
- 使用 NovaForge 格式标记：
  - **标题** 表示知识标题栏 (\knowtitle)
  - $$公式$$ 表示公式框 (\formula)
  - > 提示 表示提示框 (\infobox)
  - ! 警告 表示警告 (\warning)
  - - 列表项 表示要点
- 用纯文本（plain text）"""),
        LLMMessage(role="user", content=f"论文标题: {title}\n作者: {authors}\n\n精读笔记:\n{content}"),
    ])

    match = re.search(r"\{.*\}", resp.content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def register_tools():
    """将 NovaForge 笔记生成工具注册到 ToolRegistry"""

    registry.register(Tool(
        name="generate_note",
        description="将论文精读内容转换为 NovaForge 格式的结构化笔记（LaTeX + Markdown），并编译为 PDF。生成的文件保存在 data/notes/ 目录中",
        parameters={
            "type": "object",
            "properties": {
                "arxiv_id": {"type": "string", "description": "arXiv 论文 ID"},
                "title": {"type": "string", "description": "论文标题"},
                "content": {"type": "string", "description": "精读笔记 Markdown 全文"},
                "mode": {
                    "type": "string",
                    "enum": list(MODES.keys()),
                    "description": "NovaForge 模板模式",
                },
                "compile_pdf": {
                    "type": "boolean",
                    "description": "是否编译 PDF",
                },
            },
            "required": ["arxiv_id", "title"],
        },
        handler=generate_note,
    ))

    registry.register(Tool(
        name="list_notes",
        description="列出所有已生成的 NovaForge 笔记",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=lambda **kw: engine.list_notes(),
    ))

    registry.register(Tool(
        name="delete_note",
        description="删除指定 ID 的笔记",
        parameters={
            "type": "object",
            "properties": {
                "arxiv_id": {"type": "string", "description": "要删除的笔记 ID（arxiv_id）"},
            },
            "required": ["arxiv_id"],
        },
        handler=lambda arxiv_id, **kw: engine.delete_note(arxiv_id),
    ))

    registry.register(Tool(
        name="get_notes_dir",
        description="获取笔记存储目录路径",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=lambda **kw: engine.get_output_dir(),
    ))

    registry.register(Tool(
        name="get_novaforge_modes",
        description="列出 NovaForge 所有可用的模板模式",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=lambda **kw: engine.get_available_modes(),
    ))

    registry.register(Tool(
        name="compile_latex_to_pdf",
        description="编译指定的 .tex 文件为 PDF（使用 NovaForge 的 xelatex 编译器）",
        parameters={
            "type": "object",
            "properties": {
                "tex_path": {"type": "string", "description": ".tex 文件的完整路径"},
            },
            "required": ["tex_path"],
        },
        handler=lambda tex_path, **kw: engine.compile_latex(tex_path),
    ))
