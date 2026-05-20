"""集中式路径管理

安装版（frozen）:
  - 数据目录 → %APPDATA%/AstroNova/data/   （重装不丢失）
  - 配置文件 → 安装目录/config.json         （与 Rust 共享）
开发版:
  - 所有目录 → 项目根目录下
"""
import os
import sys
import shutil
from pathlib import Path


def get_user_data_root() -> Path:
    """返回用户数据根目录（重装后仍保留）"""
    if getattr(sys, "frozen", False):
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "AstroNova"
    # 开发模式回退到项目根
    return Path(__file__).resolve().parent.parent.parent


def get_app_root() -> Path:
    """返回应用安装根目录（存放 astro-nova.exe 的目录）"""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable)
        parent = exe.parent
        if parent.name == "binaries":
            parent = parent.parent
        if parent.name == "src-tauri":
            parent = parent.parent
        return parent
    return Path(__file__).resolve().parent.parent.parent


def get_data_dir(subdir: str = "") -> str:
    """获取数据子目录的绝对路径，并保证目录存在

    安装版: %APPDATA%/AstroNova/data/<subdir>/
    开发版: <项目根>/data/<subdir>/
    """
    base = get_user_data_root() / "data"
    if subdir:
        base = base / subdir
    return str(base.resolve())


def get_config_path() -> str:
    """config.json 路径（始终在安装根目录下，与 Rust 端共享）"""
    return str(get_app_root() / "config.json")


def get_db_path() -> str:
    """SQLite 数据库路径

    安装版: %APPDATA%/AstroNova/data/astro_nova.db
    开发版: <项目根>/data/astro_nova.db
    """
    return str(get_user_data_root() / "data" / "astro_nova.db")


def migrate_from_old_install():
    """将旧安装目录下的数据迁移到 %APPDATA%/AstroNova/

    仅在 frozen 模式且 %APPDATA% 目标目录为空时执行。
    依次检查:
      1. 当前 exe 旁边的 data/（同一目录升级）
      2. 已知的旧安装路径
    """
    if not getattr(sys, "frozen", False):
        return

    dest_root = get_user_data_root()
    if dest_root == Path(__file__).resolve().parent.parent.parent:
        return  # 开发模式，不迁移

    dest_db = Path(get_db_path())
    if dest_db.exists():
        return  # 已迁移过，跳过

    # 候选旧数据目录
    candidates = [
        get_app_root() / "data",           # 与当前 exe 同目录
        Path("F:/Nova/AstroNova/data"),     # 已知的旧安装位置
    ]

    for old_data in candidates:
        old_data = old_data.resolve()
        if not old_data.is_dir():
            continue
        db_file = old_data / "astro_nova.db"
        if not db_file.exists():
            continue
        # 找到有效旧数据 → 迁移
        dest_root.mkdir(parents=True, exist_ok=True)
        dest_data = dest_root / "data"
        if not dest_data.exists():
            try:
                shutil.copytree(str(old_data), str(dest_data))
                from astro_nova.utils.logger import logger
                logger.info(f"已从旧位置迁移数据: {old_data} → {dest_data}")
            except Exception as e:
                from astro_nova.utils.logger import logger
                logger.warning(f"数据迁移失败: {e}")
        return  # 只迁移一次


def ensure_data_dirs():
    """创建标准数据目录结构（启动时调用一次）"""
    # 首先尝试从旧位置迁移
    migrate_from_old_install()

    dirs = [
        "notes",
        "papers",
        "knowledge",
        "digest",
        "figures",
        "slides",
        "writing",
        "novaforge-templates",
    ]
    base = get_user_data_root() / "data"
    for name in dirs:
        (base / name).mkdir(parents=True, exist_ok=True)

    # logs 目录在安装根目录下
    (get_app_root() / "logs").mkdir(parents=True, exist_ok=True)
