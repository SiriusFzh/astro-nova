"""数据库连接管理"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from astro_nova.database.models import Base
from astro_nova.utils.paths import get_db_path

DB_PATH = get_db_path()

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """获取数据库会话"""
    async with async_session() as session:
        yield session
