---
name: astro-figure
description: 生成符合 ApJ/MNRAS/A&A 标准的出版级科研图表（AI 生成 matplotlib 代码）
---
# astro-figure: 天文学科研制图

**核心原则**: AI 生成可运行的 Python/matplotlib 代码 → 用户本地运行 → 输出 PDF 矢量图。

不依赖 AI 生图能力（不使用 DALL-E/Midjourney），只靠代码保证数据严谨和可复现。

## 触发方式

用户说以下任意内容时触发：
- "画图" / "制图" / "生成图表"
- "把数据可视化成 [类型] 图"
- "生成光谱图 / 光变曲线 / SED / 等高线图"
- "plot this data"

## 支持的图表类型

| 类型 | 用途 | 模板 |
|------|------|------|
| 光谱图 | 展示谱线/能谱 | `spectrum.py` |
| 光变曲线 | 时序数据 | `lightcurve.py` |
| SED 拟合 | 多波段能谱分布 | `SED.py` |
| 等高线/置信区间 | 参数空间 | `contour.py` |
| 彩色星图/热力图 | 空间分布 | 动态生成 |
| 柱状图/直方图 | 统计分布 | 动态生成 |
| 多面板组合图 | 综合展示 | 动态生成 |

## 工作流

1. 用户提供数据（CSV/FITS/ASCII 文件路径或数据描述）
2. AI 分析数据格式，选择合适的图表类型
3. AI 生成完整可运行的 Python 脚本
4. 用户本地运行脚本 → 生成 PDF/SVG 矢量图
5. 脚本自动应用 `references/figure-styles.mplstyle` 样式

## 输出标准

- **字体**: Times New Roman / STIX (数学)
- **刻度**: 向内
- **颜色**: 语义化色板（色盲友好）
- **图注**: 清晰标注 a/b/c/d 面板
- **格式**: PDF（矢量，可编辑）
- **数据来源**: 必须标注

## matplotlib 样式

```python
import matplotlib.pyplot as plt
plt.style.use("references/figure-styles.mplstyle")
```

## 脚本模板

见 `references/plot-scripts/` 目录。

## 参考

- 样式文件: `references/figure-styles.mplstyle`
- 脚本: `references/plot-scripts/*.py`
