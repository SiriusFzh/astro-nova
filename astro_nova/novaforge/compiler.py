"""NovaForge LaTeX 编译器 — 封装直接编译和基于脚本编译"""

import os
import subprocess
from typing import Optional
from pathlib import Path

from astro_nova.utils.logger import logger


def find_xelatex() -> Optional[str]:
    """查找系统 xelatex 可执行文件"""
    import shutil
    xelatex = shutil.which("xelatex")
    if xelatex:
        return xelatex
    # Windows 常见路径
    common = [
        r"C:\texlive\bin\windows\xelatex.exe",
        r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe",
    ]
    for p in common:
        if os.path.exists(p):
            return p
    # 用户目录
    user_local = os.path.expanduser(r"~\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe")
    if os.path.exists(user_local):
        return user_local
    return None


def compile_tex_to_pdf(tex_path: str, runs: int = 2, clean_aux: bool = True) -> Optional[str]:
    """编译 .tex → .pdf

    Args:
        tex_path: .tex 文件路径
        runs: xelatex 编译次数（默认 2 次）
        clean_aux: 是否清理辅助文件

    Returns:
        PDF 路径（成功）或 None（失败）
    """
    if not os.path.exists(tex_path):
        logger.error(f"文件不存在: {tex_path}")
        return None

    tex_path = os.path.abspath(tex_path)
    base = os.path.splitext(tex_path)[0]
    dir_name = os.path.dirname(tex_path)
    pdf_path = base + ".pdf"

    xelatex = find_xelatex()
    if not xelatex:
        logger.error("未找到 xelatex，请安装 TeX Live 或 MiKTeX")
        return None

    for i in range(runs):
        try:
            result = subprocess.run(
                [xelatex, "-interaction=nonstopmode",
                 "-halt-on-error",
                 "-output-directory", dir_name, tex_path],
                capture_output=True, text=False,  # binary mode to avoid GBK decode errors
                cwd=dir_name, timeout=120,
            )
            if result.returncode != 0:
                stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
                errors = [l for l in stdout.split("\n") if l.startswith("!")]
                if errors:
                    logger.warning(f"编译第 {i+1} 次: {errors[-1][:200]}")
        except subprocess.TimeoutExpired:
            logger.warning(f"xelatex 第 {i+1} 次超时 (120s)")
        except Exception as e:
            logger.warning(f"xelatex 第 {i+1} 次异常: {e}")

    if os.path.exists(pdf_path):
        logger.info(f"PDF 生成: {pdf_path}")
        # 清理辅助文件
        if clean_aux:
            for ext in [".aux", ".log", ".out", ".toc", ".lof", ".lot"]:
                aux = base + ext
                if os.path.exists(aux):
                    try:
                        os.remove(aux)
                    except OSError:
                        pass
        return pdf_path

    logger.error(f"PDF 生成失败: {tex_path}")
    return None


def get_pdf_path(tex_path: str) -> Optional[str]:
    """获取对应的 PDF 路径（不编译，仅返回路径）"""
    pdf = os.path.splitext(tex_path)[0] + ".pdf"
    return pdf if os.path.exists(pdf) else None
