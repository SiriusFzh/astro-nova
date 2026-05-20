<p align="center">
  <img src="icon.png" alt="AstroNova" width="128">
</p>

<h1 align="center">AstroNova</h1>

<p align="center">
  <strong>AI Agent 驱动的天文学科研助手</strong>
  <br>
  像 Claude Code 帮程序员写代码一样，AstroNova 帮天文人搞科研。
  <br>
  从文献检索到论文发表，一个 Agent 搞定。
</p>

---

## 这是什么？

AstroNova 是一个 **AI Agent（智能体）** 桌面应用。它的设计思路和 Claude Code、OpenAI Codex 一样——让大语言模型作为"大脑"，各种科研工具作为"手"，通过自然语言指挥 AI 完成科研任务。

**核心模式：LLM（大脑）+ Tools（手）= Agent**

Claude Code 给 AI 提供了读文件、写代码、执行命令等工具来帮程序员写程序。AstroNova 给 AI 提供了搜论文、读论文、做笔记、画图、写论文等工具来帮天文人做科研。

## 功能

### 对话
像用 ChatGPT 一样和 AI 聊天，但 AI 懂天文学，还能动手干活——你说"帮我查一下中子星合并的论文"，它就自动去 arXiv 搜索。

### 文献检索
搜索 arXiv 上的天文学论文，支持按子领域过滤（星系物理、高能天体物理、宇宙学等）。

### 论文精读
输入 arXiv ID，AI 自动下载论文全文，按 7 个维度分析：背景、方法、结果、创新点、局限性、个人思考。

### 笔记生成 (NovaForge)
精读结果一键生成结构化笔记，输出 LaTeX 和 Markdown 格式，可编译为 PDF。支持科研笔记、章节笔记、考研等多种模板。

### 科研制图
描述你的数据和想要的图，AI 生成可直接运行的 matplotlib 绘图代码，输出 PDF 矢量图。

### 论文写作
按 ApJ、MNRAS、A&A 期刊格式撰写论文章节（摘要、引言、方法、结果、讨论、结论）。

### PPT 生成
从论文精读结果生成学术汇报幻灯片，支持课题汇报、国际会议、答辩三种风格。

### 每日论文速报 (Digest)
自动爬取 arXiv 天文学论文，去重后用 AI 生成中文摘要，每天一份论文日报。

### 知识库
内置天文学基础知识的全文检索（BM25 算法），离线可用。

### 插件与技能
插件：写 Python 脚本注册新工具，热加载无需重启。技能：SKILL.md 文件定义 AI 行为，触发词激活。

## 界面

左边侧边栏切换功能，右边主区域操作。自定义暗色标题栏，支持深色模式，中英文界面。

## 快速开始

```bash
# 1. 下载安装包
# 从 Releases 下载 AstroNova_x.x.x_x64-setup.exe，双击安装

# 2. 打开软件，去设置页添加 AI 模型
# 支持 OpenAI、Anthropic Claude、DeepSeek 等

# 3. 开始使用
# 搜论文 → 精读 → 生成笔记 → 写论文 → 做PPT
```

### 从源码运行

```bash
git clone https://github.com/SiriusFzh/astro-nova.git
cd astro-nova

# Python 依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..

# 启动开发模式
npm install
npm run tauri:dev
```

### 构建安装包

```bash
npm run build
# 产物在 src-tauri/target/release/bundle/nsis/
```

## 技术栈

| 层 | 技术 |
|----|------|
| 桌面框架 | Tauri 2 (Rust) |
| 后端 | Python / FastAPI |
| 前端 | Vue 3 + Element Plus |
| 数据库 | SQLite |
| AI 接入 | OpenAI / Anthropic / DeepSeek |
| 打包 | PyInstaller (后端) + Tauri (桌面) |

## 项目结构

```
astro-nova/
├── astro_nova/              # Python 后端
│   ├── main.py              # FastAPI 入口
│   ├── providers/           # LLM 供应商（OpenAI/Anthropic/DeepSeek）
│   ├── tools/               # 科研工具（搜索/精读/笔记/制图/写作/PPT/Digest）
│   ├── novaforge/           # 笔记模板引擎
│   ├── plugins/             # 插件系统
│   ├── skills/              # 技能系统
│   ├── knowledge/           # 知识库 RAG
│   ├── database/            # 数据库
│   └── api/                 # API 路由
├── frontend/                # Vue 3 前端
│   └── src/views/           # 12 个功能页面
├── src-tauri/               # Tauri 桌面壳 (Rust)
│   └── src/lib.rs           # 后端进程管理 + 系统托盘
├── skills/                  # 预置 SKILL.md
├── references/              # LaTeX / matplotlib 资源
└── scripts/                 # 构建脚本
```

## 关于 AI Agent

AstroNova 借鉴了 Claude Code、Codex 等 AI 编程助手的 Agent 架构。核心机制是 ToolRegistry（工具注册中心）——所有工具统一注册，AI 在对话中自主决定调用哪些工具、按什么顺序调用，实现端到端的科研工作流。

## 许可证

MIT
