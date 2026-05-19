---
name: astro-search
description: 搜索 ArXiv 天文学全领域论文，返回结构化元数据
---
# astro-search: 天文学文献检索

搜索 [ArXiv](https://arxiv.org) 上所有天文学相关分支的最新论文，返回结构化元数据列表。

## 触发方式

用户说以下任意内容时触发：
- "搜索论文" / "找文献" / "search papers"
- "帮我查一下关于 [主题] 的文献"
- "最近 [领域] 有什么新进展"
- "latest on [topic]"
- "找一下 [作者] 的论文"

## 搜索覆盖领域

- `astro-ph.*` — 天体物理全分支
- `gr-qc` — 广义相对论与引力波
- `physics.space-ph` — 空间物理
- `physics.ins-det` — 天文仪器与探测器
- `cs.AI` / `cs.LG` / `stat.ML` — AI/ML 在天文中的应用

## 工作流

1. 分析用户描述，提取关键词和限定条件（分类、时间范围）
2. 用 `astro-nova/scripts/arxiv_search.py` 搜索 ArXiv API
3. 对结果进行 LLM 相关度排序
4. 展示 Top 10-20 篇，每篇包含：
   - arXiv ID / 标题 / 作者 / 年份 / 分类
   - 摘要（前 200 词）
   - 相关度评分
5. 询问用户哪些论文需要进一步精读

## CLI 用法

```bash
# 搜索
python scripts/arxiv_search.py search "neutron star mergers" --max 20 --cat astro-ph.HE astro-ph.GA --days 30

# 按 ID 获取单篇
python scripts/arxiv_search.py fetch 2301.00001

# 列出所有天文学分类
python scripts/arxiv_search.py categories

# JSON 格式输出
python scripts/arxiv_search.py search "exoplanet atmosphere" --max 5 --json
```

## 输出格式

```
======================================
  #1 [相关度: 8.5/10]
  Title: 论文标题
  Authors: Author1, Author2, et al.
  arXiv: 2301.00001  |  2023-01-01  |  [astro-ph.HE, astro-ph.GA]
  PDF: https://arxiv.org/pdf/2301.00001.pdf
  ---
  摘要前300字符...
```

## 常用搜索模板

见 `references/search-queries.md`。

## 参考

- 脚本: `scripts/arxiv_search.py`
- 分类列表: 运行 `python scripts/arxiv_search.py categories`
