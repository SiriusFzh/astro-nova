"""向量存储 — BM25 检索 + JSON 持久化

轻量实现，无外部依赖。适合学术文档的全文检索。

存储策略：
  - 数据写入用户目录 ~/.astro-nova/knowledge/ 以保证可写
  - 首次使用时从包内 seed/ 目录自动复制初始知识库
"""
import json
import math
import os
import re
import shutil
import threading
from collections import Counter
from typing import Optional

# 用户可写的数据目录
from astro_nova.utils.paths import get_data_dir as _get_data_dir
_USER_DATA_DIR = _get_data_dir("knowledge")
os.makedirs(_USER_DATA_DIR, exist_ok=True)

# 包内种子数据目录（随安装包发布）
_SEED_DIR = os.path.join(os.path.dirname(__file__), "seed")

STORAGE_DIR = _USER_DATA_DIR

# 中文+英文分词
# 先清理代码块标记等干扰字符
_CLEAN_RE = re.compile(r"```|~~~|—-+|__+")
_EN_RE = re.compile(r"[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)*")
_ZH_RE = re.compile(r"[一-鿿]{2,}")


def _tokenize(text: str) -> list[str]:
    """分词：保留英文词（>=2 字母）和中文连续字符（>=2 字）。"""
    text = _CLEAN_RE.sub(" ", text)
    tokens = _EN_RE.findall(text) + _ZH_RE.findall(text)
    return [t.lower() for t in tokens if len(t) > 1]


class Document:
    """文档块"""
    __slots__ = ("id", "content", "source", "metadata")
    def __init__(self, id: str, content: str, source: str = "", metadata: dict = None):
        self.id = id
        self.content = content
        self.source = source
        self.metadata = metadata or {}


class BM25Index:
    """BM25 索引 (Okapi BM25)"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: list[Document] = []
        self.doc_freq: dict[str, int] = {}      # term → 包含该 term 的文档数
        self.term_freqs: list[Counter] = []      # 每篇文档的 term 频率
        self.doc_lens: list[int] = []            # 每篇文档的长度 (词数)
        self.avg_len: float = 0
        self._lock = threading.Lock()

    def add(self, doc: Document):
        with self._lock:
            tokens = _tokenize(doc.content)
            tf = Counter(tokens)
            idx = len(self.documents)
            self.documents.append(doc)
            self.term_freqs.append(tf)
            self.doc_lens.append(len(tokens))
            for term in set(tokens):
                self.doc_freq[term] = self.doc_freq.get(term, 0) + 1
            self.avg_len = sum(self.doc_lens) / len(self.doc_lens)

    def add_batch(self, docs: list[Document]):
        for doc in docs:
            self.add(doc)

    def clear(self):
        with self._lock:
            self.documents.clear()
            self.term_freqs.clear()
            self.doc_lens.clear()
            self.doc_freq.clear()
            self.avg_len = 0

    @property
    def size(self) -> int:
        return len(self.documents)

    def search(self, query: str, top_k: int = 10) -> list[tuple[Document, float]]:
        """BM25 检索，返回 [(doc, score)]"""
        query_terms = _tokenize(query)
        if not query_terms or not self.documents:
            return []

        n = len(self.documents)
        scores = [0.0] * n
        qtf = Counter(query_terms)

        for term, qf in qtf.items():
            df = self.doc_freq.get(term, 0)
            if df == 0:
                continue
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)

            for i in range(n):
                tf = self.term_freqs[i].get(term, 0)
                if tf == 0:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * self.doc_lens[i] / self.avg_len)
                scores[i] += idf * (tf * (self.k1 + 1)) / denom

        scored = [(self.documents[i], scores[i]) for i in range(n) if scores[i] > 0]
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]


class VectorStore:
    """文档存储 — BM25 索引 + JSON 持久化"""

    def __init__(self, name: str = "default"):
        self.name = name
        self.index = BM25Index()
        self._store_path = os.path.join(STORAGE_DIR, f"{name}.json")
        self._loaded = False

    def _doc_path(self) -> str:
        return self._store_path

    def _seed_from_bundled(self):
        """首次运行：从包内 seed 目录复制种子知识库到用户数据目录。"""
        seed_file = os.path.join(_SEED_DIR, f"{self.name}.json")
        if not os.path.exists(seed_file):
            return  # 无种子数据
        if os.path.exists(self._store_path):
            return  # 用户已有数据
        os.makedirs(STORAGE_DIR, exist_ok=True)
        shutil.copy2(seed_file, self._store_path)
        print(f"[VectorStore] 初始知识库 '{self.name}' 已从种子数据创建")

    def _load(self):
        if self._loaded:
            return
        self._loaded = True
        self._seed_from_bundled()
        if not os.path.exists(self._doc_path()):
            return
        try:
            with open(self._doc_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            docs = []
            for item in data:
                docs.append(Document(
                    id=item["id"],
                    content=item["content"],
                    source=item.get("source", ""),
                    metadata=item.get("metadata", {}),
                ))
            self.index.add_batch(docs)
        except (json.JSONDecodeError, KeyError):
            pass

    def _save(self):
        data = []
        for doc in self.index.documents:
            data.append({
                "id": doc.id,
                "content": doc.content,
                "source": doc.source,
                "metadata": doc.metadata,
            })
        with open(self._doc_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_document(self, content: str, source: str = "", metadata: dict = None, doc_id: str = None):
        self._load()
        if doc_id is None:
            doc_id = f"doc_{len(self.index.documents)}"
        doc = Document(id=doc_id, content=content, source=source, metadata=metadata or {})
        self.index.add(doc)
        self._save()

    def add_batch(self, chunks: list[dict]):
        """批量添加，chunks: [{content, source, metadata}]"""
        self._load()
        docs = []
        for i, c in enumerate(chunks):
            doc_id = c.get("id", f"doc_{len(self.index.documents) + i}")
            docs.append(Document(
                id=doc_id,
                content=c["content"],
                source=c.get("source", ""),
                metadata=c.get("metadata", {}),
            ))
        self.index.add_batch(docs)
        self._save()

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """检索，返回带 {content, source, score, metadata} 的结果"""
        self._load()
        results = self.index.search(query, top_k)
        return [
            {
                "content": doc.content[:500],
                "content_full": doc.content,
                "source": doc.source,
                "score": round(score, 4),
                "metadata": doc.metadata,
            }
            for doc, score in results
        ]

    def count(self) -> int:
        self._load()
        return self.index.size

    def clear(self):
        self._load()
        self.index.clear()
        self._save()

    def sources(self) -> list[str]:
        """返回所有不同来源"""
        self._load()
        sources = set()
        for doc in self.index.documents:
            if doc.source:
                sources.add(doc.source)
        return sorted(sources)


# 全局存储实例
_stores: dict[str, VectorStore] = {}

def get_store(name: str = "default") -> VectorStore:
    if name not in _stores:
        _stores[name] = VectorStore(name)
    return _stores[name]
