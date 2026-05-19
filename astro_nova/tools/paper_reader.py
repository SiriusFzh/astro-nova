"""论文精读工具 — 自动获取并分析 arXiv 论文，生成结构化精读笔记

用法（工具调用）:
  read_arxiv_paper(arxiv_id="2301.00001", output_format="markdown")
    → 一站式: 搜索 → 下载 → LLM 分析 → 结构化笔记

注册为 Tool 供 LLM 自主调用。
"""
import os
from typing import Optional

from astro_nova.providers.base import LLMMessage
from astro_nova.providers.manager import manager as provider_manager
from astro_nova.tools.arxiv_download import download_and_extract as _fetch_text
from astro_nova.tools.arxiv_search import fetch_by_id as _fetch_meta
from astro_nova.tools.registry import Tool, registry
from astro_nova.utils.logger import logger

# 精读框架 7 维度 (与 astro-reader SKILL.md 一致)
READING_FRAMEWORK = """
请按以下 7 个维度分析这篇论文，输出结构化 Markdown：

## 一、文献卡片
- arXiv ID / 标题 / 作者 / 年份 / 分类

## 二、研究背景
- 解决了什么科学问题？
- 已有研究的不足？
- 本文的目标与创新？

## 三、方法/技术路线
- 使用了什么数据/观测/实验？
- 核心方法/算法/模型？
- 技术细节的关键点？

## 四、核心结果
- 最重要的 3-5 个结果（定量）
- 图表说明了什么？

## 五、创新点
- 方法创新 / 发现创新？
- 相比 previous works 的进步？

## 六、局限性
- 方法的局限？
- 未解决的问题？

## 七、个人思考
- 对自身研究的启发
- 可改进/可扩展的方向
"""


async def read_arxiv_paper(
    arxiv_id: str,
    output_format: str = "markdown",
    language: str = "中文",
) -> dict:
    """一站式论文精读：自动搜索 → 下载全文 → LLM 分析 → 结构化笔记

    Args:
        arxiv_id: arXiv ID, 如 "2301.00001"
        output_format: 输出格式, "markdown" 或 "latex"
        language: 分析语言, "中文" 或 "English"

    Returns:
        {"arxiv_id": ..., "title": ..., "note": "...", "latex": "..."}
    """
    # Step 1: 获取元数据
    meta = _fetch_meta(arxiv_id)
    if not meta:
        return {"error": f"未找到 arXiv:{arxiv_id}"}

    title = meta.get("title", "")
    logger.info(f"精读论文: {title}")

    # Step 2: 下载并提取全文
    text = _fetch_text(arxiv_id)
    if not text:
        # 如果文本提取失败，用摘要替代
        text = meta.get("summary", "")
        logger.warning(f"全文提取失败，使用摘要替代: {arxiv_id}")

    # 截断过长文本 (token 限制)
    max_chars = 30000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... 文本过长已截断]"

    # Step 3: 调用 LLM 分析
    provider = provider_manager.get_provider("read")
    if not provider:
        provider = provider_manager.get_provider("chat")

    if not provider:
        return {
            "arxiv_id": arxiv_id,
            "title": title,
            "note": "错误: 没有可用的 LLM Provider",
        }

    lang_instruction = "请用中文分析" if language == "中文" else "Please analyze in English"
    messages = [
        LLMMessage(role="system", content=f"""你是一个天文学论文精读助手。{lang_instruction}。
{READING_FRAMEWORK}

输出格式要求：
- 使用 Markdown 格式
- 关键数据点需要包含原文引用的数值
- 保持学术严谨性，不确定的内容要注明"""),
        LLMMessage(role="user", content=f"""请分析以下论文：

标题: {title}
作者: {', '.join(meta.get('authors', [])[:10])}
分类: {', '.join(meta.get('categories', []))}
摘要: {meta.get('summary', '')}

全文文本:
{text}

{lang_instruction}，按 7 维度框架输出结构化精读笔记。"""),
    ]

    try:
        resp = await provider.chat(messages)
        note = resp.content
    except Exception as e:
        logger.error(f"LLM 分析失败: {e}")
        note = f"LLM 分析失败: {e}"

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "note": note,
        "meta": {
            "authors": meta.get("authors", [])[:5],
            "published": meta.get("published", ""),
            "categories": meta.get("categories", []),
            "pdf_url": meta.get("pdf_url", ""),
        },
    }


async def fetch_paper_text(arxiv_id: str) -> str:
    """仅提取 arXiv 论文全文文本"""
    text = _fetch_text(arxiv_id)
    if text:
        return text
    meta = _fetch_meta(arxiv_id)
    return meta.get("summary", "") if meta else ""


def register_tools():
    """注册工具到全局 ToolRegistry"""
    registry.register(Tool(
        name="read_arxiv_paper",
        description="下载 arXiv 论文全文并用 AI 分析，按 7 维度输出结构化精读笔记（文献卡片、背景、方法、结果、创新点、局限性、个人思考）",
        parameters={
            "type": "object",
            "properties": {
                "arxiv_id": {
                    "type": "string",
                    "description": "arXiv 论文 ID，如 2301.00001",
                },
                "output_format": {
                    "type": "string",
                    "enum": ["markdown", "latex"],
                    "description": "输出格式",
                },
                "language": {
                    "type": "string",
                    "enum": ["中文", "English"],
                    "description": "分析语言",
                },
            },
            "required": ["arxiv_id"],
        },
        handler=read_arxiv_paper,
    ))

    registry.register(Tool(
        name="fetch_paper_text",
        description="仅提取 arXiv 论文的全文文本，不进行分析",
        parameters={
            "type": "object",
            "properties": {
                "arxiv_id": {
                    "type": "string",
                    "description": "arXiv 论文 ID",
                },
            },
            "required": ["arxiv_id"],
        },
        handler=fetch_paper_text,
    ))
