---
name: novaforge
description: 将论文精读内容输出为 NovaForge 格式科研笔记 (LaTeX + Markdown)
---
# novaforge: NovaForge 科研笔记生成

将论文精读内容转换为 NovaForge 科研模式的结构化笔记，输出为可编译的 LaTeX 文件和 Markdown 版本。

## 触发方式

用户说以下任意内容时触发：
- "整理笔记" / "生成笔记" / "导出笔记"
- "用 NovaForge 格式输出"
- "生成 LaTeX 笔记"
- 从 astro-reader 输出后调用

## 输出规范

### LaTeX 六节结构

```latex
\input{references/preamble.tex}

\section{一、研究背景与问题}
\paperinfo{论文标题}{作者}{刊源/arXiv}{年份}

\section{二、方法与技术路线}

\section{三、核心结果与发现}

\section{四、创新点与贡献}

\section{五、局限性与未来工作}

\section{六、与自身研究的关联}
%% 此部分不可缺省
```

### NovaForge 命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `\paperinfo{标题}{作者}{刊源}{年份}` | 文献卡片 | 4 列表格 |
| `\knowtitle{标题}` | 知识标题栏 | 蓝灰背景深蓝粗体 |
| `\lithead{标题}` | 科研小标题 | 蓝色粗体 |
| `\formula{内容}` | 公式框 | 带边框居中 |
| `\key{文本}` | 强调 | 橙红色 |
| `\infobox{内容}` | 提示框 | 蓝色箭头开头 |
| `\warning{内容}` | 警告 | 橙色叹号 |

## 工作流

1. 输入来源：
   - astro-reader 生成的 Markdown 精读笔记（优先）
   - 用户直接提供的内容
2. 按六节结构组织内容
3. 使用适当的 NovaForge 命令进行排版
4. 输出两个文件：
   - `<arxiv-id>.tex` — 可编译的 LaTeX 文件
   - `<arxiv-id>.md` — Markdown 版本
5. 可选：调用 latex_compiler.py 编译 PDF

## 脚本用法

```bash
# 编译 PDF
python scripts/latex_compiler.py compile note.tex --runs 2

# 清理辅助文件
python scripts/latex_compiler.py clean note.tex
```

## 产出文件组织

```
<work_dir>/<category>/
├── <arxiv-id>/
│   ├── note.tex
│   ├── note.md
│   └── figures/
└── ...
```

## 参考

- 导言区: `references/preamble.tex`
- 配色: `references/color-scheme.tex`
- 编译脚本: `scripts/latex_compiler.py`
