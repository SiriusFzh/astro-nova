# AASTeX 使用指南 (ApJ / AJ / ApJL)

## 文档类

```latex
\documentclass[aapm, twocolumn]{aastex701}
```

### 可选选项
- `aapm`: ApJ 格式 (默认)
- `aj`: AJ 格式
- `apj`: ApJ 格式
- `apjl`: ApJL 格式
- `twocolumn`: 双栏 (默认)
- `onecolumn`: 单栏
- `manuscript`: 手稿模式 (行号 + 倍行距)

## 参考文献

```latex
\bibliographystyle{aasjournal}
\bibliography{refs}
```

AASTeX 内建 bib 管理，无需额外 .bst 文件。引用格式为 author-year。

## 图表

```latex
\begin{figure}
  \includegraphics[width=\columnwidth]{fig1.pdf}
  \caption{图注。}
  \label{fig:1}
\end{figure}
```

- 宽度: `\columnwidth` (单栏) 或 `\textwidth` (跨栏)
- 格式: PDF (矢量) 或 EPS

## 表格

```latex
\begin{deluxetable}{lccr}
  \tablecaption{标题\label{tab:1}}
  \tablehead{\colhead{Col1} & \colhead{Col2} & \colhead{Col3}}
  \startdata
  a & 1 & 2 \\
  b & 3 & 4 \\
  \enddata
\end{deluxetable}
```

## 数学

AASTeX 自动加载 amsmath。常用命令：
- `\ion{元素}{电离态}`: 如 `\ion{Fe}{2}` → Fe II
- `\arcsec`, `\arcmin`: 角秒/角分
- `\micron`: 微米

## 常见注意事项

1. 参考文献必须使用 `\bibliography{}`，不要手动列出
2. 图表必须按出现顺序编号
3. 摘要不超过 250 词
4. 关键词: 3-6 个，用 `\keywords{}` 命令
5. 致谢使用 `\acknowledgments` 环境
