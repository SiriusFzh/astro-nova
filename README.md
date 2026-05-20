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

<p align="center">
  <a href="#功能">功能</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#配置说明">配置说明</a> ·
  <a href="#从源码运行">从源码运行</a> ·
  <a href="#技术栈">技术栈</a> ·
  <a href="#常见问题">常见问题</a>
</p>

---

## 这是什么？

AstroNova 是一个 **AI Agent（智能体）** 桌面应用，专为天文学研究场景设计。它的核心理念和 Claude Code、OpenAI Codex 等 AI 编程助手一致——让大语言模型作为"大脑"，各种科研工具作为"手"，通过自然语言指挥 AI 完成科研任务。

**核心公式：LLM（大脑）+ Tools（手）= Agent**

| 对比 | Claude Code | AstroNova |
|------|-------------|-----------|
| 领域 | 软件开发 | 天文学研究 |
| LLM 工具 | 读文件、写代码、执行命令 | 搜论文、读论文、画图、写论文 |
| 目标 | 帮程序员写程序 | 帮天文人搞科研 |
| 工作方式 | 自然语言描述需求，AI 自动调用工具完成 | 同上 |

## 界面概览

左边侧边栏切换功能模块，右边主区域进行操作。支持深色模式和中英文界面切换。

| 区域 | 说明 |
|------|------|
| 侧边栏 | 12 个功能页面切换入口 |
| 标题栏 | 自定义暗色标题栏，支持窗口拖拽 |
| 主区域 | 当前功能的主要操作和展示区 |
| 状态栏 | 后端运行状态、模型连接状态 |

## 功能

### 对话
像用 ChatGPT 一样和 AI 聊天，但 AI 懂天文学，还能调用工具干活。你说"帮我查一下中子星合并的论文"，它就自动去 arXiv 搜索；你说"精读第一篇"，它就下载全文按 7 个维度分析。整个过程在同一个对话窗口完成，无需切换页面。

### 文献检索
搜索 arXiv 上的天文学论文，支持按天体物理子领域过滤：
- 星系天体物理 (astro-ph.GA)
- 高能天体物理 (astro-ph.HE)
- 宇宙学 (astro-ph.CO)
- 太阳与恒星物理 (astro-ph.SR)
- 地球与行星天体物理 (astro-ph.EP)
- 天体仪器与方法 (astro-ph.IM)

支持关键词搜索和 arXiv ID 精确查找，结果包含标题、作者、摘要、分类等信息。

### 论文精读
输入 arXiv ID，AI 自动获取论文全文，按 7 个维度分析：
1. **文献卡片** — 标题、作者、期刊、分类等基本信息
2. **研究背景** — 论文要解决的科知识题
3. **方法与技术路线** — 使用的研究手段和数据分析方法
4. **核心结果** — 最重要的定量/定性发现
5. **创新点** — 相比前人工作的进步
6. **局限性** — 方法的不足和未解决的问题
7. **个人思考** — 对自身研究的启发

全文获取采用四级策略：首选 arXiv 官方源，失败则尝试 PDF 直链、HTML5 页面，最后至少返回摘要，确保流程不中断。

### 笔记生成 (NovaForge)
基于论文精读结果，一键生成格式化科研笔记。支持两种输出格式：
- **LaTeX** — 可直接编译为 PDF，适合学术存档
- **Markdown** — 适合在笔记软件中进一步编辑

内置 NovaForge 模板引擎，提供多种模板：
- 科研笔记
- 章节笔记
- 期末复习
- 考研
- 考公
- 项目文档

如果本地安装了 LaTeX 编译工具，可以直接生成 PDF 文件。

### 科研制图
描述你的数据格式和想要的图，AI 生成可直接运行的 matplotlib 绘图代码。支持 7 种图表类型：

| 类型 | 说明 |
|------|------|
| 光谱图 | 强度-波长曲线 |
| 光变曲线 | 星等/流量-时间曲线 |
| 能谱分布 (SED) | 多波段能谱拟合图 |
| 等值线图 | 二维数据等值线 |
| 直方图 | 数据分布统计 |
| 散点图 | 双变量相关性 |
| 多面板组合图 | 多图拼接 |

生成的代码适配 ApJ、MNRAS、A&A 三种天文期刊的排版规范，输出为 PDF 矢量格式。

### 论文写作
按 ApJ、MNRAS、A&A 三种主流天文期刊的格式标准，辅助撰写论文章节。支持六种章节类型：摘要、引言、方法、结果、讨论、结论。用户提供上下文信息后，AI 生成符合期刊格式的 LaTeX 代码，只输出章节内容，方便直接粘贴到论文模板中。

### PPT 生成
根据论文精读结果或 arXiv ID，自动生成学术汇报幻灯片。支持三种汇报风格：

| 风格 | 语言 | 页数 | 适用场景 |
|------|------|------|----------|
| 课题汇报 | 中文 | 10-15 页 | 组会/课题组汇报 |
| 国际会议 | 英文 | 8-10 页 | 学术会议报告 |
| 答辩开题 | 中英混合 | 15-20 页 | 毕业答辩/开题报告 |

输出格式支持三种：Marp Markdown（VS Code 预览导出）、Pandoc Markdown（转为 PPTX）、Reveal.js HTML（网页播放）。

### 每日论文速报 (Digest)
自动爬取 arXiv 所有天文学子分类的最新论文（每日更新），去重后用 AI 生成中文摘要。每天一份论文日报，按分类分组，每篇论文包含一句话总结、研究动机、方法、结果和结论。方便快速浏览，找出感兴趣的论文深入阅读。

### 知识库
内置天文学基础知识，涵盖天体测量、天体力学、恒星物理、宇宙学、电磁学、电动力学、观测方法等模块。采用 BM25 全文检索算法，完全离线可用，无需联网。

### 插件与技能
**插件系统**：写 Python 脚本就可以注册新工具，供 AI 调用。支持热加载和卸载，无需重启应用。

**技能系统**：通过 SKILL.md 文件定义 AI 行为模式。用户触发特定关键词时，软件加载对应的技能提示词，改变 AI 的行为方式。预置 7 个技能：文献搜索、论文精读、科研制图、论文写作、PPT 生成、论文速报、笔记模板。

## 安装要求

| 组件 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 64位 |
| 运行内存 | 至少 4GB（推荐 8GB+） |
| 硬盘空间 | 至少 500MB |
| 网络 | 需要连接互联网（调用 AI 模型和 arXiv） |
| WebView2 | Windows 10 自带，Windows 8 需手动安装 |

## 快速开始

```bash
# 1. 下载安装包
# 从 Releases 页面下载 AstroNova_x.x.x_x64-setup.exe，双击安装

# 2. 打开软件
# 首次启动会提示你配置 AI 模型

# 3. 配置模型
# 进入设置 → 模型配置，添加你的 AI 模型 API Key
# 支持：OpenAI、Anthropic Claude、DeepSeek、Ollama（本地模型）

# 4. 开始使用
# 搜论文 → 精读 → 生成笔记 → 写论文 → 做PPT
```

## 配置说明

### AI 模型配置
支持同时配置多个模型服务商，每个模型可以指定负责不同的任务类型：

| 任务类型 | 说明 |
|----------|------|
| chat | 日常对话和通用任务 |
| search | 文献搜索 |
| read | 论文精读 |
| write | 论文写作 |
| code | 代码生成（制图等） |

例如可以让 GPT-4o 负责搜索和对话，Claude 负责论文写作，DeepSeek 负责代码生成。

### 代理设置
软件自动检测系统代理设置。如需手动配置，在 `config.json` 中设置：
```json
{
  "proxy": "http://127.0.0.1:7890"
}
```

arXiv 的访问默认绕过代理（国内可直接访问）。

### 数据存储
- 配置文件：`%APPDATA%/AstroNova/config.json`（安装版）或项目根目录 `data/`（开发版）
- 论文数据、对话记录、笔记等：SQLite 数据库
- 下载的 PDF、生成的笔记和代码：按类型分目录存储
- 卸载重装不会丢失数据

## 从源码运行

### 环境要求
- Python 3.10+
- Node.js 20+
- Rust（安装 Tauri 2 构建工具）

### 步骤

```bash
# 克隆仓库
git clone https://github.com/SiriusFzh/astro-nova.git
cd astro-nova

# Python 依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..

# 安装项目依赖并启动开发模式
npm install
npm run tauri:dev
```

### 构建安装包

```bash
npm run build
# 产物在 src-tauri/target/release/bundle/nsis/
```

构建过程会：
1. 使用 PyInstaller 打包 Python 后端为独立 exe
2. 使用 Vite 构建 Vue 3 前端
3. 使用 Tauri 2 将前后端打包为 Windows 安装包

## 技术栈

| 层 | 技术 | 作用 |
|----|------|------|
| 桌面框架 | Tauri 2 (Rust) | 创建原生窗口、系统托盘、管理后端进程 |
| 后端 | Python / FastAPI | 提供 API 接口，处理所有业务逻辑 |
| 前端 | Vue 3 + Element Plus | 用户界面显示和交互 |
| 数据库 | SQLite | 存储配置、论文、对话记录等 |
| AI 接入 | OpenAI / Anthropic / DeepSeek | 接入大语言模型作为 Agent 大脑 |
| 文档解析 | PyMuPDF / BeautifulSoup | PDF 文本提取和 HTML 页面解析 |
| 笔记引擎 | NovaForge（内嵌） | 从模板生成 LaTeX/Markdown 笔记 |
| 打包 | PyInstaller + Tauri | 后端打包为 exe，桌面打包为安装包 |

## 项目结构

```
astro-nova/
├── astro_nova/              # Python 后端
│   ├── main.py              # FastAPI 应用入口
│   ├── api/                 # API 路由
│   ├── providers/           # LLM 供应商（OpenAI/Anthropic/DeepSeek/Ollama）
│   ├── tools/               # 科研工具（搜索/精读/笔记/制图/写作/PPT/Digest）
│   ├── novaforge/           # 笔记模板引擎（内嵌模块）
│   ├── plugins/             # 插件系统（热加载）
│   ├── skills/              # 技能系统
│   ├── knowledge/           # 知识库 RAG（BM25 检索）
│   └── database/            # 数据库模型和操作
├── frontend/                # Vue 3 前端
│   └── src/views/           # 12 个功能页面
├── src-tauri/               # Tauri 桌面壳（Rust）
│   └── src/lib.rs           # 后端进程管理 + 系统托盘
├── skills/                  # 预置技能文件（SKILL.md）
├── references/              # LaTeX / matplotlib 样式模板
└── scripts/                 # 构建和辅助脚本
```

## 关于 AI Agent 架构

AstroNova 的核心是一个 **ToolRegistry（工具注册中心）**。所有科研工具（搜索、精读、笔记、制图、写作、PPT 生成等）都注册到这个地方。AI 模型在对话时能看到这些工具的用途和参数，当需要时自主发出调用指令。系统收到指令后执行对应的工具函数，把结果返回给 AI，AI 再根据结果决定下一步。

工具调用最多可循环 12 轮，实现复杂的多步工作流。例如：
1. 用户："帮我查一下引力波对应的电磁对应体最新进展"
2. AI 调用搜索工具 → 返回论文列表
3. AI 调用精读工具分析第一篇 → 返回分析结果
4. AI 整理结果并回复用户

这个过程和 Claude Code 中大模型调用 read、edit、bash 等工具的流程一致，只是 AstroNova 的工具面向的是天文学科研场景。

## 常见问题

**Q：支持 macOS 吗？**
当前仅支持 Windows 10/11。macOS 版本计划在未来推出。

**Q：需要自己的 API Key 吗？**
需要。你需要拥有 OpenAI、Anthropic 或 DeepSeek 的 API Key。软件不内置任何 API Key。

**Q：可以离线使用吗？**
知识库功能可以离线使用（BM25 全文检索）。但 AI 对话、文献搜索等功能需要联网。

**Q：数据存在哪里？会不会丢失？**
安装版数据在 `%APPDATA%/AstroNova/data/`，卸载重装不会丢失。开发版在项目根目录的 `data/` 文件夹。

**Q：遇到问题怎么办？**
- 检查后端日志（`%APPDATA%/AstroNova/logs/` 或项目 `data/logs/`）
- 检查是否是网络问题（代理设置是否正确）
- 在 GitHub 提 Issue

## 参考项目

AstroNova 在设计和实现上参考了以下项目：

- **Claude Code**（Anthropic）— AI 编程 Agent，Agent 架构设计的主要参考
- **OpenAI Codex** — AI 编程助手，LLM + 工具调用的 Agent 模式
- **NovaForge** — 笔记模板引擎，作为内嵌模块使用
- **daily-arXiv-ai-enhanced** — 每日论文速报功能的流程设计参考

## 许可证

MIT
