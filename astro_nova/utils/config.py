"""配置管理"""
import json
import os
from pathlib import Path

DATA_DIR = Path(os.path.expanduser("~")) / ".astro-nova"
CONFIG_PATH = DATA_DIR / "config.json"


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_data_dir()
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(config: dict):
    ensure_data_dir()
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
