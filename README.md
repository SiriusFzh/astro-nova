# AstroNova 🔭

**AI 驱动的天文学全领域科研助手桌面客户端**

搜索 ArXiv → 精读论文 → 生成笔记 → 绘制图表 → 撰写论文 → 制作 PPT — 覆盖天文科研全流程。

---

## 截图

[待补充]

---

## 功能

| 功能 | 说明 |
|------|------|
| **多模型 AI 对话** | 同时配置多个 LLM，不同任务用不同模型 |
| **文献搜索** | 搜索 ArXiv 全领域天文学论文 |
| **论文精读** | 输入 arXiv ID 获取结构化学术笔记 |
| **NovaForge 笔记** | 输出 LaTeX 格式科研笔记 |
| **科研制图** | AI 生成 matplotlib 代码 |
| **论文写作** | 按 ApJ/MNRAS/A&A 标准格式撰写 |
| **PPT 生成** | 一键转为学术汇报幻灯片 |
| **插件系统** | 可安装第三方扩展 |
| **知识库 RAG** | 论文向量检索增强生成 |

## 支持的大模型

可同时配置多个 Provider，不同任务路由到不同模型：

- **OpenAI** (GPT-4o, GPT-4o-mini)
- **Anthropic Claude** (Sonnet, Haiku)
- **DeepSeek** (V3, R1)
- **Ollama** (本地运行的开源模型)
- **任何 OpenAI 兼容 API** (SiliconFlow, vLLM, 等)

## 快速开始

### 下载安装

从 [GitHub Releases](https://github.com/SiriusFzh/astro-nova/releases) 下载最新版安装包，双击安装即可。

### 源码运行

```bash
# 1. 克隆
git clone https://github.com/SiriusFzh/astro-nova.git
cd astro-nova

# 2. Python 依赖
pip install -r requirements.txt

# 3. 前端依赖
cd frontend && npm install && cd ..

# 4. 启动后端
python -m astro_nova

# 5. 新终端，启动前端
cd frontend && npm run dev
```

### 开发模式 (Electron)

```bash
npm install          # 安装 Electron 依赖
npm run dev          # 同时启动前端 + Electron
```

## 技术栈

- **后端**: Python 3.12+ / FastAPI / SQLAlchemy
- **前端**: Vue 3 / Element Plus / Vite
- **桌面**: Electron / electron-builder
- **数据库**: SQLite
- **LLM**: OpenAI 兼容 API + Anthropic Claude 直连

## 项目结构

```
astro-nova/
├── astro_nova/       # Python 后端 (FastAPI)
├── frontend/          # Vue 3 前端
├── electron/          # Electron 桌面客户端
├── scripts/           # 独立 Python 脚本
├── references/        # LaTeX / matplotlib 资源
├── skills/            # SKILL.md 技能
└── build/             # 打包配置
```

## 许可证

MIT License © 2026 一叶知秋 (SiriusFzh)
