"""工具调用 API 路由 — 内置科研工具（NovaForge 深度集成）"""
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional

from astro_nova.tools.arxiv_search import search_arxiv, fetch_by_id
from astro_nova.tools.arxiv_download import download_and_extract
from astro_nova.tools.paper_reader import read_arxiv_paper, fetch_paper_text
from astro_nova.tools.note_generator import generate_note, engine as novaforge_engine
from astro_nova.tools.figure_generator import generate_figure_code
from astro_nova.tools.writing_assistant import write_paper_section
from astro_nova.tools.ppt_generator import generate_presentation
from astro_nova.utils.logger import logger
from astro_nova.task_manager import add_notification, get_unread, get_unread_count_by_route, mark_read, mark_route_read

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
        title = result.get("title", "") or result.get("arxiv_id", req.arxiv_id)
        add_notification("read", f"论文精读完成", f"{req.arxiv_id} {title[:40]}", "/papers")
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


# ── 笔记生成（NovaForge 集成） ──

class NoteRequest(BaseModel):
    arxiv_id: str
    title: str
    content: str = ""
    mode: str = "research-note"
    compile_pdf: bool = True


@router.post("/note")
async def api_generate_note(req: NoteRequest):
    """用 NovaForge 生成科研笔记（LaTeX + Markdown + 编译 PDF）"""
    try:
        result = await generate_note(
            arxiv_id=req.arxiv_id,
            title=req.title,
            content=req.content,
            mode=req.mode,
            compile_pdf=req.compile_pdf,
        )
        add_notification("note", f"笔记已生成", f"{req.arxiv_id} {req.title[:50]}", "/notes")
        return result
    except Exception as e:
        raise HTTPException(500, f"笔记生成失败: {str(e)}")


# ── 笔记管理 ──

@router.get("/notes/list")
async def api_list_notes():
    """列出所有已生成的笔记"""
    return {"notes": novaforge_engine.list_notes()}


@router.delete("/notes/{arxiv_id}")
async def api_delete_note(arxiv_id: str):
    """删除笔记"""
    ok = novaforge_engine.delete_note(arxiv_id)
    if not ok:
        raise HTTPException(404, f"笔记不存在: {arxiv_id}")
    return {"status": "ok"}


@router.get("/notes/info/{arxiv_id}")
async def api_get_note(arxiv_id: str):
    """获取单篇笔记信息"""
    note = novaforge_engine.get_note(arxiv_id)
    if not note:
        raise HTTPException(404, f"笔记不存在: {arxiv_id}")
    return note


@router.get("/notes/pdf/{arxiv_id}")
async def api_get_note_pdf(arxiv_id: str):
    """返回已编译的笔记 PDF 文件（供浏览器/iframe 预览）"""
    note = novaforge_engine.get_note(arxiv_id)
    if not note or not note["has_pdf"]:
        raise HTTPException(404, "PDF 文件不存在，请先生成笔记")
    pdf_path = note["pdf_path"]
    return FileResponse(pdf_path, media_type="application/pdf",
                        filename=f"{arxiv_id}_note.pdf")


# ── NovaForge 模式查询 ──

@router.get("/novaforge/modes")
async def api_get_novaforge_modes():
    """列出 NovaForge 所有模板模式"""
    return {"modes": novaforge_engine.get_available_modes()}


@router.get("/novaforge/output-dir")
async def api_get_output_dir():
    """获取当前笔记输出目录路径"""
    return {"path": novaforge_engine.get_output_dir()}


# ── 读取笔记文件内容 ──

@router.get("/read-file")
async def api_read_file(path: str):
    """读取笔记文件内容（供前端预览 LaTeX/Markdown 源码）"""
    import urllib.parse
    path = urllib.parse.unquote(path)
    if not os.path.exists(path):
        raise HTTPException(404, f"文件不存在: {path}")
    # 安全: 只允许读取 notes 目录下的文件
    notes_dir = novaforge_engine.get_output_dir()
    if not path.startswith(os.path.abspath(notes_dir)):
        raise HTTPException(403, "禁止访问 notes 目录外的文件")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"path": path, "content": content}
    except Exception as e:
        raise HTTPException(500, f"读取失败: {e}")


# ── 重新编译笔记 PDF ──

@router.post("/notes/recompile/{arxiv_id}")
async def api_recompile_note(arxiv_id: str):
    """重新编译指定笔记的 LaTeX → PDF"""
    note = novaforge_engine.get_note(arxiv_id)
    if not note or not note["has_tex"]:
        raise HTTPException(404, f"笔记 .tex 不存在: {arxiv_id}")
    pdf_path = novaforge_engine.compile_latex(note["tex_path"])
    if not pdf_path:
        raise HTTPException(500, "PDF 编译失败")
    return {"status": "ok", "pdf_path": pdf_path}


# ── 每日 arXiv Digest ──

from astro_nova.tools.daily_digest import run_daily_digest, list_digest_dates, load_digest, DIGEST_DIR


class DigestRequest(BaseModel):
    categories: list[str] | None = None
    max_per_cat: int = 50
    enhance: bool = True


@router.post("/digest/run")
async def api_run_digest(req: DigestRequest):
    """运行每日 Digest：爬取 arXiv → 去重 → LLM 增强 → 生成日报"""
    try:
        result = await run_daily_digest(
            categories=req.categories,
            max_per_cat=req.max_per_cat,
            enhance=req.enhance,
        )
        date_str = result.get("date", "")
        new_count = result.get("new", 0)
        total = result.get("total", 0)
        add_notification("digest", f"Daily Digest ({new_count}篇新论文)", f"{date_str} 共{total}篇", "/digest")
        return result
    except Exception as e:
        raise HTTPException(500, f"Digest 失败: {str(e)}")


@router.get("/digest/dates")
async def api_digest_dates():
    """列出所有已有日报日期"""
    return {"dates": list_digest_dates()}


@router.get("/digest/{date_str}")
async def api_get_digest(date_str: str):
    """获取指定日期的日报数据"""
    papers = load_digest(date_str)
    if papers is None:
        raise HTTPException(404, f"未找到 {date_str} 的日报")
    return {"date": date_str, "total": len(papers), "papers": papers}


@router.get("/digest/markdown/{date_str}")
async def api_get_digest_markdown(date_str: str):
    """获取指定日期的 Markdown 日报"""
    papers = load_digest(date_str)
    if papers is None:
        raise HTTPException(404, f"未找到 {date_str} 的日报")
    from astro_nova.tools.daily_digest import generate_markdown
    md = generate_markdown(papers)
    return HTMLResponse(content=md)


# ── 论文查看器 + 引用聊天 ──


class PaperChatRequest(BaseModel):
    arxiv_id: str
    message: str
    history: list[dict] = []
    paper_text: str = ""


@router.post("/paper/open")
async def api_open_paper(req: "FetchRequest"):
    """获取论文完整信息（供查看器使用）"""
    from astro_nova.tools.paper_viewer import open_paper
    try:
        result = await open_paper(req.arxiv_id)
        return result
    except Exception as e:
        raise HTTPException(500, f"打开论文失败: {str(e)}")


@router.post("/paper/chat")
async def api_paper_chat(req: PaperChatRequest):
    """论文问答（带引用溯源）"""
    from astro_nova.tools.paper_viewer import chat_about_paper

    try:
        # 优先使用前端已缓存的论文全文，避免重复抓取
        paper_text = req.paper_text or ""
        if not paper_text:
            # 回退：后端自行抓取
            from astro_nova.tools.paper_viewer import open_paper
            from astro_nova.tools.arxiv_download import download_and_extract
            paper = await open_paper(req.arxiv_id)
            if "error" in paper:
                raise HTTPException(404, paper["error"])
            paper_text = paper.get("text", "")
            if not paper_text:
                paper_text = download_and_extract(req.arxiv_id) or ""

        result = await chat_about_paper(
            paper_id=req.arxiv_id,
            paper_text=paper_text,
            user_message=req.message,
            chat_history=req.history,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"论文聊天失败: {str(e)}")


@router.post("/paper/summarize")
async def api_summarize_paper(req: "FetchRequest"):
    """一键总结论文"""
    from astro_nova.tools.paper_viewer import open_paper, chat_about_paper
    from astro_nova.tools.arxiv_download import download_and_extract
    try:
        paper = await open_paper(req.arxiv_id)
        if "error" in paper:
            raise HTTPException(404, paper["error"])
        paper_text = paper.get("text", "")
        if not paper_text:
            paper_text = download_and_extract(req.arxiv_id) or ""

        result = await chat_about_paper(
            paper_id=req.arxiv_id,
            paper_text=paper_text,
            user_message="请用中文总结这篇论文的核心内容，分以下部分：1) 研究背景与问题 2) 方法 3) 主要发现 4) 结论与意义。对每个部分标注引用来源。",
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"总结失败: {str(e)}")

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
        add_notification("figure", f"制图完成 ({req.plot_type})", f"风格: {req.style}", "/figures")
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
        wc = result.get("word_count", 0)
        add_notification("writing", f"论文写作完成 ({req.section_type})", f"约{wc}字 | {req.journal.upper()}", "/writing")
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
        fmt = result.get("format", req.output_format)
        add_notification("ppt", f"PPT 生成完成", f"风格: {req.style} | 格式: {fmt}", "/ppt")
        return result
    except Exception as e:
        raise HTTPException(500, f"PPT 生成失败: {str(e)}")


# ── 任务通知管理 ──


@router.get("/tasks/notifications")
async def get_task_notifications():
    """获取所有未读的任务完成通知"""
    return {"notifications": get_unread()}


@router.get("/tasks/notifications/counts")
async def get_task_counts():
    """按路由分组的未读通知数量"""
    return {"counts": get_unread_count_by_route()}


@router.post("/tasks/notifications/{notification_id}/read")
async def read_notification(notification_id: str):
    """标记单条通知为已读"""
    mark_read(notification_id)
    return {"status": "ok"}


@router.post("/tasks/notifications/read-route")
async def read_notifications_by_route(route: str):
    """标记某个路由的所有通知为已读"""
    mark_route_read(route)
    return {"status": "ok"}


