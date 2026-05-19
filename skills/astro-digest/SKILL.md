---
name: astro-digest
description: 定时爬取 ArXiv 最新天文学论文，生成文献 Digest 汇总
---
# astro-digest: 每日/每周文献 Digest

按用户配置的研究方向，定时搜索 ArXiv 最新论文，用 LLM 筛选排序后生成摘要汇总。

## 触发方式

用户说以下任意内容时触发：
- "生成今天/本周的文献 digest"
- "daily digest" / "weekly digest"
- "看看最近有什么新论文"
- "帮我整理最近 [领域] 的新进展"

## 工作流

1. 按配置搜索 ArXiv 指定分类的最新论文（--sort submittedDate）
2. LLM 逐篇评估相关度 + 重要性
3. 过滤低相关度论文
4. 按相关度排序，生成摘要汇总
5. 输出 NovaForge 格式的 digest 笔记

## CLI 用法

```bash
# 手动触发 digest
python scripts/arxiv_search.py search "neutron star" --cat astro-ph.HE --days 3 --sort submittedDate --max 50
```

## 输出格式

```markdown
# ArXiv Digest: 2026-05-18

研究方向: 高能天体物理

## Top 5 推荐

### 1. [标题] (相关度: 9/10)
arXiv: 2301.xxxxx | astro-ph.HE
短摘要...

### 2. ...
```

## 配置

见 `references/digest-config.yaml`。

## 频率说明

- **daily**: 每天查看当天新提交
- **weekly**: 每周汇总一周论文
