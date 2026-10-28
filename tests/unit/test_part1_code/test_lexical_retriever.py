"""Kiểm thử BM25, tokenizer và bảo toàn metadata bằng dữ liệu độc lập."""

from copy import deepcopy
import math
import unicodedata

import pytest

from hostra_ai.part1_agent_tts.knowledge.lexical_retriever import LexicalRetriever, tokenize
from hostra_ai.part1_agent_tts.knowledge.models import FAQChunk


def chunk(name, text, skus=("A",), **metadata):
    return FAQChunk(name, text, {"faq_id": name, "sku_ids": skus,
        "evidence_refs": ("catalog:A",), "evidence_notes": ("cần xem",),
        "needs_review": True, **metadata}, f"faq:{name}")


def test_bm25_score_against_hand_calculation():
    retriever = LexicalRetriever([chunk("one", "ram ram ssd"), chunk("two", "ram cpu")])
    hits = retriever.search("RAM")
    # N=2, df=2, độ dài trung bình=2.5, tf=2, k1=1.5, b=0.75.
    expected = math.log(1 + 0.5 / 2.5) * (2 * 2.5) / (2 + 1.5 * (0.25 + 0.75 * 3 / 2.5))
    assert hits[0].chunk_id == "one"
    assert hits[0].score == pytest.approx(expected)
    assert retriever.search("ram ram")[0].score == pytest.approx(expected)


def test_tokenizer_unicode_and_technical_words():
    decomposed = unicodedata.normalize("NFD", "KHÔNG nâng RAM, SSD CPU!")
    assert tokenize(decomposed) == ["không", "nâng", "ram", "ssd", "cpu"]
    assert tokenize("GIÁ\t  máy? 2.8K") == ["giá", "máy", "2", "8k"]
    assert tokenize("giá") != tokenize("gia")


def test_top_k_tie_order_and_empty():
    retriever = LexicalRetriever([chunk("B", "ram"), chunk("A", "ram"), chunk("C", "cpu")])
    hits = retriever.search("ram", top_k=10)
    assert [h.chunk_id for h in hits] == ["A", "B"]
    assert [h.rank for h in hits] == [1, 2]
    assert [h.chunk_id for h in retriever.search("ram", top_k=1)] == ["A"]
    assert retriever.search("ram") == retriever.search("ram")
    assert retriever.search("... !  ") == retriever.search("") == []
    assert retriever.search("khôngcótrongindex") == []
    assert LexicalRetriever([]).search("ram") == []


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "2", None])
def test_invalid_top_k(value):
    with pytest.raises(ValueError, match="top_k"):
        LexicalRetriever([chunk("A", "ram")]).search("ram", top_k=value)


def test_sku_filter_all_and_metadata_isolation():
    chunks = [chunk("asus", "ram", ("A",)), chunk("compare", "ram", ("A", "B")), chunk("lenovo", "ram", ("B",))]
    before = deepcopy(chunks)
    retriever = LexicalRetriever(chunks)
    assert {h.chunk_id for h in retriever.search("ram", sku_ids=("B",))} == {"lenovo", "compare"}
    both = retriever.search("ram", sku_ids=("A", "B"))
    assert [h.chunk_id for h in both] == ["compare"]
    assert retriever.search("ram", sku_ids=("unknown",)) == []
    assert both[0].source_ref == "faq:compare"
    assert both[0].metadata["evidence_refs"] == ("catalog:A",)
    assert both[0].metadata["evidence_notes"] == ("cần xem",) and both[0].metadata["needs_review"]
    assert chunks == before
    both[0].metadata["needs_review"] = False
    chunks[1].metadata["sku_ids"] = ()
    assert retriever.search("ram", sku_ids=("A", "B"))[0].metadata["needs_review"] is True
    assert before[1].metadata["sku_ids"] == ("A", "B")
    with pytest.raises(ValueError, match="sku_ids"):
        retriever.search("ram", sku_ids=())


def test_reject_duplicate_chunk_ids():
    with pytest.raises(ValueError, match="chunk_id"):
        LexicalRetriever([chunk("A", "ram"), chunk("A", "ssd")])
