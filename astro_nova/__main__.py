"""astro-nova 桌面客户端入口"""
import uvicorn
from astro_nova.main import app
from astro_nova.utils.config import load_config
from astro_nova.utils.logger import logger

if __name__ == "__main__":
    cfg = load_config()
    port = cfg.get("port", 8615)
    log_level = cfg.get("log_level", "info").lower()

    logger.info("AstroNova 启动中 (port=%s)...", port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level=log_level)
