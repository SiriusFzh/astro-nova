"""Anthropic Claude API Provider"""
from typing import AsyncGenerator, Optional

from anthropic import AsyncAnthropic

from astro_nova.providers.base import BaseProvider, LLMMessage, LLMResponse
from astro_nova.tools.registry import Tool


class AnthropicProvider(BaseProvider):
    """Anthropic Claude"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.client = AsyncAnthropic(
            api_key=self.api_key or "sk-placeholder",
        )

    def _build_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert LLMMessages to Anthropic message format, handling tool_blocks."""
        conv = []
        for m in messages:
            if m.role == "system":
                continue
            if m.role == "tool":
                # Anthropic: tool_result is a content block
                conv.append({
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": m.tool_call_id or "", "content": m.content}],
                })
            else:
                conv.append({"role": m.role, "content": m.content})
        return conv

    async def chat(self, messages: list[LLMMessage],
                   tools: Optional[dict[str, Tool]] = None,
                   **kwargs) -> LLMResponse:
        system = None
        for m in messages:
            if m.role == "system":
                system = m.content
                break

        # 构建初始 Anthropic-format 消息列表，后续 tool 轮次直接操作
        conv = self._build_messages(messages)

        anthropic_tools = None
        tool_map: dict[str, Tool] = {}
        if tools:
            anthropic_tools = [t.to_anthropic_tool() for t in tools.values()]
            tool_map = tools

        for _ in range(self.MAX_TOOL_ROUNDS):
            resp = await self.client.messages.create(
                model=self.model,
                system=system,
                messages=conv,
                tools=anthropic_tools,
                max_tokens=kwargs.get("max_tokens", 4096),
            )

            tool_blocks = [b for b in resp.content if b.type == "tool_use"]
            text_blocks = [b for b in resp.content if b.type == "text"]

            if not tool_blocks:
                return LLMResponse(
                    content=text_blocks[0].text if text_blocks else "",
                    model=resp.model,
                    usage={"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens},
                )

            # Append assistant response (content blocks)
            asst_content: list[dict] = []
            if text_blocks:
                asst_content.append({"type": "text", "text": text_blocks[0].text})
            for tb in tool_blocks:
                asst_content.append({"type": "tool_use", "id": tb.id, "name": tb.name, "input": tb.input})
            conv.append({"role": "assistant", "content": asst_content})

            # Execute each tool + append tool_result
            tool_result_contents: list[dict] = []
            for tb in tool_blocks:
                tool = tool_map.get(tb.name)
                if not tool:
                    tool_result_contents.append({
                        "type": "tool_result",
                        "tool_use_id": tb.id,
                        "content": f"未知工具: {tb.name}",
                    })
                    continue
                try:
                    result = await tool.execute(tb.input)
                    tool_result_contents.append({
                        "type": "tool_result",
                        "tool_use_id": tb.id,
                        "content": str(result),
                    })
                except Exception as e:
                    tool_result_contents.append({
                        "type": "tool_result",
                        "tool_use_id": tb.id,
                        "content": f"工具执行错误: {e}",
                    })
            conv.append({"role": "user", "content": tool_result_contents})

        return LLMResponse(content="工具调用次数过多，已自动终止", model=resp.model if "resp" in dir() else "")

    async def chat_stream(self, messages: list[LLMMessage],
                          tools: Optional[dict[str, Tool]] = None,
                          **kwargs) -> AsyncGenerator[str, None]:
        system = None
        for m in messages:
            if m.role == "system":
                system = m.content
                break

        anthropic_tools = [t.to_anthropic_tool() for t in (tools or {}).values()] or None

        async with self.client.messages.stream(
            model=self.model,
            system=system,
            messages=self._build_messages(messages),
            tools=anthropic_tools,
            max_tokens=kwargs.get("max_tokens", 4096),
        ) as stream:
            async for text in stream.text_stream:
                yield text
