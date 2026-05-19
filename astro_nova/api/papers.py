"""论文管理 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from astro_nova.database.connection import async_session
from astro_nova.database.models import Paper
from sqlalchemy import select

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("")
async def list_papers():
    """论文列表"""
    async with async_session() as session:
        result = await session.execute(select(Paper).order_by(Paper.created_at.desc()))
        papers = result.scalars().all()
        return [
            {
                "arxiv_id": p.arxiv_id,
                "title": p.title,
                "authors": p.authors,
                "published": str(p.published)[:10] if p.published else "",
                "categories": p.categories,
                "summary": p.summary[:200] if p.summary else "",
            }
            for p in papers
        ]


@router.delete("/{arxiv_id}")
async def delete_paper(arxiv_id: str):
    async with async_session() as session:
        p = await session.get(Paper, arxiv_id)
        if not p:
            raise HTTPException(404, "论文不存在")
        await session.delete(p)
        await session.commit()
    return {"status": "ok"}
