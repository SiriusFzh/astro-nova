---
name: astro-reader
description: 深入阅读天文学论文，生成结构化精读笔记 (Markdown)
---
# astro-reader: 天文学论文精读

深入阅读一篇天文学论文，生成带原文对照的结构化 Markdown 精读笔记。

## 触发方式

用户说以下任意内容时触发：
- "精读这篇论文" / "读一下这篇"
- "帮我分析这篇文章"
- "read paper [arxiv_id]"
- "总结这篇论文的核心内容"
- 从 astro-search 选择论文后

## 输入

- **arXiv ID**: 如 `2301.00001`
- **PDF 路径**: 本地 PDF 文件路径
- **PDF URL**: 论文 PDF 链接

## 工作流

1. 获取论文文本：
   - 有 arXiv ID: 先用 `arxiv_search.py fetch` 获取元数据，再用 `arxiv_download.py fetch-text` 提取文本
   - 有 PDF 路径: 直接用 `arxiv_download.py extract` 提取文本
2. 按精读框架分析论文
3. 生成结构化 Markdown 笔记
4. 询问用户是否需要：
   - 导出为 NovaForge LaTeX 笔记（调用 novaforge 技能）
   - 生成图表（调用 astro-figure 技能）
   - 生成 PPT（调用 astro-ppt 技能）

## 脚本用法

```bash
# 获取元数据
python scripts/arxiv_search.py fetch 2301.00001

# 下载并提取全文
python scripts/arxiv_download.py fetch-text 2301.00001 --output ./papers

# 从本地 PDF 提取
python scripts/arxiv_download.py extract ./papers/2301_00001.pdf
```

## 精读框架

精读笔记按 7 个维度组织，详见 `references/reading-framework.md`：

1. 文献卡片
2. 研究背景
3. 方法/技术路线
4. 核心结果
5. 创新点
6. 局限性
7. 个人思考

## Markdown 输出格式

```markdown
# 论文标题

**文献卡片**
- arXiv: 2301.00001
- 作者: ...
- 年份: 2023
- 分类: astro-ph.HE

## 一、研究背景
...

## 二、方法
...

## 三、核心结果
...

## 四、创新点
...

## 五、局限性
...

## 六、个人思考
...
```
