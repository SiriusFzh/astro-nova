# A&A 使用指南

## 文档类

```latex
\documentclass{aa}
```

### 可选选项
- `twocolumn`: 双栏 (默认)
- `onecolumn`: 单栏

## 参考文献

```latex
\bibliographystyle{aa}
\bibliography{refs}
```

A&A 使用 author-year 引用格式。

## 图表

```latex
\begin{figure}
  \includegraphics[width=\columnwidth]{fig1.pdf}
  \caption{图注。}
  \label{fig:1}
\end{figure}
```

## 表格

```latex
\begin{table}
  \caption{标题\label{tab:1}}
  \begin{tabular}{lcc}
  \hline
  Col1 & Col2 & Col3 \\
  \hline
  a & 1 & 2 \\
  b & 3 & 4 \\
  \hline
  \end{tabular}
\end{table}
```

## 特殊功能

- `\titlerunning{短标题}`: 页眉用短标题
- `\authorrunning{短作者}`: 页眉用短作者列表
- `\institute`: 机构信息
- 附录: `\appendix` 后接章节

## 常见注意事项

1. 标题中避免缩写
2. 摘要需包含: 背景、目标、方法、结果、结论
3. 关键词: 使用 `\keywords{}`，最多 6 个
4. 致谢使用 `\acknowledgements`
5. 附录图表编号: Fig. A.1, Table B.1
6. 彩色图表需注意印刷版灰度兼容性
