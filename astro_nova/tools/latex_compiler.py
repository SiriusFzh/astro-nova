"""LaTeX 编译工具 — 封装现有 scripts/latex_compiler.py"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

try:
    from latex_compiler import compile_tex, clean_aux
except ImportError:
    compile_tex = None
    clean_aux = None


def compile_latex(tex_path: str, runs: int = 2) -> bool:
    """编译 .tex → .pdf"""
    if compile_tex is None:
        return False
    return compile_tex(tex_path, runs=runs)
