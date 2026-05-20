"""论文查看器 + 引用溯源聊天

功能:
  1. 输入 arXiv ID → 一键获取论文并显示
  2. 在分割面板中: 左=论文内容, 右=聊天
  3. "总结这篇论文" → AI 自动总结 (TL;DR + 结构)
  4. 提问 → 基于论文原文回答 + 引用原文位置
  5. "你刚刚说的出自哪里？" → 溯源引用: 返回原文+段落
  6. 英文写作支持: "用英文解释...给出引用"

引用追踪机制:
  - 每次 LLM 回答时, 强制要求标注引用来源 (段落/句子)
  - 引用存储为结构化数据, 支持反向查询
"""
import json
import os
import re
from typing import Optional
from pathlib import Path

from astro_nova.utils.logger import logger

# ── 引用数据结构 ──

"""
Citation = {
    "paper_id": "2301.00001",
    "text": "引用的原文",
    "section": "段落编号或节标题",
    "sentence_index": [3, 5],  # 句子索引范围
    "page": None,  # PDF 页号 (如有)
    "confidence": "exact|paraphrase",  # 精确引用或转述
}
"""


def extract_sections_from_text(text: str) -> list[dict]:
    """将论文全文按段落/节切分, 便于引用定位

    Args:
        text: 论文全文文本

    Returns:
        [{"index": 0, "heading": "Abstract", "sentences": [...], "text": "..."}]
    """
    sections = []
    lines = text.split("\n")
    current_heading = "Abstract"
    current_sentences = []
    current_lines = []

    section_idx = 0
    # Common section headings in academic papers
    section_keywords = [
        "abstract", "introduction", "background", "related work",
        "method", "approach", "experiment", "result", "discussion",
        "conclusion", "appendix", "acknowledgment", "reference",
        "data", "observation", "analysis", "summary",
    ]
    # Also match numbered headings like "1. Introduction", "2.1 Method"
    heading_pattern = re.compile(
        r'^(\d+(\.\d+)*\s+)?'
        r'((' + '|'.join(section_keywords) + r')'
        r'|[A-Z][a-z]+(\s+[A-Z][a-z]+)*)'
        r'(\s*:\s*.*)?$',
        re.IGNORECASE
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        is_heading = False
        # Check for markdown headings
        if stripped.startswith("#"):
            is_heading = True
        # Check for ALL CAPS short lines (classic paper heading style)
        elif stripped.isupper() and 3 < len(stripped) < 80:
            is_heading = True
        # Check for numbered headings like "1. Introduction" or "2.1 Method"
        elif re.match(r'^\d+(\.\d+)*\s+', stripped):
            is_heading = True
        # Check for common section keywords
        elif len(stripped) < 100 and not stripped.endswith(".") and not stripped.endswith(":"):
            lower = stripped.lower().rstrip(".")
            if lower in section_keywords or any(k in lower for k in section_keywords):
                is_heading = True
            if current_lines:
                sections.append({
                    "index": section_idx,
                    "heading": current_heading,
                    "text": "\n".join(current_lines),
                    "sentences": current_sentences,
                })
                section_idx += 1
            current_heading = stripped.lstrip("#").strip()
            current_sentences = []
            current_lines = []
        else:
            current_lines.append(stripped)
            # 按句号分割句子
            if stripped:
                for sent in re.split(r'(?<=[.!?])\s+', stripped):
                    if sent.strip():
                        current_sentences.append(sent.strip())

    # 最后一段
    if current_lines:
        sections.append({
            "index": section_idx,
            "heading": current_heading,
            "text": "\n".join(current_lines),
            "sentences": current_sentences,
        })

    return sections


def build_paper_context(sections: list[dict], max_chars: int = 8000) -> str:
    """构建带段落标记的论文上下文供 LLM 引用

    Returns:
        标记后的文本: "[Sec-0] Abstract\n...\n[Sec-1] Introduction\n..."
    """
    context_parts = []
    total = 0
    for sec in sections:
        sec_tag = f"[Sec-{sec['index']}] {sec['heading']}"
        sec_text = sec["text"]
        if total + len(sec_text) > max_chars:
            allowed = max_chars - total
            if allowed > 200:
                context_parts.append(f"{sec_tag}\n{sec_text[:allowed]}...")
            break
        context_parts.append(f"{sec_tag}\n{sec_text}")
        total += len(sec_text)
    return "\n\n".join(context_parts)


# ── 论文聊天: 引用感知的 LLM 封装 ──

CITATION_SYSTEM_PROMPT = """你是一个论文阅读助手。你正在阅读一篇 arXiv 论文, 需要回答用户关于论文内容的问题。

## 规则
1. **精确引用**: 每次回答时, 必须在引用处标注来源, 格式为 `[Sec-N]` 表示第 N 节。
2. **原文引用**: 对于关键论点, 直接引用原文 (用引号) 并标注 `[Sec-N]`。
3. **不要推测**: 如果论文中没有相关内容, 明确说"论文未提及此事", 不要自行编造。
4. **中文回答**: 默认用中文回答, 除非用户要求其他语言。
5. **英语写作支持**: 如果用户问"这个观点用英文怎么说"或"帮我写英文", 提供英文并标注引用。
6. **溯源**: 当用户问"你刚才说的出自哪里"时, 回顾对话, 给出对应的原文引用和段落。

## 论文内容

{paper_context}
"""


async def chat_about_paper(
    paper_id: str,
    paper_text: str,
    user_message: str,
    chat_history: list = None,
) -> dict:
    """关于论文的问答 — 带引用溯源

    Args:
        paper_id: arXiv ID
        paper_text: 论文全文
        user_message: 用户问题
        chat_history: 历史消息

    Returns:
        {"answer": "...", "citations": [{"sec": N, "text": "..."}], ...}
    """
    from astro_nova.providers.manager import manager
    from astro_nova.providers.base import LLMMessage

    provider = manager.get_provider("chat")
    if not provider:
        return {"answer": "无可用 LLM Provider", "citations": []}

    # 构建引用上下文
    sections = extract_sections_from_text(paper_text)
    paper_context = build_paper_context(sections)
    system_prompt = CITATION_SYSTEM_PROMPT.format(paper_context=paper_context)

    # 构建消息
    messages = [LLMMessage(role="system", content=system_prompt)]
    if chat_history:
        for msg in chat_history[-10:]:  # 限制历史长度
            messages.append(LLMMessage(role=msg["role"], content=msg["content"]))
    messages.append(LLMMessage(role="user", content=user_message))

    try:
        resp = await provider.chat(messages)
        answer = resp.content

        # 从回答中提取引用
        citations = []
        for match in re.finditer(r'\[Sec-(\d+)\]', answer):
            sec_idx = int(match.group(1))
            if sec_idx < len(sections):
                sec = sections[sec_idx]
                citations.append({
                    "sec": sec_idx,
                    "heading": sec["heading"],
                    "text": sec["text"][:300],
                })

        # 去重
        seen_secs = set()
        unique_citations = []
        for c in citations:
            if c["sec"] not in seen_secs:
                seen_secs.add(c["sec"])
                unique_citations.append(c)

        return {
            "answer": answer,
            "citations": unique_citations,
            "paper_id": paper_id,
        }
    except Exception as e:
        logger.error(f"论文聊天失败: {e}")
        return {"answer": f"回答失败: {e}", "citations": []}


# ── 一键打开论文 ──

async def open_paper(arxiv_id: str) -> dict:
    """获取论文完整信息供查看器使用

    Args:
        arxiv_id: arXiv ID

    Returns:
        {"arxiv_id": ..., "title": ..., "authors": [...],
         "abstract": ..., "text": "...全文...",
         "sections": [...段落结构...],
         "pdf_url": ..., "abs_url": ...,
         "has_full_text": bool}
    """
    from astro_nova.tools.arxiv_fetch import fetch_arxiv_paper

    result = await fetch_arxiv_paper(arxiv_id, format="auto")
    if "error" in result:
        return result

    # 结构化段落
    text = result.get("text", "")
    sections = extract_sections_from_text(text) if text else []

    return {
        "arxiv_id": arxiv_id,
        "title": result.get("title", ""),
        "authors": result.get("authors", []),
        "abstract": text[:500] if text else result.get("text", ""),
        "text": text,
        "sections": sections,
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
        "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
        "has_full_text": result.get("has_full_text", False),
        "source": result.get("source", ""),
    }
