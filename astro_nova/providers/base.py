"""LLM Provider 抽象基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional

from astro_nova.tools.registry import Tool


@dataclass
class LLMMessage:
    """统一消息格式"""
    role: str        # "system" / "user" / "assistant" / "tool"
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    reasoning_content: Optional[str] = None  # DeepSeek thinking mode


@dataclass
class LLMResponse:
    """统一响应格式"""
    content: str
    reasoning_content: Optional[str] = None
    role: str = "assistant"
    model: str = ""
    usage: dict = field(default_factory=dict)
    tool_calls: Optional[list[dict]] = None   # [{name, arguments}]


class BaseProvider(ABC):
    """Provider 抽象基类 — 所有 LLM 后端统一接口"""

    MAX_TOOL_ROUNDS = 12

    def __init__(self, config: dict):
        self.config = config
        self.name = config.get("name", "")
        self.model = config.get("model", "")
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "")

    @abstractmethod
    async def chat(self, messages: list[LLMMessage],
                   tools: Optional[dict[str, Tool]] = None,
                   **kwargs) -> LLMResponse:
        """非流式对话 — 支持工具调用"""
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[LLMMessage],
                          tools: Optional[dict[str, Tool]] = None,
                          **kwargs) -> AsyncGenerator[str, None]:
        """流式对话，逐 chunk 产出文本"""
        ...
        yield ""  # pragma: no cover
