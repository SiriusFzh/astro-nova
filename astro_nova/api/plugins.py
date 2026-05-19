"""插件管理 API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from astro_nova.plugins.manager import manager as plugin_manager
from astro_nova.tools.registry import registry as tool_registry
from astro_nova.utils.logger import logger

router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginResponse(BaseModel):
    name: str
    version: str
    description: str
    author: str
    is_active: bool


@router.get("")
async def list_plugins():
    """列出所有已加载的插件"""
    plugins = plugin_manager.list_plugins()
    # 补充工具数量信息
    result = []
    for p in plugins:
        tools = [t for t in tool_registry.list_all() if t.name.startswith(p["name"])]
        p["tool_count"] = len(tools)
        result.append(p)
    return {"plugins": result}


@router.post("/{name}/load")
async def load_plugin(name: str):
    """手动加载一个插件"""
    from astro_nova.plugins.manager import PLUGINS_DIR
    import os

    dirpath = os.path.join(PLUGINS_DIR, name)
    if not os.path.isdir(dirpath):
        # 在所有子目录中查找
        for entry in os.listdir(PLUGINS_DIR):
            candidate = os.path.join(PLUGINS_DIR, entry)
            if os.path.isdir(candidate):
                try:
                    from astro_nova.plugins.metadata import parse_plugin_yaml
                    meta = parse_plugin_yaml(candidate)
                    if meta and meta.get("name") == name:
                        dirpath = candidate
                        break
                except Exception:
                    continue
        else:
            raise HTTPException(status_code=404, detail=f"插件 {name} 未找到")

    instance = plugin_manager.load_plugin(dirpath)
    if not instance:
        raise HTTPException(status_code=400, detail=f"插件 {name} 加载失败")

    await plugin_manager.start_plugin(name)
    return {"message": f"插件 {name} 已加载", "name": name}


@router.post("/{name}/unload")
async def unload_plugin(name: str):
    """卸载插件"""
    await plugin_manager.stop_plugin(name)
    ok = plugin_manager.unload_plugin(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"插件 {name} 未找到")
    return {"message": f"插件 {name} 已卸载", "name": name}


@router.post("/{name}/reload")
async def reload_plugin(name: str):
    """热重载插件"""
    ok = await plugin_manager.reload_plugin(name)
    if not ok:
        raise HTTPException(status_code=400, detail=f"插件 {name} 重载失败")
    return {"message": f"插件 {name} 已重载", "name": name}


@router.post("/scan")
async def scan_plugins():
    """扫描 plugins_user 目录加载所有插件"""
    count_before = len(plugin_manager.list_plugins())
    plugin_manager.load_all()
    await plugin_manager.start_all()
    count_after = len(plugin_manager.list_plugins())
    return {
        "message": f"扫描完成，新增 {count_after - count_before} 个插件",
        "total": count_after,
    }
