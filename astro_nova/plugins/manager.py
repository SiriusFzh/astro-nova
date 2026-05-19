"""插件管理器 — 加载/卸载/热重载"""

import importlib
import importlib.util
import os
import sys
import traceback
from typing import Optional

from astro_nova.plugins.base import BasePlugin
from astro_nova.plugins.metadata import parse_plugin_yaml
from astro_nova.utils.logger import logger

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "plugins_user")


class PluginManager:
    """插件管理器 — 全局单例"""

    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}      # name → plugin instance
        self._loaded = False

    def _ensure_dir(self):
        os.makedirs(PLUGINS_DIR, exist_ok=True)
        if PLUGINS_DIR not in sys.path:
            sys.path.insert(0, PLUGINS_DIR)

    def load_plugin(self, dirpath: str) -> Optional[BasePlugin]:
        """从目录加载一个插件"""
        meta = parse_plugin_yaml(dirpath)
        if not meta:
            logger.warning(f"缺少 plugin.yaml: {dirpath}")
            return None

        name = meta["name"]
        if name in self._plugins:
            logger.warning(f"插件已存在: {name}")
            return None

        entry_file = os.path.join(dirpath, meta["entry"])
        if not os.path.isfile(entry_file):
            logger.warning(f"插件入口文件不存在: {entry_file}")
            return None

        try:
            # 动态导入
            spec = importlib.util.spec_from_file_location(
                f"plugin_{name}",
                entry_file,
            )
            if not spec or not spec.loader:
                return None

            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # 查找 BasePlugin 子类
            plugin_class = None
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                    plugin_class = attr
                    break

            if not plugin_class:
                logger.warning(f"插件中未找到 BasePlugin 子类: {name}")
                return None

            instance = plugin_class()
            instance.name = instance.name or name
            instance.metadata = meta

            self._plugins[name] = instance
            logger.info(f"已加载插件: {name} v{instance.version}")
            return instance

        except Exception as e:
            logger.error(f"加载插件失败 {name}: {e}\n{traceback.format_exc()}")
            return None

    def load_all(self, plugins_dir: str = None):
        """扫描目录加载所有插件"""
        self._ensure_dir()
        search_dir = plugins_dir or PLUGINS_DIR
        if not os.path.isdir(search_dir):
            return

        for entry in sorted(os.listdir(search_dir)):
            dirpath = os.path.join(search_dir, entry)
            if os.path.isdir(dirpath):
                self.load_plugin(dirpath)

    def unload_plugin(self, name: str) -> bool:
        """卸载插件"""
        plugin = self._plugins.pop(name, None)
        if not plugin:
            return False
        try:
            plugin.unregister_tools()
            importlib.invalidate_caches()
            logger.info(f"已卸载插件: {name}")
        except Exception as e:
            logger.error(f"卸载插件失败 {name}: {e}")
        return True

    async def start_plugin(self, name: str):
        """启动插件 (调用 on_load + 注册工具)"""
        plugin = self._plugins.get(name)
        if not plugin:
            return
        try:
            await plugin.on_load()
            plugin.register_tools()
            logger.info(f"已启动插件: {name}")
        except Exception as e:
            logger.error(f"启动插件失败 {name}: {e}")

    async def start_all(self):
        """启动所有已加载的插件"""
        for name in list(self._plugins.keys()):
            await self.start_plugin(name)
        self._loaded = True

    async def stop_plugin(self, name: str):
        """停止插件"""
        plugin = self._plugins.get(name)
        if not plugin:
            return
        try:
            await plugin.on_unload()
            plugin.unregister_tools()
        except Exception as e:
            logger.error(f"停止插件失败 {name}: {e}")

    async def reload_plugin(self, name: str) -> bool:
        """热重载插件"""
        await self.stop_plugin(name)
        self.unload_plugin(name)
        # 重新查找目录
        for entry in os.listdir(PLUGINS_DIR):
            dirpath = os.path.join(PLUGINS_DIR, entry)
            if os.path.isdir(dirpath):
                meta = parse_plugin_yaml(dirpath)
                if meta and meta.get("name") == name:
                    instance = self.load_plugin(dirpath)
                    if instance:
                        await self.start_plugin(name)
                        return True
        return False

    def list_plugins(self) -> list[dict]:
        """列出所有插件"""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "author": p.author,
                "is_active": p._tools_registered,
            }
            for p in self._plugins.values()
        ]

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        return self._plugins.get(name)


# 全局单例
manager = PluginManager()
