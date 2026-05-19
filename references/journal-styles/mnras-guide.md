# MNRAS 使用指南

## 文档类

```latex
\documentclass[useAMS, usenatbib]{mnras}
```

### 可选选项
- `useAMS`: 加载 AMS 数学
- `usenatbib`: 使用 natbib 引用
- `twocolumn`: 双栏
- `onecolumn`: 单栏 (封面文章)
- `astro`: 天体物理 (默认)
- `geophys`: 地球物理

## 参考文献

```latex
\bibliographystyle{mnras}
\bibliography{refs}
```

使用 natbib，author-year 格式。

## 图表

```latex
\begin{figure}
  \includegraphics[width=\columnwidth]{fig1.pdf}
  \caption{图注。}
  \label{fig:1}
\end{figure}
```

## 表格

使用标准 `table` 环境或 `deluxetable` (需加载 `deluxetable` 包)。

## 数学

amsmath 已预加载。常用命令：
- `\tensorsymbol`: 张量符号
- `\vector`: 矢量符号
- `\ion{元素}{电离态}`: 电离态标注

## 常见注意事项

1. 标题不超过 100 字符
2. 摘要不超过 300 词
3. 章节编号: 1, 1.1, 1.1.1
4. 图表注必须完整 (不依赖正文理解)
5. 数据可用性说明: 需包含 Data Availability 章节
6. 参考文献必须全部在正文中引用
