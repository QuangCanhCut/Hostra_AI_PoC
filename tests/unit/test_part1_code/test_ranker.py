"""RRF được kiểm tra bằng công thức; score BM25/cosine không cộng trực tiếp."""

import pytest

from hostra_ai.part1_agent_tts.knowledge.models import RetrievalHit
from hostra_ai.part1_agent_tts.knowledge.ranker import fuse_rrf


def hit(name, rank, score=10.0, skus=("A",)):
    return RetrievalHit(name, f"faq:{name}", score, rank, {"sku_ids": skus}, "text", "lexical")


def test_rrf_formula_dedup_and_components():
    hits = fuse_rrf([hit("A", 1), hit("B", 2)], [hit("B", 1, .8), hit("A", 2, .5)], top_k=5)
    assert [h.chunk_id for h in hits] == ["A", "B"]
    assert hits[0].score == pytest.approx(1 / 61 + 1 / 62)
    assert hits[0].component_ranks == {"lexical": 1, "semantic": 2}
    assert hits[0].component_scores == {"lexical": 10.0, "semantic": .5}
    assert fuse_rrf([hit("A", 1), hit("A", 2)], [], top_k=1)[0].score == pytest.approx(1 / 61)
    assert fuse_rrf([], [hit("B", 3)])[0].score == pytest.approx(1 / 63)


def test_bounded_sku_bonus_no_brand_favoritism():
    results = fuse_rrf([hit("A", 1), hit("B", 1, skus=("A", "B"))], [], sku_ids=("A",), sku_boost=.1)
    assert results[0].chunk_id == "A" and results[0].score == pytest.approx(1.1 / 61)
    unscoped = fuse_rrf([hit("A", 1), hit("B", 1)], [])
    assert unscoped[0].score == unscoped[1].score
    with pytest.raises(ValueError, match="sku_boost"):
        fuse_rrf([], [], sku_boost=.2)


@pytest.mark.parametrize("top,rrf", [(0, 60), (True, 60), (5, 0)])
def test_invalid_limits(top, rrf):
    with pytest.raises(ValueError):
        fuse_rrf([], [], top_k=top, rrf_k=rrf)
