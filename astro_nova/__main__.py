"""astro-nova 桌面客户端入口"""
import uvicorn
from astro_nova.main import app
from astro_nova.utils.logger import logger

if __name__ == "__main__":
    logger.info("AstroNova 启动中...")
    uvicorn.run(app, host="127.0.0.1", port=8615, log_level="info")
