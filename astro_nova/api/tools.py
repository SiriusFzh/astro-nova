"""工具调用 API 路由 — 内置科研工具"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from astro_nova.tools.arxiv_search import search_arxiv, fetch_by_id
from astro_nova.tools.arxiv_download import download_and_extract
from astro_nova.tools.paper_reader import read_arxiv_paper, fetch_paper_text
from astro_nova.tools.note_generator import generate_note
from astro_nova.tools.figure_generator import generate_figure_code
from astro_nova.tools.writing_assistant import write_paper_section
from astro_nova.tools.ppt_generator import generate_presentation

router = APIRouter(prefix="/tools", tags=["tools"])


# ── ArXiv 搜索/下载 ──

class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    categories: list[str] = ["astro-ph"]
    days_back: Optional[int] = None


class FetchRequest(BaseModel):
    arxiv_id: str


@router.post("/arxiv/search")
async def api_search(req: SearchRequest):
    try:
        results = search_arxiv(req.query, req.max_results, req.categories, req.days_back)
        return {"papers": results}
    except Exception as e:
        raise HTTPException(500, f"搜索失败: {str(e)}")


@router.post("/arxiv/fetch")
async def api_fetch(req: FetchRequest):
    try:
        paper = fetch_by_id(req.arxiv_id)
        if not paper:
            raise HTTPException(404, f"未找到 arXiv:{req.arxiv_id}")
        text = download_and_extract(req.arxiv_id)
        return {"paper": paper, "text_preview": text[:3000] if text else ""}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"获取失败: {str(e)}")


# ── 论文精读 ──

class ReadPaperRequest(BaseModel):
    arxiv_id: str
    output_format: str = "markdown"
    language: str = "中文"


@router.post("/read")
async def api_read_paper(req: ReadPaperRequest):
    """一站式论文精读"""
    try:
        result = await read_arxiv_paper(
            arxiv_id=req.arxiv_id,
            output_format=req.output_format,
            language=req.language,
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"精读失败: {str(e)}")


@router.post("/read/text")
async def api_fetch_text(req: FetchRequest):
    """仅提取论文全文"""
    try:
        text = await fetch_paper_text(req.arxiv_id)
        if not text:
            raise HTTPException(404, f"无法获取论文文本: {req.arxiv_id}")
        return {"arxiv_id": req.arxiv_id, "text": text[:5000]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"提取失败: {str(e)}")


# ── 笔记生成 ──

class NoteRequest(BaseModel):
    arxiv_id: str
    title: str
    content: str = ""
    output_format: str = "both"


@router.post("/note")
async def api_generate_note(req: NoteRequest):
    """生成 NovaForge 格式笔记"""
    try:
        result = await generate_note(
            arxiv_id=req.arxiv_id,
            title=req.title,
            content=req.content,
            output_format=req.output_format,
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"笔记生成失败: {str(e)}")


# ── 制图代码生成 ──

class FigureRequest(BaseModel):
    data_description: str
    plot_type: str = "spectrum"
    style: str = "apj"
    additional_requirements: str = ""


@router.post("/figure")
async def api_generate_figure(req: FigureRequest):
    """生成出版级 matplotlib 绘图代码"""
    try:
        result = await generate_figure_code(
            data_description=req.data_description,
            plot_type=req.plot_type,
            style=req.style,
            additional_requirements=req.additional_requirements,
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"制图代码生成失败: {str(e)}")


# ── 论文写作 ──

class WritingRequest(BaseModel):
    section_type: str
    journal: str = "apj"
    title: str = ""
    context: str = ""
    additional_notes: str = ""


@router.post("/write")
async def api_write_section(req: WritingRequest):
    """按期刊格式撰写论文章节"""
    try:
        result = await write_paper_section(
            section_type=req.section_type,
            journal=req.journal,
            title=req.title,
            context=req.context,
            additional_notes=req.additional_notes,
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"写作失败: {str(e)}")


# ── PPT 生成 ──

class PPTRequest(BaseModel):
    arxiv_id: str = ""
    title: str = ""
    content: str = ""
    style: str = "journal_club"
    output_format: str = "marp"
    additional_notes: str = ""


@router.post("/ppt")
async def api_generate_ppt(req: PPTRequest):
    """生成学术汇报幻灯片"""
    try:
        result = await generate_presentation(
            arxiv_id=req.arxiv_id,
            title=req.title,
            content=req.content,
            style=req.style,
            output_format=req.output_format,
            additional_notes=req.additional_notes,
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"PPT 生成失败: {str(e)}")
