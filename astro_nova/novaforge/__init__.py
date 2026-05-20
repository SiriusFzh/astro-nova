"""NovaForge — 通用知识笔记模板引擎

作为 astro-nova 的内置模块，嵌入完整的 NovaForge 项目。
提供:
  - 从 NovaForge 仓库读取 LaTeX/Markdown/Typst 模板
  - 按模式（科研笔记/章节笔记/期末复习/考研/考公/项目）填充内容
  - 编译 LaTeX → PDF
  - 自动存储到 notes/ 目录
  - 输出文件管理和 PDF 预览支持

用法:
  from astro_nova.novaforge import NovaForgeEngine
  engine = NovaForgeEngine()
  result = engine.generate("research-note", title="...", content={...})
  # → {"tex": "...", "md": "...", "pdf": "...", "files": {...}}

模板来源（优先级）:
  1. 本地 astro_nova/novaforge/templates/（开发模式）
  2. ~/.astro-nova/novaforge-templates/（已缓存的下载）
  3. https://github.com/SiriusFzh/NovaForge（运行时下载）
"""

import os
import re
import json
import shutil
import subprocess
from datetime import date
from typing import Optional
from pathlib import Path

from astro_nova.utils.logger import logger
from astro_nova.utils.paths import get_data_dir, get_app_root

# ── 路径 ──
MODULE_DIR = Path(__file__).parent
TEMPLATES_DIR = MODULE_DIR / "templates"

# 模板缓存目录（在 data/ 下）
TEMPLATE_CACHE = Path(get_data_dir("novaforge-templates"))

# NovaForge GitHub 仓库 raw 地址
NOVAFORGE_RAW = "https://raw.githubusercontent.com/SiriusFzh/NovaForge/main"

# 需要从 NovaForge 获取的模板文件
NOVAFORGE_TEMPLATES = {
    "latex": ["preamble.tex", "template.tex"],
    "markdown": ["chapter-notes.md", "exam-review.md", "project-summary.md", "research-note.md"],
}


# ── 可用模式 ──
MODES = {
    "research-note": {
        "name": "科研笔记",
        "description": "文献/科研笔记 — 适用于论文阅读、课题研究",
        "latex_template": "research-note.latex",
        "md_template": "research-note.md",
        "sections": [
            "文献卡片", "研究背景与问题", "方法与技术路线",
            "核心结果与发现", "创新点与贡献", "局限性与未来工作",
            "个人思考与启发",
        ],
    },
    "chapter-notes": {
        "name": "章节笔记",
        "description": "7 步模块化结构 — 适用于系统学习新知识",
        "latex_template": "chapter-notes.latex",
        "md_template": "chapter-notes.md",
        "sections": [
            "概念引入", "核心原理", "方法技巧",
            "典型示例", "真题/实战", "巩固练习", "专题总结",
        ],
    },
    "exam-review": {
        "name": "期末复习",
        "description": "真题分类 + 留白练习 — 适用于备考冲刺",
        "latex_template": "exam-review.latex",
        "md_template": "exam-review.md",
    },
    "kaoyan": {
        "name": "考研模式",
        "description": "7 步 + 考研真题 — 考研专业课专用",
        "latex_template": "kaoyan.latex",
        "md_template": "exam-review.md",
    },
    "gongkao": {
        "name": "考公模式",
        "description": "行测/申论/面试考点分类",
        "latex_template": "gongkao.latex",
        "md_template": "exam-review.md",
    },
    "project": {
        "name": "项目模式",
        "description": "项目文档 — 架构/进度/决策/复盘",
        "latex_template": "project.latex",
        "md_template": "project-summary.md",
    },
}

def _get_default_output_dir() -> Path:
    """笔记输出目录统一在 data/notes/ 下"""
    return Path(get_data_dir("notes"))


class NovaForgeEngine:
    """NovaForge 笔记引擎 — 模板加载、内容填充、编译、输出管理"""

    def __init__(self):
        self.output_dir = _get_default_output_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._latex_templates: dict[str, str] = {}
        self._md_templates: dict[str, str] = {}
        self._preamble = ""
        self._full_template = ""
        self._load_templates()

    def update_output_dir(self, notes_dir: str | Path):
        """从外部配置更新输出目录（在 lifespan 中加载 config 后调用）"""
        self.output_dir = Path(notes_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── 模板加载 ──

    def _load_templates(self):
        """从嵌入的模板目录加载所有模板（PyInstaller 已打包）"""
        preamble_path = TEMPLATES_DIR / "latex" / "preamble.tex"
        template_path = TEMPLATES_DIR / "latex" / "template.tex"
        if preamble_path.exists():
            self._preamble = preamble_path.read_text(encoding="utf-8")
        if template_path.exists():
            self._full_template = template_path.read_text(encoding="utf-8")

        md_dir = TEMPLATES_DIR / "markdown"
        if md_dir.exists():
            for f in md_dir.iterdir():
                if f.suffix == ".md":
                    self._md_templates[f.stem] = f.read_text(encoding="utf-8")

        if not self._preamble:
            logger.error("NovaForge 模板加载失败: preamble.tex 未找到（打包问题）")

    def get_available_modes(self) -> list[dict]:
        """返回可用模式列表"""
        return [
            {"id": k, **v}
            for k, v in MODES.items()
        ]

    # ── LaTeX 模板合成 ──

    def _build_latex_research_note(self, data: dict) -> str:
        """生成科研笔记 LaTeX（当前最常用的模式）"""
        title = data.get("title", "科研笔记")
        title_short = data.get("title_short", title[:40])
        arxiv_id = data.get("arxiv_id", "")
        authors = data.get("authors", "")
        published = data.get("published", "")
        categories = data.get("categories", "")
        journal = data.get("journal", "arXiv")
        year = data.get("year", published[:4] if len(published) >= 4 else "")

        sections = data.get("sections", {})
        core = self._fmt_latex_para(sections.get("core", ""))
        methods = self._fmt_latex_para(sections.get("methods", ""))
        results = self._fmt_latex_para(sections.get("results", ""))
        innovation = self._fmt_latex_para(sections.get("innovation", ""))
        limitations = self._fmt_latex_para(sections.get("limitations", ""))
        thoughts = self._fmt_latex_para(sections.get("thoughts", ""))

        title_safe = self._escape_latex(title)

        return f"""%% NovaForge 科研笔记 — 由 AstroNova 自动生成
%% 编译: xelatex × 2
\\documentclass[10pt,a4paper]{{article}}

%% ── 加载 NovaForge Preamble ──
{self._preamble}

%% ── 补充颜色 ──
\\definecolor{{papercolor}}{{HTML}}{{4a148c}}

%% ── 页眉覆盖 ──
\\fancyhead[L]{{\\small\\color{{gray}}astro-nova · {title_safe}}}
\\fancyhead[R]{{\\small\\color{{gray}}{title_short}}}

%% ════════════════════════════════════════════
\\begin{{document}}

%% ── 封面标题 ──
\\begin{{center}}
  \\vspace{{1em}}
  {{\\Huge\\bfseries\\color{{titlecolor}} {title_safe}}} \\\\[0.3em]
  {{\\large\\color{{gray}} {authors}}} \\\\[0.3em]
  {{\\small\\color{{gray}} {arxiv_id} \\;|\\; {published} \\;|\\; {categories}}}
  \\vspace{{1em}}
\\end{{center}}

%% ── 文献卡片 ──
\\section{{一、文献卡片}}
\\noindent
\\begin{{tabular}}{{|p{{2.2em}}|p{{\\dimexpr\\textwidth-2.2em-2\\tabcolsep\\relax}}|}}
  \\hline
  \\multicolumn{{1}}{{|c|}}{{\\textbf{{\\small\\color{{papercolor}}标题}}}} & {{\\small {title_safe}}} \\\\
  \\hline
  \\multicolumn{{1}}{{|c|}}{{\\textbf{{\\small\\color{{papercolor}}作者}}}} & {{\\small {authors}}} \\\\
  \\hline
  \\multicolumn{{1}}{{|c|}}{{\\textbf{{\\small\\color{{papercolor}}刊源}}}} & {{\\small {journal}}} \\\\
  \\hline
  \\multicolumn{{1}}{{|c|}}{{\\textbf{{\\small\\color{{papercolor}}年份}}}} & {{\\small {year}}} \\\\
  \\hline
\\end{{tabular}}\\par

%% ── 核心内容 ──
\\section{{二、核心内容}}
{core}

\\section{{三、方法与技术路线}}
{methods}

\\section{{四、核心结果与发现}}
{results}

\\section{{五、创新点与贡献}}
{innovation}

\\section{{六、局限性与未来工作}}
{limitations}

\\section{{七、个人思考与启发}}
{thoughts}

\\vspace{{1em}}
\\noindent\\textcolor{{gray}}{{\\small 最后修订：{date.today().isoformat()} \\quad 生成工具：AstroNova + NovaForge}}

\\end{{document}}
"""

    def _escape_latex(self, text: str) -> str:
        """转义 LaTeX 特殊字符"""
        replacements = [
            ("\\", "\\textbackslash "),
            ("&", "\\&"), ("%", "\\%"), ("$", "\\$"),
            ("#", "\\#"), ("_", "\\_"), ("{", "\\{"), ("}", "\\}"),
            ("~", "\\textasciitilde "), ("^", "\\textasciicircum "),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    def _fmt_latex_para(self, text: str) -> str:
        """将纯文本段落转换为 NovaForge LaTeX 格式"""
        if not text or not text.strip():
            return "\\textcolor{gray}{（暂无内容）}\n\n"
        lines = text.strip().split("\n")
        out = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if s.startswith("$$") and s.endswith("$$"):
                core = s.strip("$")
                out.append(f"\\formula{{{core}}}\n\n")
            elif s.startswith("**") and s.endswith("**"):
                out.append(f"\\knowtitle{{{s.strip('*')}}}\n\n")
            elif s.startswith("> "):
                out.append(f"\\infobox{{{s[2:]}}}\n\n")
            elif s.startswith("! "):
                out.append(f"\\warning{{{s[2:]}}}\n\n")
            elif s.startswith("- ") or s.startswith("* "):
                bullet = s[2:]
                out.append(f"\\noindent $\\bullet$ {bullet}\\\\\n")
            else:
                out.append(f"\\noindent {s}\n\n")
        return "".join(out)

    # ── Markdown 模板 ──

    def _build_md_research_note(self, data: dict) -> str:
        """生成科研笔记 Markdown"""
        title = data.get("title", "科研笔记")
        arxiv_id = data.get("arxiv_id", "")
        authors = data.get("authors", "")
        published = data.get("published", "")
        categories = data.get("categories", "")
        sections = data.get("sections", {})

        md = f"""# {title}

> 科研笔记 · NovaForge 格式 · 由 AstroNova 自动生成

---

## 一、文献卡片

| 项目 | 内容 |
|------|------|
| **标题** | {title} |
| **作者** | {authors} |
| **arXiv ID** | {arxiv_id} |
| **刊源** | {data.get('journal', 'arXiv')} |
| **年份** | {published[:4] if len(published) >= 4 else ''} |
| **分类** | {categories} |

## 二、核心内容

{sections.get('core', '（暂无内容）')}

---

## 三、方法与技术路线

{sections.get('methods', '（暂无内容）')}

---

## 四、核心结果与发现

{sections.get('results', '（暂无内容）')}

---

## 五、创新点与贡献

{sections.get('innovation', '（暂无内容）')}

---

## 六、局限性与未来工作

{sections.get('limitations', '（暂无内容）')}

---

## 七、个人思考与启发

{sections.get('thoughts', '（暂无内容）')}

---

> 最后修订：{date.today().isoformat()}
> 生成工具：AstroNova + NovaForge
"""
        return md

    # ── 编译 ──

    def compile_latex(self, tex_path: str, runs: int = 2) -> Optional[str]:
        """用 xelatex 编译 .tex → .pdf

        Args:
            tex_path: .tex 文件的完整路径
            runs: 编译次数（默认 2 次以解析交叉引用）

        Returns:
            PDF 路径（成功）或 None（失败）
        """
        if not os.path.exists(tex_path):
            logger.error(f"编译失败：文件不存在 {tex_path}")
            return None

        tex_path = os.path.abspath(tex_path)
        base = os.path.splitext(tex_path)[0]
        dir_name = os.path.dirname(tex_path)
        pdf_path = base + ".pdf"

        # 检查已存在且更新的 PDF
        if os.path.exists(pdf_path):
            tex_mtime = os.path.getmtime(tex_path)
            pdf_mtime = os.path.getmtime(pdf_path)
            if pdf_mtime >= tex_mtime:
                logger.info(f"PDF 已是最新: {pdf_path}")
                return pdf_path

        xelatex = self._find_xelatex()
        if not xelatex:
            logger.error("未找到 xelatex，请安装 TeX Live 或 MiKTeX")
            return None

        for i in range(runs):
            try:
                result = subprocess.run(
                    [xelatex, "-interaction=nonstopmode",
                     "-output-directory", dir_name, tex_path],
                    capture_output=True, text=False,
                    cwd=dir_name, timeout=120,
                )
                if result.returncode != 0:
                    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
                    errors = [l for l in stdout.split("\n")
                              if "Error" in l or "!" in l[:2]]
                    if errors:
                        logger.warning(f"xelatex 第 {i+1} 次: {errors[-1][:200]}")
            except subprocess.TimeoutExpired:
                logger.warning(f"xelatex 第 {i+1} 次超时")
            except Exception as e:
                logger.warning(f"xelatex 第 {i+1} 次异常: {e}")

        if os.path.exists(pdf_path):
            logger.info(f"PDF 编译成功: {pdf_path}")
            return pdf_path

        logger.error(f"PDF 编译失败: {tex_path}")
        return None

    def _find_xelatex(self) -> Optional[str]:
        """查找系统 xelatex"""
        import shutil
        xelatex = shutil.which("xelatex")
        if xelatex:
            return xelatex
        # Windows 常见路径
        for prefix in [
            r"C:\texlive\bin\windows",
            r"C:\Program Files\MiKTeX\miktex\bin\x64",
            r"C:\Users\*\AppData\Local\Programs\MiKTeX\miktex\bin\x64",
        ]:
            expanded = os.path.expanduser(prefix)
            candidate = os.path.join(expanded, "xelatex.exe")
            if os.path.exists(candidate):
                return candidate
        return None

    # ── 输出管理 ──

    def generate(self, mode: str = "research-note", **data) -> dict:
        """生成笔记的完整工作流

        Args:
            mode: 模板模式（research-note / chapter-notes / exam-review / ...）
            data: 填充数据

        Returns:
            { "mode": ..., "title": ..., "tex_path": ..., "md_path": ...,
              "pdf_path": ..., "pdf_available": bool, "files": {...} }
        """
        mode = mode or "research-note"
        arxiv_id = data.get("arxiv_id", f"note-{date.today().isoformat()}")
        title = data.get("title", "未命名笔记")

        # 笔记存储目录
        note_dir = self.output_dir / arxiv_id
        note_dir.mkdir(parents=True, exist_ok=True)

        # 生成 LaTeX
        if mode == "research-note":
            latex = self._build_latex_research_note(data)
            md = self._build_md_research_note(data)
        else:
            # 其他模式 fallback 到 research-note
            latex = self._build_latex_research_note(data)
            md = self._build_md_research_note(data)

        # 写入文件
        tex_path = str(note_dir / f"{arxiv_id}.tex")
        md_path = str(note_dir / f"{arxiv_id}.md")
        self._write_text(tex_path, latex)
        self._write_text(md_path, md)

        # 编译 PDF
        pdf_path = self.compile_latex(tex_path)
        pdf_available = pdf_path is not None

        result = {
            "mode": mode,
            "title": title,
            "arxiv_id": arxiv_id,
            "latex": latex,
            "md": md,
            "tex_path": tex_path,
            "md_path": md_path,
            "pdf_path": pdf_path if pdf_available else "",
            "pdf_available": pdf_available,
            "files": {
                "tex": tex_path,
                "md": md_path,
            },
        }
        if pdf_available:
            result["files"]["pdf"] = pdf_path

        logger.info(f"NovaForge 笔记已保存: {tex_path}")
        return result

    def _write_text(self, path: str, content: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    # ── 笔记管理 ──

    def list_notes(self) -> list[dict]:
        """列出所有已生成的笔记"""
        notes = []
        if not self.output_dir.exists():
            return notes
        for entry in sorted(self.output_dir.iterdir(), key=os.path.getmtime, reverse=True):
            if entry.is_dir():
                tex = entry / f"{entry.name}.tex"
                md = entry / f"{entry.name}.md"
                pdf = entry / f"{entry.name}.pdf"
                notes.append({
                    "id": entry.name,
                    "title": self._extract_title(tex) if tex.exists() else entry.name,
                    "has_tex": tex.exists(),
                    "has_md": md.exists(),
                    "has_pdf": pdf.exists(),
                    "tex_path": str(tex) if tex.exists() else "",
                    "md_path": str(md) if md.exists() else "",
                    "pdf_path": str(pdf) if pdf.exists() else "",
                    "created_at": date.fromtimestamp(os.path.getmtime(entry)).isoformat(),
                })
        return notes

    def _extract_title(self, tex_path: str) -> str:
        """从 .tex 文件中提取标题"""
        try:
            with open(tex_path, "r", encoding="utf-8") as f:
                content = f.read()
            m = re.search(r"\\section\*?\{.*?\}|\\begin\{document\}.*?\n.*?\\textbf\{([^}]+)\}", content, re.DOTALL)
            # 简单的标题提取
            for line in content.split("\n"):
                if "Huge\\bfseries" in line:
                    m2 = re.search(r"\\color\{titlecolor\}\s*([^\\]+?)\s*(?:\\\\|\\end|$)", line)
                    if m2:
                        return m2.group(1).strip()
            m = re.search(r"\\section\{一、文献卡片\}", content)
            if m:
                prev = content[max(0, m.start()-200):m.start()]
                h = re.search(r"\\textbf\{标题\}\s*\&\s*\{\\small\s*([^}]+)\}", content)
                if h:
                    return h.group(1).strip()
        except Exception:
            pass
        return os.path.basename(tex_path).replace(".tex", "")

    def get_note(self, arxiv_id: str) -> Optional[dict]:
        """获取单篇笔记信息"""
        note_dir = self.output_dir / arxiv_id
        if not note_dir.exists():
            return None
        tex = note_dir / f"{arxiv_id}.tex"
        md = note_dir / f"{arxiv_id}.md"
        pdf = note_dir / f"{arxiv_id}.pdf"
        return {
            "id": arxiv_id,
            "title": self._extract_title(str(tex)) if tex.exists() else arxiv_id,
            "has_tex": tex.exists(),
            "has_md": md.exists(),
            "has_pdf": pdf.exists(),
            "tex_path": str(tex) if tex.exists() else "",
            "md_path": str(md) if md.exists() else "",
            "pdf_path": str(pdf) if pdf.exists() else "",
        }

    def delete_note(self, arxiv_id: str) -> bool:
        """删除笔记目录"""
        note_dir = self.output_dir / arxiv_id
        if note_dir.exists():
            shutil.rmtree(note_dir)
            return True
        return False

    def get_output_dir(self) -> str:
        return str(self.output_dir)


# 全局单例
engine = NovaForgeEngine()
