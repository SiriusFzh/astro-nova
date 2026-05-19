---
name: astro-writing
description: 按 ApJ/MNRAS/A&A 标准格式撰写天文学论文各章节
---
# astro-writing: 天文学论文写作

按照天体物理学期刊标准格式撰写论文各章节。

## 触发方式

用户说以下任意内容时触发：
- "写论文" / "撰写论文"
- "写引言 / 方法 / 结果 / 讨论"
- "帮我写成 ApJ / MNRAS / A&A 格式"
- "write paper / write introduction"

## 支持的期刊

| 期刊 | 文档类 | 引用格式 |
|------|--------|---------|
| ApJ / AJ / ApJL | `aastex701.cls` | author-year |
| MNRAS | `mnras.cls` | author-year |
| A&A | `aa.cls` | author-year |
| Nature Astronomy | `sn-jnl.cls` | 数值引用 |

## 支持写作的章节

- **摘要**: 按各期刊字数限制
- **引言**: 背景 → gap → 本文目标
- **方法**: 观测/实验/理论方法
- **结果**: 主要发现 + 图表引用
- **讨论**: 解释 → 对比 → 展望
- **结论**: 总结 + 未来工作

## 工作流

1. 用户指定期刊格式
2. AI 按对应期刊的写作规范生成 .tex 文件
3. 用户可要求修改/完善特定章节
4. 可选：编译 PDF 检查格式

## 写作规范

- 字数限制
- 章节结构要求
- 引用格式
- 图表编号规则

## 参考

- 期刊样式: `references/journal-styles/*.md`
- 章节骨架: `references/section-skeleton/*.tex`
- 示例论文: `references/sample-paper/apj-sample.tex`
