"""对话 API 路由 — 自动注入技能 + 工具调用 + NovaForge 工作流

工作流程（LLM 驱动的端到端笔记生成）:
  用户: "帮我读一下 2301.00001 并生成笔记"
  LLM:  1. 调用 read_arxiv_paper(arxiv_id="2301.00001")
        2. 获取精读结果
        3. 调用 generate_note(arxiv_id="2301.00001", title="...", content="...")
        4. NovaForge 自动编译 LaTeX → PDF
        5. 返回笔记链接和摘要

  用户: "搜索中子星合并的论文"
  LLM:  1. 调用 search_arxiv(query="neutron star mergers")
        2. 返回结果列表供用户选择
"""
import traceback
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from pydantic import BaseModel

from astro_nova.providers.base import LLMMessage
from astro_nova.providers.manager import manager as provider_manager
from astro_nova.skills.executor import manager as skill_manager
from astro_nova.tools.registry import registry as tool_registry
from astro_nova.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    messages: list[dict]       # [{"role": "user", "content": "..."}]
    task_type: str = "chat"    # chat / search / read / write / code
    stream: bool = False


class ChatResponse(BaseModel):
    content: str
    model: str = ""
    reasoning_content: Optional[str] = None


# LLM 工具注入 — 告知 LLM 有哪些科研工具可用
TOOL_SYSTEM_PROMPT = """# 身份与风格
你是一个天文学科研助手。你的回答风格是：

1. **日常交流**：像正常朋友一样自然对话。被问好时简单回一句"你好！👋 我是你的天文学科研助手，很高兴为你服务！"即可，不要主动推送功能列表或 arXiv digest 推销。
2. **回答问题**：用平常的语言直说，别搞花哨格式。不要使用 emoji、表格、Markdown 分级标题、引用块等排版元素——除非用户明确要求。说几句话把事说清楚就行，不需要展开成完整文章。
3. **工具调用**：当用户明确需要你执行操作（搜论文、读论文、生成笔记等）时，再调用相应工具。不要在日常闲聊中推送工具能力。

# 内置工具能力
你可以自主调用以下工具来完成用户的科研请求：

## 文献检索
- **search_arxiv**(query, max_results, categories) — 搜索 arXiv 天文学论文
- **fetch_arxiv_paper**(arxiv_id, format) — 获取论文全文文本（自动 PDF→HTML→摘要三级回退）

## 论文精读
- **read_arxiv_paper**(arxiv_id, language) — 一站式精读: 自动下载+LLM分析+7维结构化笔记

## NovaForge 笔记生成
- **generate_note**(arxiv_id, title, content, mode, compile_pdf) — 用 NovaForge 引擎生成结构化笔记（支持 research-note / chapter-notes / exam-review / kaoyan / gongkao / project 等模式）
- **get_novaforge_modes**() — 列出所有可用模板模式
- **list_notes**() — 列出所有已生成的笔记
- **compile_latex_to_pdf**(tex_path) — 手动编译 .tex → PDF

## 推荐工作流
1. 搜索论文 → 用户选择 → 精读 → 生成笔记
2. 直接输入 arXiv ID → 精读 → 生成笔记
3. 已有精读内容 → 生成笔记

## 注意
- 生成笔记后告知用户 PDF 路径
- 用户不提模式时默认用 research-note（科研笔记）
"""


@router.post("")
async def chat(req: ChatRequest, request: Request):
    """非流式对话 — 自动注入技能 system prompt + 可用工具"""
    messages = [
        LLMMessage(
            role=m["role"],
            content=m["content"],
            reasoning_content=m.get("reasoning_content"),
        )
        for m in req.messages
    ]

    # 注入工具系统提示
    has_system = any(m.role == "system" for m in messages)
    tool_injected = False
    if has_system:
        for i, m in enumerate(messages):
            if m.role == "system":
                messages.insert(i + 1, LLMMessage(role="system", content=TOOL_SYSTEM_PROMPT))
                tool_injected = True
                break
    else:
        messages.insert(0, LLMMessage(role="system", content=TOOL_SYSTEM_PROMPT))
        tool_injected = True

    # 注入技能 system prompt（追加在工具提示之后）
    skill_prompt = skill_manager.build_system_prompt(req.task_type)
    if skill_prompt:
        messages.append(LLMMessage(role="system", content=skill_prompt))

    # 获取所有已注册的工具 (插件 + 内置)
    tools = tool_registry.get_all_dict()

    # 从用户配置读取 LLM 参数
    cfg = getattr(request.app.state, "config", {})
    llm_kwargs = {
        "max_tokens": cfg.get("max_tokens"),
        "temperature": cfg.get("temperature"),
    }
    llm_kwargs = {k: v for k, v in llm_kwargs.items() if v is not None}

    # 让大模型自行决定是否进行深度思考（不传 thinking 参数 = 模型默认行为）
    # 部分模型（如 deepseek-reasoner）自带思考，不影响；非思考模型则直接快速回复

    try:
        resp = await provider_manager.chat(req.task_type, messages, tools=tools, **llm_kwargs)
        return ChatResponse(
            content=resp.content,
            model=resp.model,
            reasoning_content=resp.reasoning_content,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"LLM 调用失败:\n{tb}")
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {e}\n\n{tb}")
