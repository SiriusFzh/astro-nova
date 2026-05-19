# astro-nova — Claude Code 项目配置

## 项目类型
天文学全领域 AI 科研助手 — 7 个独立技能 (SKILL.md 架构)

## 核心命令

### 脚本调用
- `python scripts/arxiv_search.py search <query> [--cat] [--max] [--days]`
- `python scripts/arxiv_download.py fetch-text <arxiv_id>`
- `python scripts/latex_compiler.py compile <tex_path>`

### LaTeX 编译
```bash
python scripts/latex_compiler.py compile note.tex --runs 2
python scripts/latex_compiler.py clean note.tex
```

## 代码规范

### Python
- 类型注解 + dataclass
- argparse CLI (subparsers)
- 错误处理：文件存在性检查 + import 异常提示
- 日志：print (轻量)

### LaTeX
- 导言区使用 `references/preamble.tex`
- 科研模式命令: `\paperinfo`, `\knowtitle`, `\lithead`, `\formula`, `\key`

### matplotlib
- 样式: `plt.style.use("references/figure-styles.mplstyle")`
- 输出: PDF 矢量格式
- 字体: Times New Roman (或 STIX)

## 技能开发规范

每个技能包含:
```
skills/<skill-name>/
├── SKILL.md           # 技能定义 (必需)
└── references/        # 技能专属资源 (可选)
```

SKILL.md 格式遵循 Claude Code 官方规范。

## 领域知识
- 天文学全领域: astro-ph.*, physics.space-ph, physics.ins-det, gr-qc
- 期刊标准: ApJ (AASTeX), MNRAS (mnras.cls), A&A (aa.cls)
- 颜色系统: NovaForge 13 色调色板 (见 references/preamble.tex)

## GitHub 注意事项
- README 更新追加日志到顶部 (ISO 8601 时间戳)
- 较大更新创建 GitHub Releases
- 仓库: https://github.com/SiriusFzh/astro-nova
