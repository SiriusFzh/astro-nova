"""Provider 配置管理 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional

from astro_nova.database.connection import async_session
from astro_nova.database.models import ProviderConfig
from astro_nova.providers.manager import manager
from astro_nova.utils.logger import logger
from sqlalchemy import select

router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderCreate(BaseModel):
    name: str
    provider_type: str
    display_name: str          # 供应商名称
    website: Optional[str] = ""  # 官网链接
    api_key: Optional[str] = ""
    api_base: Optional[str] = "" # API 地址
    model: str                   # 模型型号
    task_route: str = "all"
    is_active: bool = True

    @field_validator("name", "provider_type", "display_name", "model")
    @classmethod
    def not_blank(cls, v, info):
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} 不能为空")
        return v.strip()


class ProviderUpdate(ProviderCreate):
    pass


@router.get("")
async def list_providers():
    """列出所有 Provider 配置"""
    async with async_session() as session:
        result = await session.execute(select(ProviderConfig))
        providers = result.scalars().all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "provider_type": p.provider_type,
                "display_name": p.display_name,
                "website": p.website or "",
                "model": p.model,
                "api_base": p.api_base or "",
                "task_route": p.task_route,
                "is_active": p.is_active,
            }
            for p in providers
        ]


@router.post("")
async def create_provider(cfg: ProviderCreate):
    """添加 Provider 配置"""
    async with async_session() as session:
        exists = await session.execute(
            select(ProviderConfig).where(ProviderConfig.name == cfg.name)
        )
        if exists.scalar_one_or_none():
            raise HTTPException(400, f"Provider '{cfg.name}' 已存在")

        p = ProviderConfig(**cfg.model_dump())
        session.add(p)
        await session.commit()

    # 热重载 Provider
    await _reload_providers()
    return {"status": "ok", "name": cfg.name}


@router.put("/{provider_id}")
async def update_provider(provider_id: int, cfg: ProviderCreate):
    """更新 Provider 配置"""
    async with async_session() as session:
        p = await session.get(ProviderConfig, provider_id)
        if not p:
            raise HTTPException(404, "Provider 不存在")
        for key, value in cfg.model_dump().items():
            setattr(p, key, value)
        await session.commit()
    await _reload_providers()
    return {"status": "ok", "name": cfg.name}


@router.delete("/{provider_id}")
async def delete_provider(provider_id: int):
    """删除 Provider"""
    async with async_session() as session:
        p = await session.get(ProviderConfig, provider_id)
        if not p:
            raise HTTPException(404, "Provider 不存在")
        await session.delete(p)
        await session.commit()
    await _reload_providers()
    return {"status": "ok"}


async def _cleanup_invalid_providers():
    """清理数据库中缺少必填字段的 Provider 记录"""
    async with async_session() as session:
        result = await session.execute(select(ProviderConfig))
        all_configs = result.scalars().all()
        removed = 0
        for c in all_configs:
            if not c.name or not c.name.strip() or not c.provider_type or not c.display_name or not c.model:
                logger.warning(f"清理无效 Provider: id={c.id} name={c.name!r}")
                await session.delete(c)
                removed += 1
        if removed:
            await session.commit()
            logger.info(f"已清理 {removed} 个无效 Provider")


async def _reload_providers():
    """从数据库重新加载所有 Provider，先清理无效记录"""
    await _cleanup_invalid_providers()
    async with async_session() as session:
        result = await session.execute(select(ProviderConfig))
        configs = result.scalars().all()
        manager.load_from_configs([
            {
                "name": c.name,
                "provider_type": c.provider_type,
                "display_name": c.display_name,
                "website": c.website or "",
                "api_key": c.api_key or "",
                "api_base": c.api_base or "",
                "model": c.model,
                "task_route": c.task_route,
                "is_active": c.is_active,
            }
            for c in configs
        ])
