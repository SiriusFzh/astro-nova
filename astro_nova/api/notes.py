"""笔记管理 API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from astro_nova.database.connection import async_session
from astro_nova.database.models import Note
from sqlalchemy import select

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteCreate(BaseModel):
    arxiv_id: Optional[str] = None
    title: str
    format: str = "markdown"
    content: str
    tags: Optional[str] = None


@router.get("")
async def list_notes():
    async with async_session() as session:
        result = await session.execute(select(Note).order_by(Note.updated_at.desc()))
        notes = result.scalars().all()
        return [
            {
                "id": n.id,
                "arxiv_id": n.arxiv_id,
                "title": n.title,
                "format": n.format,
                "tags": n.tags,
                "created_at": str(n.created_at)[:16] if n.created_at else "",
            }
            for n in notes
        ]


@router.post("")
async def create_note(note: NoteCreate):
    async with async_session() as session:
        n = Note(**note.model_dump())
        session.add(n)
        await session.commit()
    return {"status": "ok", "id": n.id}


@router.delete("/{note_id}")
async def delete_note(note_id: int):
    async with async_session() as session:
        n = await session.get(Note, note_id)
        if n:
            await session.delete(n)
            await session.commit()
    return {"status": "ok"}
