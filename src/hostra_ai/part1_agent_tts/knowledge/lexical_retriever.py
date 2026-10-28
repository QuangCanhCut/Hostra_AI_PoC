"""BM25 lexical baseline chạy trong bộ nhớ, không gọi dịch vụ bên ngoài."""

from collections import Counter
from copy import deepcopy
import math
import re
import unicodedata

from .models import FAQChunk, LexicalSearchHit


def tokenize(text: str) -> list[str]:
    """Chuẩn hóa NFC, casefold và tách các chuỗi chữ/số; giữ dấu và từ 'không'."""
    normalized = unicodedata.normalize("NFC", unicodedata.normalize("NFC", text).casefold())
    return re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)


class LexicalRetriever:
    """Chỉ số BM25 Okapi trên snapshot chunks; thống kê luôn tính trên toàn corpus."""

    def __init__(self, chunks: list[FAQChunk], *, k1: float = 1.5, b: float = 0.75):
        if not math.isfinite(k1) or not math.isfinite(b) or k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 yêu cầu k1 > 0 và 0 <= b <= 1")
        if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
            raise ValueError("chunk_id phải duy nhất")
        self._chunks = deepcopy(chunks)
        self.k1, self.b = k1, b
        self._counts = [Counter(tokenize(chunk.retrieval_text)) for chunk in self._chunks]
        self._lengths = [sum(counts.values()) for counts in self._counts]
        self._avg_length = sum(self._lengths) / len(self._lengths) if self._lengths else 0.0
        frequencies: Counter[str] = Counter()
        for counts in self._counts:
            frequencies.update(counts.keys())
        total = len(self._chunks)
        self._idf = {term: math.log1p((total - df + 0.5) / (df + 0.5))
                     for term, df in frequencies.items()}

    def search(self, query: str, *, top_k: int = 5,
               sku_ids: tuple[str, ...] | None = None) -> list[LexicalSearchHit]:
        """Trả hit có điểm dương; lọc tùy chọn yêu cầu chunk chứa tất cả SKU.

        IDF/độ dài trung bình vẫn tính trên corpus gốc, không thay đổi theo bộ lọc.
        Query rỗng hoặc chỉ có dấu câu trả danh sách rỗng.
        """
        if not isinstance(query, str):
            raise TypeError("query phải là chuỗi")
        if type(top_k) is not int or top_k <= 0:
            raise ValueError("top_k phải là số nguyên dương")
        if sku_ids is not None and (not isinstance(sku_ids, tuple) or not sku_ids
                or any(not isinstance(sku, str) or not sku.strip() for sku in sku_ids)):
            raise ValueError("sku_ids phải là tuple không rỗng gồm các SKU")
        terms = set(tokenize(query))
        if not terms or not self._avg_length:
            return []
        requested = set(sku_ids or ())
        scored: list[tuple[float, FAQChunk]] = []
        # Sắp xếp token để tổng floating point xác định giữa các tiến trình Python.
        for chunk, counts, length in zip(self._chunks, self._counts, self._lengths):
            if requested and not requested.issubset(chunk.metadata.get("sku_ids", ())):
                continue
            score = 0.0
            for term in sorted(terms):
                frequency = counts.get(term, 0)
                if frequency:
                    denominator = frequency + self.k1 * (1 - self.b + self.b * length / self._avg_length)
                    score += self._idf[term] * frequency * (self.k1 + 1) / denominator
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return [LexicalSearchHit(chunk.chunk_id, chunk.source_ref, score, rank,
                                 deepcopy(chunk.metadata), chunk.retrieval_text)
                for rank, (score, chunk) in enumerate(scored[:top_k], start=1)]
