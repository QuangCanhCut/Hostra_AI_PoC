"""Kiểm thử facade và ranh giới dữ liệu đầu vào."""

import json
from pathlib import Path

import pytest

from hostra_ai.part1_agent_tts.knowledge_engine import load_knowledge

ROOT = Path(__file__).resolve().parents[3]


def test_facade_reads_without_modifying_inputs():
    catalog = ROOT / "shared_data/inputs/catalog_skus.json"
    faq = ROOT / "shared_data/inputs/product_faq.md"
    before = (catalog.read_bytes(), faq.read_bytes())
    engine = load_knowledge(catalog, faq)
    assert engine.get_product("LAPTOP-ASUS-001")["price_vnd"] == 26500000
    assert engine.get_faq("FAQ-ASUS-001").faq_id == "FAQ-ASUS-001"
    assert len(engine.list_faq_chunks()) == 39
    chunks = engine.list_faq_chunks()
    assert chunks[0].metadata["source_file"] == "shared_data/inputs/product_faq.md"
    chunks[0].metadata["faq_id"] = "changed"
    assert engine.list_faq_chunks()[0].metadata["faq_id"] == "FAQ-ASUS-001"
    with pytest.raises(KeyError, match="FAQ"):
        engine.get_faq("unknown")
    assert before == (catalog.read_bytes(), faq.read_bytes())


def test_empty_faq_rejected_and_external_source_id(tmp_path):
    catalog = ROOT / "shared_data/inputs/catalog_skus.json"
    faq = tmp_path / "faq.md"
    faq.write_text("# Tài liệu\n## Fallback\nKhông có FAQ\n", encoding="utf-8")
    with pytest.raises(ValueError, match="không chứa mục FAQ"):
        load_knowledge(catalog, faq)
    faq.write_text((ROOT / "shared_data/inputs/product_faq.md").read_text(encoding="utf-8"), encoding="utf-8")
    engine = load_knowledge(catalog, faq, source_id="knowledge/product_faq.md")
    assert engine.get_faq("FAQ-ASUS-001").source_file == "knowledge/product_faq.md"
    assert engine.list_faq_chunks()[0].metadata["source_file"] == "knowledge/product_faq.md"


def test_search_faq_without_active_sku_filter(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    engine = load_knowledge(ROOT / "shared_data/inputs/catalog_skus.json", ROOT / "shared_data/inputs/product_faq.md")
    hits = engine.search_faq("Giá Lenovo bao nhiêu?", top_k=5)
    assert any("LAPTOP-LENOVO-002" in h.metadata["sku_ids"] for h in hits)
    comparison = engine.search_faq("ASUS Lenovo giá", sku_ids=("LAPTOP-ASUS-001", "LAPTOP-LENOVO-002"))
    assert comparison and all(len(h.metadata["sku_ids"]) == 2 for h in comparison)
    review = engine.search_faq("chính sách trả góp freeship", top_k=39)
    hit = next(h for h in review if h.chunk_id == "FAQ-SALES-002")
    assert hit.metadata["needs_review"] and hit.metadata["evidence_refs"] == ()
    assert "Catalog hai SKU" in hit.metadata["evidence_notes"]


def test_evaluation_fixture_labels_reference_existing_faqs():
    engine = load_knowledge(ROOT / "shared_data/inputs/catalog_skus.json", ROOT / "shared_data/inputs/product_faq.md")
    cases = json.loads((ROOT / "tests/fixtures/rag/lexical_eval.json").read_text(encoding="utf-8"))
    assert cases
    for case in cases:
        assert case["query"].strip() and case["relevant_faq_ids"]
        assert all(engine.get_faq(faq_id) for faq_id in case["relevant_faq_ids"])
        assert len(engine.search_faq(case["query"], top_k=3)) <= 3
