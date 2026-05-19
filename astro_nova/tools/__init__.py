"""科研工具包 — 所有工具模块在此注册到 ToolRegistry"""
from astro_nova.tools.registry import registry
from astro_nova.utils.logger import logger


def register_all_tools():
    """注册所有内置工具到全局 ToolRegistry"""
    count_before = len(registry.list_all())

    # 已有工具（直接注册顶层函数）
    from astro_nova.tools.arxiv_search import search_arxiv, fetch_by_id
    from astro_nova.tools.registry import Tool

    registry.register(Tool(
        name="search_arxiv",
        description="搜索 arXiv 天文学论文，返回标题/作者/摘要/PDF链接",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "max_results": {"type": "integer", "description": "返回结果数量", "default": 10},
                "categories": {
                    "type": "array", "items": {"type": "string"},
                    "description": "arXiv 分类, 默认 astro-ph",
                },
            },
            "required": ["query"],
        },
        handler=lambda query, max_results=10, categories=None: search_arxiv(query, max_results, categories),
    ))

    # 新工具模块 — 每个模块有自己的 register_tools()
    modules = [
        "astro_nova.tools.paper_reader",
        "astro_nova.tools.note_generator",
        "astro_nova.tools.figure_generator",
        "astro_nova.tools.writing_assistant",
        "astro_nova.tools.ppt_generator",
    ]

    for mod_name in modules:
        try:
            mod = __import__(mod_name, fromlist=["register_tools"])
            if hasattr(mod, "register_tools"):
                mod.register_tools()
        except Exception as e:
            logger.error(f"注册工具模块失败 {mod_name}: {e}")

    count_after = len(registry.list_all())
    logger.info(f"已注册 {count_after} 个工具 (新增 {count_after - count_before})")
