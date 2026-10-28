"""E2E M02 qua provider mock; tên file riêng tránh trùng module test unit."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from hostra_ai.part1_agent_tts.knowledge_engine import load_knowledge

ROOT = Path(__file__).resolve().parents[2]


def test_full_m02_mock_pipeline(tmp_path, mock_embeddings, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    catalog, faq = ROOT / "shared_data/inputs/catalog_skus.json", ROOT / "shared_data/inputs/product_faq.md"
    before = (catalog.read_bytes(), faq.read_bytes())
    engine = load_knowledge(catalog, faq)
    assert engine.index_status() == {"ready": False}
    lexical_before = engine.search_faq("Giá Lenovo bao nhiêu?")
    index = engine.build_vector_index(mock_embeddings)
    path = tmp_path / "index.json"
    index.save(path)
    assert index.chunk_count == 39
    second = load_knowledge(catalog, faq)
    second.load_vector_index(path, mock_embeddings)
    for mode in ("lexical", "semantic", "hybrid"):
        hits = second.search("ASUS RAM", mode=mode)
        assert len(hits) == 5
        for hit in hits:
            faq_record = second.get_faq(hit.metadata["faq_id"])
            assert hit.source_ref == f"faq:{faq_record.faq_id}"
            assert hit.metadata["needs_review"] == faq_record.needs_review
            assert hit.metadata["evidence_notes"] == faq_record.evidence_notes
        package = second.retrieve("Giá ASUS và Lenovo?", mode=mode)
        assert len(package.catalog_evidence) == 2
        assert package.status == "ok"
    assert engine.search_faq("Giá Lenovo bao nhiêu?") == lexical_before
    assert before == (catalog.read_bytes(), faq.read_bytes())


def test_lexical_startup_does_not_construct_sdk(monkeypatch):
    import openai
    forbidden = Mock(side_effect=AssertionError("Không được tạo API client"))
    monkeypatch.setattr(openai, "OpenAI", forbidden)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    engine = load_knowledge(ROOT / "shared_data/inputs/catalog_skus.json", ROOT / "shared_data/inputs/product_faq.md")
    assert engine.search("RAM")
    assert engine.search_faq("RAM")
    with pytest.raises(RuntimeError, match="provider"):
        engine.search("RAM", mode="semantic")
    forbidden.assert_not_called()
