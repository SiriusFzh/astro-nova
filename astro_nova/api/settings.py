"""设置 API"""
from fastapi import APIRouter
from astro_nova.utils.config import load_config, save_config

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings():
    return load_config()


@router.post("")
async def update_settings(config: dict):
    save_config(config)
    return {"status": "ok"}
