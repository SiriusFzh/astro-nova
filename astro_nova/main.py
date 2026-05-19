"""astro-nova FastAPI 应用"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from astro_nova.database.connection import init_db
from astro_nova.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("初始化数据库...")
    await init_db()

    # 注册所有内置工具
    from astro_nova.tools import register_all_tools
    register_all_tools()

    logger.info("AstroNova 已就绪")
    yield
    logger.info("AstroNova 已关闭")


app = FastAPI(
    title="AstroNova",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS (Electron 加载需要)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 健康检查 ──
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ── 导入并注册路由 ──
from astro_nova.api import chat, providers, settings, papers, notes, tools, knowledge, skills, plugins

app.include_router(chat.router, prefix="/api")
app.include_router(providers.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(plugins.router, prefix="/api")
