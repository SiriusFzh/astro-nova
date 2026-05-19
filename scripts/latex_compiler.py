"""
astro-nova / scripts / latex_compiler.py
LaTeX 编译工具 — 使用 xelatex 编译 .tex 文件

依赖: xelatex (MiKTeX)

用法:
    python latex_compiler.py compile note.tex
    python latex_compiler.py clean note.tex
"""

import argparse
import os
import subprocess
import sys


def compile_tex(tex_path: str, runs: int = 2) -> bool:
    """用 xelatex 编译 .tex 文件，返回是否成功。"""
    if not os.path.exists(tex_path):
        print(f"文件不存在: {tex_path}", file=sys.stderr)
        return False

    base = os.path.splitext(tex_path)[0]
    dir_name = os.path.dirname(tex_path) or "."

    print(f"编译: {tex_path}")
    for i in range(runs):
        print(f"  第 {i+1}/{runs} 遍 xelatex...")
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-output-directory", dir_name, tex_path],
            capture_output=True, text=True, cwd=dir_name
        )
        if result.returncode != 0:
            # 收集关键错误
            errors = [l for l in result.stderr.split("\n") if "Error" in l or "error" in l.lower()]
            if errors:
                for e in errors[:5]:
                    print(f"  ERROR: {e}", file=sys.stderr)
            # 检查 .log 文件
            log_path = base + ".log"
            if os.path.exists(log_path):
                with open(log_path) as f:
                    for line in f:
                        if "Error" in line:
                            print(f"  LOG: {line.strip()}", file=sys.stderr)

    pdf_path = base + ".pdf"
    if os.path.exists(pdf_path):
        print(f"成功: {pdf_path}")
        return True
    else:
        print("编译失败", file=sys.stderr)
        return False


def clean_aux(tex_path: str):
    """删除 LaTeX 辅助文件。"""
    base = os.path.splitext(tex_path)[0]
    exts = [".aux", ".log", ".out", ".toc", ".nav", ".snm", ".bbl", ".blg"]
    for ext in exts:
        path = base + ext
        if os.path.exists(path):
            os.remove(path)
            print(f"删除: {path}")
    print("清理完成")


def main():
    parser = argparse.ArgumentParser(description="LaTeX 编译工具 (xelatex)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_c = sub.add_parser("compile", help="编译 .tex → .pdf")
    p_c.add_argument("tex_path", help=".tex 文件路径")
    p_c.add_argument("--runs", type=int, default=2, help="xelatex 编译遍数")

    p_cl = sub.add_parser("clean", help="清理辅助文件")
    p_cl.add_argument("tex_path", help=".tex 文件路径")

    args = parser.parse_args()

    if args.command == "compile":
        compile_tex(args.tex_path, args.runs)
    elif args.command == "clean":
        clean_aux(args.tex_path)


if __name__ == "__main__":
    main()
