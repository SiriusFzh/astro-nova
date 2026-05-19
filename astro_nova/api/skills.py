"""技能管理 API"""
from fastapi import APIRouter
from pydantic import BaseModel
from astro_nova.skills.executor import manager

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("")
async def list_skills():
    return {"skills": manager.list_skills()}


@router.post("/{name}/activate")
async def activate_skill(name: str):
    ok = manager.activate(name)
    return {"status": "ok" if ok else "not_found"}


@router.post("/{name}/deactivate")
async def deactivate_skill(name: str):
    ok = manager.deactivate(name)
    return {"status": "ok" if ok else "not_found"}
