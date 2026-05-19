"""plugin.yaml 解析器"""

import os
import yaml
from typing import Optional


def parse_plugin_yaml(dirpath: str) -> Optional[dict]:
    """解析插件目录下的 plugin.yaml"""
    yaml_path = os.path.join(dirpath, "plugin.yaml")
    if not os.path.isfile(yaml_path):
        return None
    with open(yaml_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError:
            return None

    if not isinstance(data, dict):
        return None

    return {
        "name": data.get("name", os.path.basename(dirpath)),
        "version": data.get("version", "1.0.0"),
        "description": data.get("description", ""),
        "author": data.get("author", ""),
        "entry": data.get("entry", "main.py"),
        "enabled": data.get("enabled", True),
        "dependencies": data.get("dependencies", []),
    }
