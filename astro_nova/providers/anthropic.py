"""Anthropic Claude API Provider — http.client 实现，零自动解压"""
import asyncio
import json
from typing import AsyncGenerator, Optional

from astro_nova.providers.base import BaseProvider, LLMMessage, LLMResponse
from astro_nova.tools.registry import Tool
from astro_nova.utils.proxy import create_https_connection


class AnthropicProvider(BaseProvider):
    """Anthropic Claude — http.client 实现"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key or "sk-placeholder",
            "anthropic-version": "2023-06-01",
        }

    def _connect(self) -> tuple:
        conn = create_https_connection("api.anthropic.com", timeout=120)
        return conn, "/v1/messages"

    def _build_messages(self, messages: list[LLMMessage]) -> list[dict]:
        conv = []
        for m in messages:
            if m.role == "system":
                continue
            if m.role == "tool":
                conv.append({
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": m.tool_call_id or "", "content": m.content}],
                })
            else:
                conv.append({"role": m.role, "content": m.content})
        return conv

    def _request(self, body: dict) -> dict:
        url = "https://api.anthropic.com/v1/messages"
        data = json.dumps(body).encode()
        conn, path = self._connect()
        try:
            conn.request("POST", path, body=data, headers=self._headers)
            resp = conn.getresponse()
            resp_body = resp.read()
            if resp.status >= 400:
                raise RuntimeError(
                    f"HTTP {resp.status}: {resp_body.decode(errors='replace')}"
                )
            return json.loads(resp_body)
        finally:
            conn.close()

    async def chat(self, messages: list[LLMMessage],
                   tools: Optional[dict[str, Tool]] = None,
                   **kwargs) -> LLMResponse:
        system = None
        for m in messages:
            if m.role == "system":
                system = m.content
                break

        conv = self._build_messages(messages)

        anthropic_tools = None
        tool_map: dict[str, Tool] = {}
        if tools:
            anthropic_tools = [t.to_anthropic_tool() for t in tools.values()]
            tool_map = tools

        for _ in range(self.MAX_TOOL_ROUNDS):
            body = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "messages": conv,
            }
            if system:
                body["system"] = system
            if anthropic_tools:
                body["tools"] = anthropic_tools

            result = await asyncio.to_thread(self._request, body)

            content_blocks = result.get("content", [])
            tool_blocks = [b for b in content_blocks if b.get("type") == "tool_use"]
            text_blocks = [b for b in content_blocks if b.get("type") == "text"]

            if not tool_blocks:
                return LLMResponse(
                    content=text_blocks[0]["text"] if text_blocks else "",
                    model=result.get("model", self.model),
                    usage={
                        "input_tokens": result.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": result.get("usage", {}).get("output_tokens", 0),
                    },
                )

            # Append assistant response (content blocks)
            asst_content: list[dict] = []
            if text_blocks:
                asst_content.append({"type": "text", "text": text_blocks[0]["text"]})
            for tb in tool_blocks:
                asst_content.append({"type": "tool_use", "id": tb["id"], "name": tb["name"], "input": tb["input"]})
            conv.append({"role": "assistant", "content": asst_content})

            # Execute each tool + append tool_result
            tool_result_contents: list[dict] = []
            for tb in tool_blocks:
                tool = tool_map.get(tb["name"])
                if not tool:
                    tool_result_contents.append({
                        "type": "tool_result",
                        "tool_use_id": tb["id"],
                        "content": f"未知工具: {tb['name']}",
                    })
                    continue
                try:
                    result_tool = await tool.execute(tb["input"])
                    tool_result_contents.append({
                        "type": "tool_result",
                        "tool_use_id": tb["id"],
                        "content": str(result_tool),
                    })
                except Exception as e:
                    tool_result_contents.append({
                        "type": "tool_result",
                        "tool_use_id": tb["id"],
                        "content": f"工具执行错误: {e}",
                    })
            conv.append({"role": "user", "content": tool_result_contents})

        return LLMResponse(content="工具调用次数过多，已自动终止", model=self.model)

    async def chat_stream(self, messages: list[LLMMessage],
                          tools: Optional[dict[str, Tool]] = None,
                          **kwargs) -> AsyncGenerator[str, None]:
        system = None
        for m in messages:
            if m.role == "system":
                system = m.content
                break

        body = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": self._build_messages(messages),
            "stream": True,
        }
        if system:
            body["system"] = system
        anthropic_tools = [t.to_anthropic_tool() for t in (tools or {}).values()] or None
        if anthropic_tools:
            body["tools"] = anthropic_tools

        data = json.dumps(body).encode()
        conn, path = self._connect()
        try:
            conn.request("POST", path, body=data, headers=self._headers)
            resp = conn.getresponse()
            if resp.status >= 400:
                err = resp.read().decode(errors="replace")
                raise RuntimeError(f"HTTP {resp.status}: {err}")

            buffer = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.strip()
                    if not line or line.startswith(b":"):
                        continue
                    if line.startswith(b"data: "):
                        try:
                            ev = json.loads(line[6:])
                            if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                                yield ev["delta"]["text"]
                        except json.JSONDecodeError:
                            pass
        finally:
            conn.close()
