# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 构建 — astro_nova 后端 → 单文件 EXE (onefile)"""
import os
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

block_cipher = None

a = Analysis(
    [os.path.join(ROOT, "astro_nova", "__main__.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, "astro_nova", "knowledge", "seed", "*.json"),
         os.path.join("astro_nova", "knowledge", "seed")),
        (os.path.join(ROOT, "skills"), "skills"),
        (os.path.join(ROOT, "references"), "references"),
        (os.path.join(ROOT, "astro_nova", "novaforge", "templates"),
         os.path.join("astro_nova", "novaforge", "templates")),
    ],
    hiddenimports=[
        "bs4",
        "arxiv",
        "arxiv.arxiv",
        "arxiv._arxiv",
        "fitz",
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.middleware",
        "uvicorn.middleware.asgi2",
        "uvicorn.middleware.proxy_headers",
        "fastapi",
        "pydantic",
        "pydantic.deprecated",
        "pydantic.json",
        "sqlalchemy",
        "sqlalchemy.sql.default_comparator",
        "certifi",
        "charset_normalizer",
        "xml",
        "xml.etree",
        "xml.etree.ElementTree",
        "markdown",
        "aiosqlite",
        "multipart",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "PyQt5", "PySide6", "matplotlib", "scipy",
        "PIL", "pandas", "notebook", "jupyter", "IPython",
        "setuptools", "pip", "wheel", "test", "unittest",
        "tensorflow", "torch", "torchvision",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="astro_nova_backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
