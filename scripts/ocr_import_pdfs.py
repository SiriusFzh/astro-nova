"""扫描版 PDF → OpenCV 预处理 → Tesseract OCR → 导入知识库

用法: python scripts/ocr_import_pdfs.py

用 PyMuPDF 渲染每页 → OpenCV 灰度/二值化/降噪 →
Tesseract (chi_sim+eng) → 分块 → 导入知识库
"""
import os
import sys
import time

TESSERACT_PATH = r"F:\Tesseract\tesseract.exe"
TESSDATA_DIR = r"F:\Tesseract\tessdata"
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

import pytesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

import fitz
import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from astro_nova.knowledge.chunker import chunk_document
from astro_nova.knowledge.vector_store import VectorStore

PDF_DIR = r"E:\QQ\文件"
STORE_NAME = "textbooks"

PDFS = [
    ("基础天文学(1).pdf", "基础天文学"),
    ("《天文学新概论》第四版(苏宜).pdf", "天文学新概论"),
    ("郭硕鸿《电动力学》第三版.pdf", "电动力学_郭硕鸿"),
    ("物理学大题典 电磁学与电动力学（第二版）(1).pdf", "物理学大题典_电磁学与电动力学"),
    ("电磁学千题解 by 张之翔.pdf", "电磁学千题解"),
]


def preprocess_image(pix) -> np.ndarray:
    """PyMuPDF pixmap → OpenCV 预处理 (灰度 → Otsu 二值化 → 降噪)"""
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if pix.n >= 3 else img
    # Otsu 自适应二值化
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 降噪
    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
    return denoised


def ocr_page(page, page_num: int) -> str:
    """OCR 单页 PDF，返回识别文本"""
    try:
        pix = page.get_pixmap(dpi=250)
        processed = preprocess_image(pix)
        text = pytesseract.image_to_string(processed, lang="chi_sim+eng", config="--psm 6 --oem 1")
        return text.strip()
    except Exception as e:
        # 降级: 低 DPI 无预处理
        try:
            pix = page.get_pixmap(dpi=150)
            text = pytesseract.image_to_string(pix.tobytes("png"), lang="chi_sim+eng", config="--psm 6")
            return text.strip()
        except:
            return ""


def ocr_pdf(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    total = len(doc)
    pages = []
    basename = os.path.basename(pdf_path)
    print(f"  [{basename}] 共 {total} 页")

    t0 = time.time()
    for i in range(total):
        text = ocr_page(doc[i], i + 1)
        if text and len(text) > 15:
            pages.append({"page": i + 1, "text": text})

        if (i + 1) % 30 == 0 or i == total - 1:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"    已处理 {i+1}/{total} 页 ({rate:.1f} 页/秒), {len(pages)} 页有内容")

    doc.close()
    return pages


def import_to_knowledgebase(pages: list[dict], book_name: str) -> int:
    store = VectorStore(STORE_NAME)
    combined = 0

    for i in range(0, len(pages), 3):
        chunk_pages = pages[i:i + 3]
        text = "\n\n".join(p["text"] for p in chunk_pages)
        if len(text) < 30:
            continue

        p_start = chunk_pages[0]["page"]
        p_end = chunk_pages[-1]["page"]
        page_range = f"{p_start}-{p_end}" if p_start != p_end else str(p_start)
        doc_id = f"{book_name}_p{page_range}"

        chunks = chunk_document(text, doc_id=doc_id, metadata={
            "source": book_name,
            "pages": page_range,
            "type": "ocr_textbook",
        })
        for c in chunks:
            store.add_document(c)
        combined += 1

    store.save()
    print(f"  [OK] 导入 {combined} 个文档块 ({len(pages)} 页) → '{STORE_NAME}'")
    return combined


def main():
    print("=" * 60)
    print("扫描版 PDF OCR → 知识库导入")
    print("=" * 60)

    total_chunks = 0
    total_pages = 0

    for fname, book_name in PDFS:
        pdf_path = os.path.join(PDF_DIR, fname)
        if not os.path.isfile(pdf_path):
            print(f"[SKIP] 文件不存在: {fname}")
            continue

        print(f"\n{'='*50}")
        print(f"处理: {fname}")
        print(f"{'='*50}")

        try:
            t0 = time.time()
            pages = ocr_pdf(pdf_path)
            elapsed = time.time() - t0

            # Count total pages for progress
            doc_check = fitz.open(pdf_path)
            total = len(doc_check)
            doc_check.close()

            print(f"  OCR 完成: {len(pages)}/{total} 页有文字, 耗时 {elapsed:.0f}s")
            if pages:
                n = import_to_knowledgebase(pages, book_name)
                total_chunks += n
                total_pages += len(pages)

        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"总计: {total_pages} 页 OCR, {total_chunks} 个文档块 → 知识库 '{STORE_NAME}'")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
