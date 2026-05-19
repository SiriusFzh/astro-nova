"""技能执行器 — 管理技能激活、触发匹配、系统提示组装"""
import re
from typing import Optional
from astro_nova.skills.loader import SkillDef, load_all_skills, extract_triggers


class SkillManager:
    """技能管理器 — 全局单例"""

    def __init__(self):
        self._skills: dict[str, SkillDef] = {}       # name → SkillDef
        self._active: set[str] = set()                # 当前激活的技能名
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True
        for skill in load_all_skills():
            self._skills[skill.name] = skill
            if not skill.triggers:
                skill.triggers = extract_triggers(skill.prompt)
        # 默认激活所有 skill
        self._active = set(self._skills.keys())

    def list_skills(self) -> list[dict]:
        """返回所有技能列表"""
        self._ensure_loaded()
        return [
            {
                **s.to_dict(),
                "is_active": s.name in self._active,
            }
            for s in self._skills.values()
        ]

    def get_skill(self, name: str) -> Optional[SkillDef]:
        self._ensure_loaded()
        return self._skills.get(name)

    def activate(self, name: str) -> bool:
        self._ensure_loaded()
        if name in self._skills:
            self._active.add(name)
            return True
        return False

    def deactivate(self, name: str) -> bool:
        self._ensure_loaded()
        if name in self._skills:
            self._active.discard(name)
            return True
        return False

    def is_active(self, name: str) -> bool:
        self._ensure_loaded()
        return name in self._active

    def get_active_skills(self) -> list[SkillDef]:
        """获取当前激活的技能列表"""
        self._ensure_loaded()
        return [self._skills[n] for n in self._active if n in self._skills]

    def match_triggers(self, user_message: str) -> list[SkillDef]:
        """匹配用户消息中的触发词，返回匹配的技能"""
        self._ensure_loaded()
        matched = []
        msg = user_message.lower()
        for name in self._active:
            skill = self._skills.get(name)
            if not skill:
                continue
            for trigger in skill.triggers:
                tlow = trigger.lower()
                # 参数化触发词: "latest on [topic]" → 匹配前缀 "latest on "
                if "[" in tlow and "]" in tlow:
                    prefix = tlow.split("[")[0].strip()
                    if prefix and msg.startswith(prefix):
                        matched.append(skill)
                        break
                elif tlow in msg:
                    matched.append(skill)
                    break
        return matched

    def build_system_prompt(self, task_type: str = "chat") -> str:
        """将所有激活技能的 prompt 组装为 system prompt"""
        skills = self.get_active_skills()
        if not skills:
            return ""

        parts = ["你是一个天文学科研助手。以下是你可以使用的技能及其指令：\n"]
        for s in skills:
            parts.append(f"===== {s.name}: {s.description} =====\n")
            parts.append(s.prompt)
            parts.append("\n\n")

        return "".join(parts).strip()


# 全局单例
manager = SkillManager()
