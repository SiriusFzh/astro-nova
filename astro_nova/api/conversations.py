"""对话历史管理 API"""
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete

from astro_nova.database.connection import async_session
from astro_nova.database.models import Conversation
from astro_nova.utils.logger import logger

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str = "新对话"


class ConversationUpdate(BaseModel):
    title: str | None = None
    messages: list[dict] | None = None


class ConversationOut(BaseModel):
    id: int
    title: str
    messages: list[dict] = []
    created_at: str
    updated_at: str


def _to_out(c: Conversation) -> ConversationOut:
    msgs = json.loads(c.messages) if c.messages else []
    return ConversationOut(
        id=c.id,
        title=c.title or "新对话",
        messages=msgs,
        created_at=c.created_at.isoformat() if c.created_at else "",
        updated_at=c.updated_at.isoformat() if c.updated_at else "",
    )


@router.get("")
async def list_conversations():
    """获取所有对话（不含完整消息，只取标题和时间）"""
    async with async_session() as session:
        result = await session.execute(
            select(Conversation).order_by(Conversation.updated_at.desc())
        )
        conversations = result.scalars().all()
        return [
            {
                "id": c.id,
                "title": c.title or "新对话",
                "message_count": len(json.loads(c.messages)) if c.messages else 0,
                "created_at": c.created_at.isoformat() if c.created_at else "",
                "updated_at": c.updated_at.isoformat() if c.updated_at else "",
            }
            for c in conversations
        ]


@router.post("")
async def create_conversation(body: ConversationCreate):
    """创建新对话"""
    async with async_session() as session:
        c = Conversation(
            title=body.title,
            messages="[]",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(c)
        await session.commit()
        await session.refresh(c)
        logger.info(f"创建对话: {c.id} ({body.title})")
        return _to_out(c)


@router.get("/{conv_id}")
async def get_conversation(conv_id: int):
    """获取单个对话（含完整消息）"""
    async with async_session() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        c = result.scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="对话不存在")
        return _to_out(c)


@router.put("/{conv_id}")
async def update_conversation(conv_id: int, body: ConversationUpdate):
    """更新对话（标题或消息）"""
    async with async_session() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        c = result.scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="对话不存在")
        if body.title is not None:
            c.title = body.title
        if body.messages is not None:
            c.messages = json.dumps(body.messages, ensure_ascii=False)
        c.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(c)
        return _to_out(c)


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: int):
    """删除对话"""
    async with async_session() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        c = result.scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="对话不存在")
        await session.delete(c)
        await session.commit()
        logger.info(f"删除对话: {conv_id}")
        return {"ok": True}


class MessageUpdate(BaseModel):
    index: int
    content: str


@router.patch("/{conv_id}/messages/{msg_idx}")
async def edit_message(conv_id: int, msg_idx: int, body: MessageUpdate):
    """编辑单条消息内容"""
    async with async_session() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        c = result.scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="对话不存在")
        msgs = json.loads(c.messages) if c.messages else []
        if msg_idx < 0 or msg_idx >= len(msgs):
            raise HTTPException(status_code=400, detail="消息索引越界")
        msgs[msg_idx]["content"] = body.content
        c.messages = json.dumps(msgs, ensure_ascii=False)
        c.updated_at = datetime.utcnow()
        await session.commit()
        logger.info(f"编辑消息: conv={conv_id}, idx={msg_idx}")
        return {"ok": True, "messages": msgs}


@router.delete("/{conv_id}/messages/{msg_idx}")
async def delete_message(conv_id: int, msg_idx: int):
    """删除单条消息"""
    async with async_session() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        c = result.scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="对话不存在")
        msgs = json.loads(c.messages) if c.messages else []
        if msg_idx < 0 or msg_idx >= len(msgs):
            raise HTTPException(status_code=400, detail="消息索引越界")
        msgs.pop(msg_idx)
        c.messages = json.dumps(msgs, ensure_ascii=False)
        c.updated_at = datetime.utcnow()
        await session.commit()
        logger.info(f"删除消息: conv={conv_id}, idx={msg_idx}")
        return {"ok": True, "messages": msgs}
