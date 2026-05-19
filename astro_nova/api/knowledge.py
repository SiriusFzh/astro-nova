"""知识库管理 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from astro_nova.knowledge.vector_store import get_store
from astro_nova.knowledge.retriever import retrieve, list_stores, get_store_info

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class SearchRequest(BaseModel):
    query: str
    store: str = "default"
    top_k: int = 10
    source_filter: Optional[str] = None


class IngestRequest(BaseModel):
    content: str
    source: str = ""
    store: str = "default"
    metadata: Optional[dict] = None


@router.get("/stores")
async def api_list_stores():
    return {"stores": list_stores()}


@router.get("/stores/{store_name}")
async def api_store_info(store_name: str):
    return get_store_info(store_name)


@router.post("/search")
async def api_search(req: SearchRequest):
    results = retrieve(
        query=req.query,
        store_name=req.store,
        top_k=req.top_k,
        source_filter=req.source_filter,
    )
    return {"results": results}


@router.post("/ingest")
async def api_ingest(req: IngestRequest):
    store = get_store(req.store)
    store.add_document(
        content=req.content,
        source=req.source,
        metadata=req.metadata,
    )
    return {"status": "ok", "doc_count": store.count()}


@router.post("/clear")
async def api_clear(store_name: str = "default"):
    store = get_store(store_name)
    store.clear()
    return {"status": "ok"}
