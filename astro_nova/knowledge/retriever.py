"""检索器 — 知识库查询入口，支持多库混合检索"""
from typing import Optional
from astro_nova.knowledge.vector_store import get_store, VectorStore


def retrieve(
    query: str,
    store_name: str = "default",
    top_k: int = 10,
    source_filter: Optional[str] = None,
) -> list[dict]:
    """检索知识库。

    Args:
        query: 查询字符串
        store_name: 知识库名称
        top_k: 返回 top N
        source_filter: 可选，按来源过滤

    Returns:
        [{content, content_full, source, score, metadata}]
    """
    store = get_store(store_name)
    results = store.search(query, top_k)

    if source_filter:
        results = [r for r in results if source_filter in r.get("source", "")]

    return results


def retrieve_with_context(
    query: str,
    store_name: str = "default",
    top_k: int = 5,
    max_chars: int = 4000,
) -> str:
    """检索并拼接为上下文文本，可直接填入 LLM prompt。"""
    results = retrieve(query, store_name, top_k)
    if not results:
        return ""

    parts = []
    total = 0
    for r in results:
        content = r["content_full"]
        source = r.get("source", "unknown")
        snippet = f"[来源: {source}]\n{content}\n"
        if total + len(snippet) > max_chars:
            break
        parts.append(snippet)
        total += len(snippet)

    return "\n---\n".join(parts)


def list_stores() -> list[str]:
    """列出所有知识库。"""
    import os
    from astro_nova.knowledge.vector_store import STORAGE_DIR
    stores = []
    if os.path.exists(STORAGE_DIR):
        for f in os.listdir(STORAGE_DIR):
            if f.endswith(".json"):
                stores.append(f[:-5])
    return stores or ["default"]


def get_store_info(store_name: str = "default") -> dict:
    """获取知识库信息。"""
    store = get_store(store_name)
    return {
        "name": store_name,
        "doc_count": store.count(),
        "sources": store.sources(),
    }
