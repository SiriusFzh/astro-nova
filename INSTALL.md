# astro-nova 安装指南

## 前置依赖

### 1. Claude Code

astro-nova 基于 Claude Code SKILL.md 架构。你需要先安装 Claude Code：

```bash
npm install -g @anthropic-ai/claude-code
```

或从 [claude.ai/code](https://claude.ai/code) 下载桌面版。

### 2. Python 3.10+

```bash
python --version   # 确保 ≥ 3.10
```

### 3. LaTeX (可选 — 仅编译 .tex 文件时需要)

安装 MiKTeX (Windows) 或 TeX Live (Linux/Mac)：

- **Windows**: https://miktex.org/download
- **Mac**: `brew install --cask mactex`
- **Linux**: `sudo apt install texlive-xetex texlive-publishers`

确保 `xelatex` 可用：

```bash
xelatex --version
```

---

## 安装 astro-nova

### 方式一：完整安装（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/SiriusFzh/astro-nova.git
cd astro-nova

# 2. 安装 Python 依赖
pip install -r requirements.txt
```

### 方式二：仅安装单个技能

每个技能目录是自包含的，复制对应 `skills/<skill-name>/` 目录到 Claude Code 的 skills 路径即可。

---

## 验证安装

### 验证 Python 脚本

```bash
# 测试 ArXiv 搜索
python scripts/arxiv_search.py search "neutron star mergers" --max 3

# 测试 LaTeX 编译（需要 xelatex）
python scripts/latex_compiler.py compile path/to/note.tex
```

### 验证 Claude Code 技能

在 Claude Code 会话中触发对应技能关键词即可使用。

---

## 各技能额外依赖

| 技能 | 额外依赖 |
|------|---------|
| astro-search | `arxiv` (已包含) |
| astro-reader | `pymupdf` (已包含) |
| novaforge | xelatex |
| astro-figure | `matplotlib`, `numpy`, `astropy` (已包含) |
| astro-writing | xelatex + 对应期刊模板 |
| astro-ppt | 无 |
| astro-digest | `arxiv` (已包含) |

---

## 文件组织规范

astro-nova 在用户工作目录下按以下结构组织产出文件：

```
<work_dir>/
├── astro-ph.GA/          # 按 ArXiv 分类
│   ├── 2301_00001v3/     # 按 arXiv ID
│   │   ├── note.tex
│   │   ├── note.md
│   │   └── figures/
│   └── ...
├── astro-ph.HE/
│   └── ...
└── digest/
    └── weekly-2026-W20.md
```

---

## 升级

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```
