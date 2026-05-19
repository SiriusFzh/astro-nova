"""OpenAI 兼容 API Provider (OpenAI / DeepSeek / SiliconFlow / 任何兼容 API)"""
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from astro_nova.providers.base import BaseProvider, LLMMessage, LLMResponse
from astro_nova.tools.registry import Tool


class OpenAIProvider(BaseProvider):
    """OpenAI 兼容 API"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.client = AsyncOpenAI(
            api_key=self.api_key or "sk-placeholder",
            base_url=self.api_base or "https://api.openai.com/v1",
        )

    def _build_messages(self, messages: list[LLMMessage]) -> list[dict]:
        msgs = []
        for m in messages:
            d = {"role": m.role}
            if m.role == "tool":
                d["tool_call_id"] = m.tool_call_id or ""
                d["content"] = m.content
            else:
                d["content"] = m.content
            if m.name:
                d["name"] = m.name
            msgs.append(d)
        return msgs

    async def chat(self, messages: list[LLMMessage],
                   tools: Optional[dict[str, Tool]] = None,
                   **kwargs) -> LLMResponse:
        msgs = self._build_messages(messages)
        openai_tools = [t.to_openai_tool() for t in (tools or {}).values()] or None

        for _ in range(self.MAX_TOOL_ROUNDS):
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=msgs,
                tools=openai_tools,
                **{k: v for k, v in kwargs.items() if k not in ("tools",)},
            )
            choice = resp.choices[0]
            msg = choice.message

            if not msg.tool_calls:
                return LLMResponse(
                    content=msg.content or "",
                    model=resp.model,
                    usage=dict(resp.usage) if resp.usage else {},
                )

            # Append assistant message with tool_calls
            asst: dict = {"role": "assistant", "content": msg.content}
            asst["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
            msgs.append(asst)

            # Execute each tool
            for tc in msg.tool_calls:
                tool = tools.get(tc.function.name) if tools else None
                if not tool:
                    msgs.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": f"未知工具: {tc.function.name}"
                    })
                    continue
                try:
                    result = await tool.execute(tc.function.arguments)
                    msgs.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
                except Exception as e:
                    msgs.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": f"工具执行错误: {e}"
                    })

        return LLMResponse(content="工具调用次数过多，已自动终止", model=resp.model if "resp" in dir() else "")

    async def chat_stream(self, messages: list[LLMMessage],
                          tools: Optional[dict[str, Tool]] = None,
                          **kwargs) -> AsyncGenerator[str, None]:
        msgs = self._build_messages(messages)
        openai_tools = [t.to_openai_tool() for t in (tools or {}).values()] or None

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            tools=openai_tools,
            stream=True,
            **{k: v for k, v in kwargs.items() if k not in ("tools",)},
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
