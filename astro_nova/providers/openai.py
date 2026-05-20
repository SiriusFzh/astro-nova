"""OpenAI 兼容 API Provider — http.client 实现，零自动解压"""
import asyncio
import http.client
import json
from typing import AsyncGenerator, Optional
from urllib.parse import urlparse

from astro_nova.providers.base import BaseProvider, LLMMessage, LLMResponse
from astro_nova.tools.registry import Tool
from astro_nova.utils.proxy import create_https_connection, create_http_connection


class OpenAIProvider(BaseProvider):
    """OpenAI 兼容 API — 纯 http.client 实现"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._base = (self.api_base or "https://api.openai.com/v1").rstrip("/")
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or 'sk-placeholder'}",
        }

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
            # DeepSeek thinking mode requires reasoning_content field on assistant messages.
            # Must include the field (null is OK) to avoid API rejection.
            if m.role == "assistant":
                d["reasoning_content"] = m.reasoning_content
            msgs.append(d)
        return msgs

    def _connect(self, url: str) -> tuple:
        """建立 http.client 连接，返回 (conn, path)（支持代理）"""
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        if parsed.scheme == "https":
            # 国内访问 OpenAI/DeepSeek API 需要走代理
            conn = create_https_connection(host, port=port or 443, timeout=120)
        else:
            conn = create_http_connection(host, port=port or 80, timeout=120)
        return conn, path

    def _request(self, body: dict) -> dict:
        """发送 HTTP POST — 无自动解压，完全控制"""
        url = f"{self._base}/chat/completions"
        data = json.dumps(body).encode()
        conn, path = self._connect(url)
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
        msgs = self._build_messages(messages)
        openai_tools = [t.to_openai_tool() for t in (tools or {}).values()] or None

        for _ in range(self.MAX_TOOL_ROUNDS):
            body = {
                "model": self.model,
                "messages": msgs,
                **{k: v for k, v in kwargs.items() if k not in ("tools",)},
            }
            if openai_tools:
                body["tools"] = openai_tools
            body = {k: v for k, v in body.items() if v is not None}

            result = await asyncio.to_thread(self._request, body)

            choice = result.get("choices", [{}])[0]
            msg = choice.get("message", {})

            if not msg.get("tool_calls"):
                return LLMResponse(
                    content=msg.get("content") or "",
                    model=result.get("model", self.model),
                    usage=result.get("usage", {}),
                    reasoning_content=msg.get("reasoning_content"),
                )

            # Append assistant message with tool_calls
            asst: dict = {"role": "assistant", "content": msg.get("content")}
            asst["tool_calls"] = msg["tool_calls"]
            asst["reasoning_content"] = msg.get("reasoning_content")
            msgs.append(asst)

            # Execute each tool
            for tc in msg["tool_calls"]:
                tool = tools.get(tc["function"]["name"]) if tools else None
                if not tool:
                    msgs.append({
                        "role": "tool", "tool_call_id": tc["id"],
                        "content": f"未知工具: {tc['function']['name']}"
                    })
                    continue
                try:
                    result_tool = await tool.execute(tc["function"]["arguments"])
                    msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result_tool)})
                except Exception as e:
                    msgs.append({
                        "role": "tool", "tool_call_id": tc["id"],
                        "content": f"工具执行错误: {e}"
                    })

        return LLMResponse(content="工具调用次数过多，已自动终止", model=self.model)

    async def chat_stream(self, messages: list[LLMMessage],
                          tools: Optional[dict[str, Tool]] = None,
                          **kwargs) -> AsyncGenerator[str, None]:
        """流式 — http.client + SSE"""
        msgs = self._build_messages(messages)
        openai_tools = [t.to_openai_tool() for t in (tools or {}).values()] or None

        body = {
            "model": self.model,
            "messages": msgs,
            "stream": True,
            **{k: v for k, v in kwargs.items() if k not in ("tools",)},
        }
        if openai_tools:
            body["tools"] = openai_tools
        body = {k: v for k, v in body.items() if v is not None}

        url = f"{self._base}/chat/completions"
        data = json.dumps(body).encode()
        conn, path = self._connect(url)
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
                    if not line or line == b"data: [DONE]":
                        continue
                    if line.startswith(b"data: "):
                        try:
                            ev = json.loads(line[6:])
                            delta = ev.get("choices", [{}])[0].get("delta", {})
                            if delta.get("content"):
                                yield delta["content"]
                        except json.JSONDecodeError:
                            pass
        finally:
            conn.close()
