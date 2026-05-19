"""ProviderManager — 多模型路由管理器

支持同时配置多个 LLM Provider，根据任务类型自动选择对应模型。
"""
from typing import Optional
from astro_nova.providers.base import BaseProvider, LLMMessage
from astro_nova.providers.openai import OpenAIProvider
from astro_nova.tools.registry import Tool
try:
    from astro_nova.providers.anthropic import AnthropicProvider
except ImportError:
    AnthropicProvider = None  # anthropic 包未安装
from astro_nova.utils.logger import logger

PROVIDER_REGISTRY = {
    "openai": OpenAIProvider,
    "deepseek": OpenAIProvider,   # DeepSeek 使用 OpenAI 兼容 API
    "ollama": OpenAIProvider,     # Ollama 同样兼容 OpenAI API
}
if AnthropicProvider:
    PROVIDER_REGISTRY["anthropic"] = AnthropicProvider


class ProviderManager:
    """多模型路由管理器"""

    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}

    def load_from_configs(self, configs: list[dict]):
        """从配置列表加载所有 Provider"""
        self._providers.clear()
        for cfg in configs:
            provider_type = cfg.get("provider_type", "")
            cls = PROVIDER_REGISTRY.get(provider_type)
            if not cls:
                logger.warning(f"未知 Provider 类型: {provider_type}")
                continue
            try:
                provider = cls(cfg)
                name = cfg.get("name", f"{provider_type}-{cfg.get('model', 'unknown')}")
                self._providers[name] = provider
                logger.info(f"已加载 Provider: {name} ({cfg.get('model', '')})")
            except Exception as e:
                logger.error(f"加载 Provider 失败: {cfg.get('name', '')}: {e}")

    def get_provider(self, task_type: str = "chat") -> Optional[BaseProvider]:
        """根据任务类型获取对应 Provider

        优先匹配 task_route 完全匹配的，其次匹配 "all"。
        """
        # 精确匹配
        for name, provider in self._providers.items():
            route = provider.config.get("task_route", "all")
            if route == task_type and provider.config.get("is_active", True):
                return provider
        # 回退到 all
        for name, provider in self._providers.items():
            route = provider.config.get("task_route", "all")
            if route == "all" and provider.config.get("is_active", True):
                return provider
        return None

    def get_all_providers(self) -> list[dict]:
        """获取所有 Provider 配置"""
        return [
            {
                "name": name,
                "provider_type": p.config.get("provider_type", ""),
                "display_name": p.config.get("display_name", name),
                "model": p.model,
                "task_route": p.config.get("task_route", "all"),
                "is_active": p.config.get("is_active", True),
            }
            for name, p in self._providers.items()
        ]

    async def chat(self, task_type: str, messages: list[LLMMessage],
                   tools: Optional[dict[str, Tool]] = None, **kwargs):
        """统一的 chat 入口 — 自动路由，支持工具调用"""
        provider = self.get_provider(task_type)
        if not provider:
            raise ValueError(f"没有可用的 Provider (task={task_type})")
        return await provider.chat(messages, tools=tools, **kwargs)

    async def chat_stream(self, task_type: str, messages: list[LLMMessage],
                          tools: Optional[dict[str, Tool]] = None, **kwargs):
        provider = self.get_provider(task_type)
        if not provider:
            raise ValueError(f"没有可用的 Provider (task={task_type})")
        async for chunk in provider.chat_stream(messages, tools=tools, **kwargs):
            yield chunk


# 全局单例
manager = ProviderManager()
