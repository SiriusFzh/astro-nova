"""SKILL.md 加载器 — 解析 YAML frontmatter + Markdown 内容"""
import os
import re
import yaml
from pathlib import Path
from typing import Optional

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "skills")

# frontmatter 正则: --- ... ---
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class SkillDef:
    """单个技能的定义"""
    __slots__ = ("name", "description", "prompt", "source_path", "triggers")

    def __init__(self, name: str, description: str, prompt: str, source_path: str = "", triggers: list = None):
        self.name = name
        self.description = description
        self.prompt = prompt        # SKILL.md 正文（不含 frontmatter）
        self.source_path = source_path
        self.triggers = triggers or []

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "prompt_preview": self.prompt[:200] if self.prompt else "",
            "triggers": self.triggers,
        }


def parse_skill_md(filepath: str) -> Optional[SkillDef]:
    """解析单个 SKILL.md 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    m = _FM_RE.match(content)
    if not m:
        # 没有 frontmatter，整个文件作为 prompt
        return SkillDef(
            name=Path(filepath).parent.name,
            description="",
            prompt=content.strip(),
            source_path=filepath,
        )

    try:
        meta = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        meta = {}

    body = content[m.end():].strip()
    name = meta.get("name", Path(filepath).parent.name)
    description = meta.get("description", "")
    triggers = meta.get("triggers", [])

    return SkillDef(
        name=name,
        description=description,
        prompt=body,
        source_path=filepath,
        triggers=triggers,
    )


def load_all_skills(skills_dir: str = None) -> list[SkillDef]:
    """扫描 skills/ 目录下所有 SKILL.md，返回列表"""
    if skills_dir is None:
        skills_dir = SKILLS_DIR
    if not os.path.exists(skills_dir):
        return []

    skills = []
    for entry in sorted(os.listdir(skills_dir)):
        skill_dir = os.path.join(skills_dir, entry)
        skill_file = os.path.join(skill_dir, "SKILL.md")
        if os.path.isdir(skill_dir) and os.path.isfile(skill_file):
            skill = parse_skill_md(skill_file)
            if skill:
                skills.append(skill)
    return skills


def extract_triggers(prompt: str) -> list[str]:
    """从 SKILL.md 的 '## 触发方式' 节中提取触发关键词"""
    lines = prompt.split("\n")
    in_triggers = False
    triggers = []
    for line in lines:
        if "触发" in line and line.startswith("##"):
            in_triggers = True
            continue
        if in_triggers:
            if line.startswith("##"):
                break
            stripped = line.strip()
            if stripped.startswith("- "):
                raw = stripped[2:].strip()
                for part in re.split(r"[//]", raw):
                    part = part.strip().strip('"').strip("'").strip("“").strip("”")
                    if part and len(part) > 1:
                        triggers.append(part)
    return triggers
