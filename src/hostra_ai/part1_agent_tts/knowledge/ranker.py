"""Xếp hạng hợp nhất bằng Reciprocal Rank Fusion, không trộn thang điểm thô."""

from copy import deepcopy
from dataclasses import replace

from .models import RetrievalHit


# ============================================================
# RRF — MỖI NGUỒN ĐÓNG GÓP 1 / (k + rank)
# ============================================================

def fuse_rrf(lexical: list[RetrievalHit], semantic: list[RetrievalHit], *,
             top_k: int = 5, rrf_k: int = 60, sku_ids: tuple[str, ...] | None = None,
             sku_boost: float = 0.05) -> list[RetrievalHit]:
    """Deduplicate theo chunk_id; bonus tối đa 10% chỉ khi scope SKU được cấp rõ.

    FAQ chứa đúng tập SKU được ưu tiên nhẹ hơn FAQ chứa thêm SKU khác.
    Không có scope thì không boost; không có ưu tiên theo tên hãng.
    """
    if type(top_k) is not int or top_k <= 0 or type(rrf_k) is not int or rrf_k <= 0:
        raise ValueError("top_k và rrf_k phải là số nguyên dương")
    if not 0 <= sku_boost <= 0.1:
        raise ValueError("sku_boost phải trong [0, 0.1]")
    records: dict[str, RetrievalHit] = {}
    totals: dict[str, float] = {}
    ranks: dict[str, dict[str, int]] = {}
    scores: dict[str, dict[str, float]] = {}
    for name, hits in (("lexical", lexical), ("semantic", semantic)):
        seen = set()
        for hit in hits:
            if type(hit.rank) is not int or hit.rank <= 0:
                raise ValueError("Retriever rank phải là số nguyên dương")
            if hit.chunk_id in seen:
                continue
            seen.add(hit.chunk_id)
            previous = records.get(hit.chunk_id)
            if previous is not None and (previous.source_ref != hit.source_ref or previous.metadata != hit.metadata
                                         or previous.retrieval_text != hit.retrieval_text):
                raise ValueError("Hai retrievers trả metadata khác nhau cho cùng chunk")
            records[hit.chunk_id] = hit
            totals[hit.chunk_id] = totals.get(hit.chunk_id, 0.0) + 1.0 / (rrf_k + hit.rank)
            ranks.setdefault(hit.chunk_id, {})[name] = hit.rank
            scores.setdefault(hit.chunk_id, {})[name] = hit.score
    fused = []
    for chunk_id, hit in records.items():
        bonus = sku_boost if sku_ids and set(hit.metadata["sku_ids"]) == set(sku_ids) else 0.0
        score = totals[chunk_id] * (1 + bonus)
        fused.append(replace(deepcopy(hit), score=score, mode="hybrid",
            component_scores=dict(scores[chunk_id]), component_ranks=dict(ranks[chunk_id])))
    fused.sort(key=lambda hit: (-hit.score, hit.chunk_id))
    return [replace(hit, rank=rank) for rank, hit in enumerate(fused[:top_k], start=1)]
