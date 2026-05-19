"""工具注册中心 — 插件和技能统一注册可调用工具"""
import json
from typing import Any, Callable, Coroutine


class Tool:
    """一个可调用的工具定义"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict,    # JSON Schema
        handler: Callable[..., Coroutine[Any, Any, str]],
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_openai_tool(self) -> dict:
        """转为 OpenAI tool 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_anthropic_tool(self) -> dict:
        """转为 Anthropic tool_use 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    async def execute(self, arguments: str | dict) -> str:
        """执行工具，返回结果字符串"""
        if isinstance(arguments, str):
            args = json.loads(arguments)
        else:
            args = arguments
        return await self.handler(**args)


class ToolRegistry:
    """全局工具注册中心"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def unregister(self, name: str):
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_all(self) -> list[Tool]:
        return list(self._tools.values())

    def get_all_dict(self) -> dict[str, Tool]:
        """返回 name→Tool 的 dict，供 provider 工具调用"""
        return dict(self._tools)

    def to_openai_tools(self) -> list[dict]:
        return [t.to_openai_tool() for t in self._tools.values()]

    def to_anthropic_tools(self) -> list[dict]:
        return [t.to_anthropic_tool() for t in self._tools.values()]

    def clear(self):
        self._tools.clear()


# 全局单例
registry = ToolRegistry()
