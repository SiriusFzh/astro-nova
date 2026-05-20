"""DeepSeek Provider — 使用 OpenAI 兼容接口"""
from astro_nova.providers.openai import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek API (OpenAI 兼容)"""

    def __init__(self, config: dict):
        # DeepSeek 默认 API 地址
        if not config.get("api_base"):
            config["api_base"] = "https://api.deepseek.com/v1"
        super().__init__(config)
