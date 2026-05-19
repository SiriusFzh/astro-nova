"""对话 API 路由 — 自动注入技能 + 工具调用"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from astro_nova.providers.base import LLMMessage
from astro_nova.providers.manager import manager as provider_manager
from astro_nova.skills.executor import manager as skill_manager
from astro_nova.tools.registry import registry as tool_registry

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    messages: list[dict]       # [{"role": "user", "content": "..."}]
    task_type: str = "chat"    # chat / search / read / write / code
    stream: bool = False


class ChatResponse(BaseModel):
    content: str
    model: str = ""


@router.post("")
async def chat(req: ChatRequest):
    """非流式对话 — 自动注入技能 system prompt + 可用工具"""
    messages = [LLMMessage(role=m["role"], content=m["content"]) for m in req.messages]

    # 注入技能 system prompt
    skill_prompt = skill_manager.build_system_prompt(req.task_type)
    if skill_prompt:
        has_system = any(m.role == "system" for m in messages)
        if has_system:
            for i, m in enumerate(messages):
                if m.role == "system":
                    messages.insert(i + 1, LLMMessage(role="system", content=skill_prompt))
                    break
        else:
            messages.insert(0, LLMMessage(role="system", content=skill_prompt))

    # 获取所有已注册的工具 (插件 + 内置)
    tools = tool_registry.get_all_dict()

    try:
        resp = await provider_manager.chat(req.task_type, messages, tools=tools)
        return ChatResponse(content=resp.content, model=resp.model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")
