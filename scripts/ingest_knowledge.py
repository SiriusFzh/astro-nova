"""
批量导入文档到知识库

用法:
    python ingest_knowledge.py import E:/QQ/文件/基础天文学(1).pdf
    python ingest_knowledge.py import E:/QQ/文件/普物笔记_extracted --recursive
    python ingest_knowledge.py search "太阳质量"
    python ingest_knowledge.py info
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from astro_nova.knowledge.document_loader import load_document, scan_directory
from astro_nova.knowledge.chunker import chunk_document
from astro_nova.knowledge.vector_store import get_store
from astro_nova.knowledge.retriever import retrieve, get_store_info


def ingest_file(filepath: str, store_name: str = "default", show_progress: bool = True):
    """导入单个文件到知识库。"""
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return 0

    basename = os.path.basename(filepath)
    if show_progress:
        print(f"正在读取: {basename}...", end=" ", flush=True)

    text = load_document(filepath)
    if not text:
        print(f"无法提取文本: {basename}")
        return 0

    size_mb = len(text) / 1024 / 1024
    if show_progress:
        print(f"({size_mb:.1f}MB 文本) 分块中...", end=" ", flush=True)

    chunks = chunk_document(text, strategy="smart", chunk_size=1000, chunk_overlap=200)
    if not chunks:
        print("分块为空")
        return 0

    store = get_store(store_name)
    batch = [
        {"content": c, "source": basename, "metadata": {"source_path": filepath}}
        for c in chunks
    ]
    store.add_batch(batch)

    if show_progress:
        print(f"[OK] {len(chunks)} 个块")
    return len(chunks)


def ingest_directory(
    dirpath: str,
    store_name: str = "default",
    extensions: set = None,
):
    """递归导入目录下所有支持的文件。"""
    files = scan_directory(dirpath, extensions)
    if not files:
        print(f"目录中未找到支持的文件: {dirpath}")
        return 0

    total = 0
    for f in files:
        total += ingest_file(f["path"], store_name)

    store = get_store(store_name)
    print(f"\n总计导入 {total} 个块，知识库共 {store.count()} 个文档")
    return total


def main():
    parser = argparse.ArgumentParser(description="知识库文档导入工具")
    sub = parser.add_subparsers(dest="command", required=True)

    # import 子命令
    p_import = sub.add_parser("import", help="导入文档")
    p_import.add_argument("path", help="文件或目录路径")
    p_import.add_argument("--store", default="default", help="知识库名称")
    p_import.add_argument("--recursive", "-r", action="store_true", help="递归导入目录")

    # search 子命令
    p_search = sub.add_parser("search", help="搜索知识库")
    p_search.add_argument("query", help="搜索关键词")
    p_search.add_argument("--store", default="default", help="知识库名称")
    p_search.add_argument("--top", type=int, default=5, help="返回数量")

    # info 子命令
    sub.add_parser("info", help="查看知识库状态")

    # clear 子命令
    p_clear = sub.add_parser("clear", help="清空知识库")
    p_clear.add_argument("--store", default="default", help="知识库名称")

    args = parser.parse_args()

    if args.command == "import":
        if os.path.isdir(args.path):
            ingest_directory(args.path, args.store)
        else:
            start = time.time()
            count = ingest_file(args.path, args.store)
            elapsed = time.time() - start
            if count:
                store = get_store(args.store)
                print(f"知识库共 {store.count()} 个文档 ({elapsed:.1f}s)")

    elif args.command == "search":
        results = retrieve(args.query, args.store, args.top)
        print(f"\n找到 {len(results)} 个结果:\n")
        for i, r in enumerate(results, 1):
            print(f"  #{i} [得分: {r['score']:.3f}] 来源: {r.get('source', '?')}")
            print(f"     {r['content'][:200]}...")
            print()

    elif args.command == "info":
        info = get_store_info(args.store if hasattr(args, 'store') and args.store else "default")
        print(f"知识库: {info['name']}")
        print(f"文档数: {info['doc_count']}")
        print(f"来源: {', '.join(info['sources']) if info['sources'] else '无'}")

    elif args.command == "clear":
        from astro_nova.knowledge.vector_store import get_store as gs
        store = gs(args.store if hasattr(args, 'store') and args.store else "default")
        store.clear()
        print(f"已清空知识库: {args.store if hasattr(args, 'store') and args.store else 'default'}")


if __name__ == "__main__":
    main()
