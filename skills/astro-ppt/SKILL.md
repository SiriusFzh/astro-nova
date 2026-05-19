---
name: astro-ppt
description: 将论文内容转换为学术汇报 PPT（3种风格 × 3种输出格式）
---
# astro-ppt: 学术汇报 PPT 生成

从论文（arXiv ID / PDF / 精读笔记）一键生成学术汇报幻灯片，支持 3 种汇报风格和 3 种输出格式。

## 触发方式

- "生成 PPT" / "做 slides"
- "准备 journal club 汇报" / "做个汇报 PPT"
- "make a presentation for this paper"
- "生成开题报告 / 答辩 PPT"

## 工作流

```
Step 1: 输入 → 用户提供论文 (arXiv ID / PDF 路径 / 精读笔记 Markdown)
Step 2: 选风格 → 课题汇报 | 国际会议 | 答辩/开题
Step 3: 选格式 → Marp | Pandoc | Reveal.js
Step 4: 生成 → AI 按模板填充内容，含图表占位符
Step 5: 输出 → 用户本地用 Marp/Pandoc 转为 PPTX/PDF
```

## 三种风格

### 课题汇报 (10-15页) — 默认
课题组会、Journal Club、读书报告。中文，详细，含"个人思考"章节。
```
封面 → 目录 → 研究背景(2页) → 方法(2页) → 结果(3-4页) → 讨论 → 结论 → 我的思考 → 参考文献
```

### 国际会议 (8-10页)
AAS/IAU/COSPAR 等国际会议。English, concise, figure-driven.
```
Title → Motivation → Method → Results(3页) → Discussion → Summary → Backup
```

### 答辩/开题 (15-20页)
硕士答辩、博士开题、基金申请。中英混合，含创新点列条。
```
封面 → 框架 → 背景(3页) → 方法(3页) → 结果(5页) → 讨论 → 结论与创新点 → 展望 → Q&A → 备份页
```

## 三种输出格式

| 格式 | 转换命令 | 适用场景 |
|------|---------|---------|
| **Marp** | `npx @marp-team/marp-cli slide.md --pptx` | Windows + VS Code 生态 |
| **Pandoc** | `pandoc slide.md -o slide.pptx` | 通用，需要 LaTeX |
| **Reveal.js** | 浏览器直接打开 slide.html | 网页分享、在线汇报 |

## 配色偏好记忆

astro-ppt 会记录用户的 PPT 配色偏好（模仿 video-podcast-maker 的 user_prefs 机制）：

- 主色 / 强调色 / 背景色
- 字体选择
- 是否显示页码
- 默认输出格式

首次使用使用上述默认配色，之后自动沿用用户偏好。

## 参考

- 幻灯片结构模板: `references/slide-structure.md`
- 每页详细布局: 每个风格在 slide-structure.md 中有完整版式
