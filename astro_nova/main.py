"""astro-nova FastAPI 应用"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from astro_nova.database.connection import init_db
from astro_nova.utils.logger import logger
from astro_nova.utils.config import load_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 创建标准数据目录结构
    from astro_nova.utils.paths import ensure_data_dirs
    ensure_data_dirs()

    # 加载用户配置
    cfg = load_config()
    app.state.config = cfg

    # 应用日志等级
    log_level = cfg.get("log_level", "INFO")
    logger.setLevel(log_level)

    logger.info("初始化数据库...")
    await init_db()

    # 注册所有内置工具
    from astro_nova.tools import register_all_tools
    register_all_tools()

    # 笔记输出目录（支持配置覆盖）
    notes_dir = cfg.get("notes_dir")
    if notes_dir:
        from astro_nova.novaforge import engine
        engine.update_output_dir(notes_dir)
        logger.info(f"笔记输出目录: {notes_dir}")

    # 清理无效数据并加载 Provider
    from astro_nova.api.providers import _reload_providers
    from astro_nova.api.notes import cleanup_invalid_notes
    await _reload_providers()
    await cleanup_invalid_notes()

    logger.info("AstroNova 已就绪 (port=%s, log_level=%s)",
                cfg.get("port", 8615), log_level)
    yield
    logger.info("AstroNova 已关闭")


app = FastAPI(
    title="AstroNova",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS (桌面客户端需要)
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
from astro_nova.api import chat, providers, settings, papers, notes, tools, knowledge, skills, plugins, conversations

app.include_router(chat.router, prefix="/api")
app.include_router(providers.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(plugins.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
