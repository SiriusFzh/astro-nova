"""NovaForge 模板模式定义 — 六种预设模式

每种模式包含：
  - id: 唯一标识
  - name: 显示名
  - description: 简要说明
  - sections: 章节列表
  - cover_fields: 封面字段
  - is_academic: 是否学术模式（影响页眉/文献卡片）
"""

from dataclasses import dataclass, field


@dataclass
class NovaForgeMode:
    id: str
    name: str
    description: str
    sections: list[str] = field(default_factory=list)
    is_academic: bool = False
    has_paper_card: bool = False
    has_exercises: bool = False


MODES: dict[str, NovaForgeMode] = {
    "research-note": NovaForgeMode(
        id="research-note",
        name="科研笔记",
        description="文献/科研笔记 — 论文精读、研究课题的结构化笔记",
        sections=[
            "文献卡片", "研究背景与问题", "方法与技术路线",
            "核心结果与发现", "创新点与贡献", "局限性与未来工作",
            "个人思考与启发",
        ],
        is_academic=True,
        has_paper_card=True,
    ),
    "chapter-notes": NovaForgeMode(
        id="chapter-notes",
        name="章节笔记",
        description="7 步模块化结构 — 系统学习新知识，每节 7 步",
        sections=[
            "概念引入", "核心原理", "方法技巧",
            "典型示例", "真题/实战", "巩固练习", "专题总结",
        ],
        has_exercises=True,
    ),
    "exam-review": NovaForgeMode(
        id="exam-review",
        name="期末复习",
        description="真题分类 + 留白练习 — 备考冲刺专用",
        sections=[
            "题型分类", "高频考点", "易错点",
            "典型真题", "模拟练习", "答题模板",
        ],
        has_exercises=True,
    ),
    "kaoyan": NovaForgeMode(
        id="kaoyan",
        name="考研模式",
        description="7 步 + 考研真题 — 考研专业课专用",
        sections=[
            "概念引入", "核心原理", "方法技巧",
            "典型示例", "考研真题", "巩固练习", "专题总结",
        ],
        has_exercises=True,
    ),
    "gongkao": NovaForgeMode(
        id="gongkao",
        name="考公模式",
        description="行测/申论/面试考点分类",
        sections=[
            "考点概述", "解题方法", "典型示例",
            "真题实战", "易错归纳", "模拟训练",
        ],
        has_exercises=True,
    ),
    "project": NovaForgeMode(
        id="project",
        name="项目模式",
        description="项目文档 — 架构/进度/决策/复盘",
        sections=[
            "项目概览", "架构设计", "技术选型",
            "进度追踪", "问题与决策", "复盘总结",
        ],
    ),
}


def get_mode(mode_id: str) -> NovaForgeMode:
    """获取模式定义，fallback 到 research-note"""
    return MODES.get(mode_id, MODES["research-note"])


def guess_mode_from_query(query: str) -> str:
    """根据用户查询猜测最合适的模式"""
    q = query.lower()
    if any(k in q for k in ["考研", "kaoyan", "专业课"]):
        return "kaoyan"
    if any(k in q for k in ["考公", "公考", "行测", "申论", "面试", "gongkao"]):
        return "gongkao"
    if any(k in q for k in ["期末", "考试", "复习", "exam", "冲刺"]):
        return "exam-review"
    if any(k in q for k in ["项目", "project", "架构", "进度", "复盘"]):
        return "project"
    if any(k in q for k in ["章节", "课程", "学习笔记", "chapter"]):
        return "chapter-notes"
    return "research-note"
