"""学术汇报 PPT 生成工具 — 从论文生成 Marp/Pandoc/Reveal.js 幻灯片

支持 3 种汇报风格 × 3 种输出格式：
  风格: 课题汇报 / 国际会议 / 答辩开题
  格式: Marp Markdown / Pandoc Markdown / Reveal.js HTML

用法:
  generate_presentation(arxiv_id="2301.00001", style="journal_club", output_format="marp")
    → 返回幻灯片 Markdown 源码
"""
import os
from typing import Optional

from astro_nova.providers.base import LLMMessage
from astro_nova.providers.manager import manager as provider_manager
from astro_nova.tools.arxiv_download import download_and_extract as _fetch_text
from astro_nova.tools.arxiv_search import fetch_by_id as _fetch_meta
from astro_nova.tools.registry import Tool, registry
from astro_nova.utils.logger import logger

from astro_nova.utils.paths import get_data_dir as _get_data_dir

SLIDE_DIR = _get_data_dir("slides")

STYLE_CONFIGS = {
    "journal_club": {
        "name": "课题汇报",
        "pages": "10-15 页",
        "language": "中文",
        "structure": "封面 → 目录 → 研究背景(2页) → 方法(2页) → 结果(3-4页) → 讨论 → 结论 → 个人思考 → 参考文献",
        "description": "课题组会、Journal Club、读书报告。中文，详细，含个人思考章节",
    },
    "conference": {
        "name": "国际会议",
        "pages": "8-10 页",
        "language": "English",
        "structure": "Title → Motivation → Method → Results(3页) → Discussion → Summary → Backup",
        "description": "AAS/IAU/COSPAR 等国际会议。English, concise, figure-driven",
    },
    "defense": {
        "name": "答辩/开题",
        "pages": "15-20 页",
        "language": "中文为主",
        "structure": "封面 → 框架 → 背景(3页) → 方法(3页) → 结果(5页) → 讨论 → 结论与创新点 → 展望 → Q&A → 备份页",
        "description": "硕士答辩、博士开题、基金申请",
    },
}

FORMAT_INSTRUCTIONS = {
    "marp": """Marp Markdown 格式:
---
marp: true
theme: default
class: lead
paginate: true
---

# 标题
内容...

用 `---` 分隔幻灯片。""",
    "pandoc": """Pandoc Markdown 格式:
% 标题
% 作者
% 日期

# 章节
内容...

用 `\\newpage` 或 `# 新章节` 分隔幻灯片。""",
    "revealjs": """Reveal.js HTML 格式:
<section>
<h2>标题</h2>
<p>内容</p>
</section>

用 `<section>` 标签分隔幻灯片。""",
}


async def generate_presentation(
    arxiv_id: str = "",
    title: str = "",
    content: str = "",
    style: str = "journal_club",
    output_format: str = "marp",
    additional_notes: str = "",
) -> dict:
    """从论文生成学术汇报幻灯片

    Args:
        arxiv_id: arXiv ID (与 content 二选一)
        title: 演示标题
        content: 论文精读笔记或内容描述（优先使用）
        style: 汇报风格 (journal_club / conference / defense)
        output_format: 输出格式 (marp / pandoc / revealjs)
        additional_notes: 额外要求

    Returns:
        {"slides": "...", "file_path": "...", "format": "...", "style": "..."}
    """
    os.makedirs(SLIDE_DIR, exist_ok=True)

    style_cfg = STYLE_CONFIGS.get(style, STYLE_CONFIGS["journal_club"])

    # 收集论文信息
    paper_title = title
    paper_text = content

    if arxiv_id and not paper_text:
        meta = _fetch_meta(arxiv_id)
        if meta:
            paper_title = paper_title or meta.get("title", "")
            paper_text = _fetch_text(arxiv_id) or meta.get("summary", "")

    if not paper_text:
        return {"error": "请提供 arXiv ID 或论文内容", "slides": ""}

    max_chars = 25000
    if len(paper_text) > max_chars:
        paper_text = paper_text[:max_chars] + "\n\n[... 截断]"

    provider = provider_manager.get_provider("chat")
    if not provider:
        return {"error": "没有可用的 LLM Provider", "slides": ""}

    format_guide = FORMAT_INSTRUCTIONS.get(output_format, FORMAT_INSTRUCTIONS["marp"])

    messages = [
        LLMMessage(role="system", content=f"""你是一个学术汇报 PPT 生成专家。

风格: {style_cfg['name']} ({style_cfg['description']})
页数: {style_cfg['pages']}
语言: {style_cfg['language']}
结构: {style_cfg['structure']}

{format_guide}

要求:
- 内容学术严谨，数据准确
- 图表占位符用 `![Figure: 描述](placeholder)` 标记
- 每页要点不超过 5 个
- 含页码（Marp 的 paginate: true）
- 适当使用 bold/italic 强调关键概念"""),
        LLMMessage(role="user", content=f"""论文: {paper_title}
内容: {paper_text[:12000]}
额外要求: {additional_notes}

请按 {style_cfg['name']} 风格生成 {output_format} 格式的幻灯片。"""),
    ]

    try:
        resp = await provider.chat(messages)
        slides = resp.content

        # 提取代码块
        import re
        match = re.search(r"```(?:markdown|md|html)?\n(.*?)```", slides, re.DOTALL)
        if match:
            slides = match.group(1).strip()

        # 保存文件
        ext_map = {"marp": ".md", "pandoc": ".md", "revealjs": ".html"}
        ext = ext_map.get(output_format, ".md")
        fname = f"{arxiv_id or 'presentation'}_{style}_{output_format}{ext}"
        file_path = os.path.join(SLIDE_DIR, fname)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(slides)

        convert_cmd = {
            "marp": f"npx @marp-team/marp-cli {file_path} --pptx",
            "pandoc": f"pandoc {file_path} -o {file_path}.pptx",
            "revealjs": f"xdg-open {file_path}",
        }.get(output_format, "")

        logger.info(f"幻灯片已保存: {file_path}")
        return {
            "slides": slides,
            "file_path": file_path,
            "format": output_format,
            "style": style,
            "style_name": style_cfg["name"],
            "convert_command": convert_cmd,
        }
    except Exception as e:
        logger.error(f"PPT 生成失败: {e}")
        return {"error": str(e), "slides": ""}


def register_tools():
    registry.register(Tool(
        name="generate_presentation",
        description="从 arXiv 论文或精读笔记生成学术汇报幻灯片（支持 Marp/Pandoc/Reveal.js 格式，支持课题汇报/国际会议/答辩开题三种风格）",
        parameters={
            "type": "object",
            "properties": {
                "arxiv_id": {"type": "string", "description": "arXiv 论文 ID（与 content 二选一）"},
                "title": {"type": "string", "description": "演示标题"},
                "content": {"type": "string", "description": "论文精读笔记或内容描述（优先于 arxiv_id）"},
                "style": {
                    "type": "string",
                    "enum": ["journal_club", "conference", "defense"],
                    "description": "汇报风格: 课题汇报(中文详细) / 国际会议(英文简洁) / 答辩开题(中英混合)",
                },
                "output_format": {
                    "type": "string",
                    "enum": ["marp", "pandoc", "revealjs"],
                    "description": "输出格式: Marp / Pandoc / Reveal.js",
                },
                "additional_notes": {"type": "string", "description": "额外要求，如配色、页数等"},
            },
            "required": [],
        },
        handler=generate_presentation,
    ))
