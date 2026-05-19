"""
astro-nova / scripts / arxiv_download.py
ArXiv PDF 下载与文本提取工具

依赖: pip install arxiv pymupdf requests

用法:
    python arxiv_download.py download 2301.00001 --output ./papers
    python arxiv_download.py extract ./papers/2301.00001.pdf
    python arxiv_download.py fetch-text 2301.00001
"""

import argparse
import os
import sys
import urllib.request

try:
    import arxiv
except ImportError:
    print("请先安装 arxiv: pip install arxiv", file=sys.stderr)
    sys.exit(1)

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def download_pdf(arxiv_id: str, output_dir: str = ".") -> str | None:
    """下载 arXiv 论文 PDF，返回本地路径。"""
    os.makedirs(output_dir, exist_ok=True)
    # 去除版本号后缀用于目录命名，保留完整 ID 用于 URL
    base_id = arxiv_id.split("v")[0]
    safe_id = arxiv_id.replace(".", "_").replace("/", "_")
    pdf_path = os.path.join(output_dir, f"{safe_id}.pdf")

    if os.path.exists(pdf_path):
        print(f"文件已存在: {pdf_path}")
        return pdf_path

    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    print(f"下载中: {url}")
    try:
        urllib.request.urlretrieve(url, pdf_path)
        print(f"保存至: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"下载失败: {e}", file=sys.stderr)
        return None


def extract_text(pdf_path: str) -> str | None:
    """从 PDF 提取文本内容。"""
    if fitz is None:
        print("需要安装 pymupdf: pip install pymupdf", file=sys.stderr)
        return None

    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}", file=sys.stderr)
        return None

    try:
        doc = fitz.open(pdf_path)
        text_parts = []
        for page_num, page in enumerate(doc, 1):
            text = page.get_text().strip()
            if text:
                text_parts.append(f"--- Page {page_num} ---\n{text}")
        doc.close()
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"文本提取失败: {e}", file=sys.stderr)
        return None


def fetch_and_extract(arxiv_id: str, output_dir: str = ".") -> str | None:
    """下载 PDF 并提取文本，返回文本内容。"""
    pdf_path = download_pdf(arxiv_id, output_dir)
    if not pdf_path:
        return None
    return extract_text(pdf_path)


def main():
    parser = argparse.ArgumentParser(description="ArXiv PDF 下载与文本提取")
    sub = parser.add_subparsers(dest="command", required=True)

    p_dl = sub.add_parser("download", help="下载 PDF")
    p_dl.add_argument("arxiv_id", help="arXiv ID")
    p_dl.add_argument("--output", "-o", default=".", help="保存目录")

    p_ext = sub.add_parser("extract", help="从 PDF 提取文本")
    p_ext.add_argument("pdf_path", help="PDF 文件路径")

    p_ft = sub.add_parser("fetch-text", help="下载并提取文本")
    p_ft.add_argument("arxiv_id", help="arXiv ID")
    p_ft.add_argument("--output", "-o", default=".", help="保存目录")

    args = parser.parse_args()

    if args.command == "download":
        download_pdf(args.arxiv_id, args.output)

    elif args.command == "extract":
        text = extract_text(args.pdf_path)
        if text:
            print(text[:2000])
            print(f"\n... (共 {len(text)} 字符)")

    elif args.command == "fetch-text":
        text = fetch_and_extract(args.arxiv_id, args.output)
        if text:
            print(text[:2000])
            print(f"\n... (共 {len(text)} 字符)")


if __name__ == "__main__":
    main()
