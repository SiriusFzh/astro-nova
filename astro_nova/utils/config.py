"""配置管理"""
import json
import os

from astro_nova.utils.paths import get_config_path


def load_config() -> dict:
    path = get_config_path()
    if os.path.exists(path):
        return json.loads(open(path, "r", encoding="utf-8").read())
    return {}


def save_config(config: dict):
    path = get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(
        json.dumps(config, indent=2, ensure_ascii=False)
    )
