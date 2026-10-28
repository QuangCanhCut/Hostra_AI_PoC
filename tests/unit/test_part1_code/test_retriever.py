"""Kiểm thử routing/evidence bằng mock vectors, không gọi API thật."""

from pathlib import Path

import pytest

from hostra_ai.part1_agent_tts.knowledge.lexical_retriever import LexicalRetriever
from hostra_ai.part1_agent_tts.knowledge.models import RagConfig
from hostra_ai.part1_agent_tts.knowledge.retriever import KnowledgeRetriever
from hostra_ai.part1_agent_tts.knowledge.vector_index import VectorIndex
from hostra_ai.part1_agent_tts.knowledge_engine import load_knowledge

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def retriever(mock_embeddings):
    engine = load_knowledge(ROOT / "shared_data/inputs/catalog_skus.json", ROOT / "shared_data/inputs/product_faq.md")
    chunks = engine.list_faq_chunks()
    index = VectorIndex(chunks, mock_embeddings.embed_documents([c.retrieval_text for c in chunks]),
        provider=mock_embeddings.provider_name, model=mock_embeddings.model, requested_dimensions=8)
    return KnowledgeRetriever(chunks, engine.catalog, LexicalRetriever(chunks), RagConfig(), provider=mock_embeddings, index=index)


def test_modes_and_cached_query(retriever, mock_embeddings):
    for mode in ("lexical", "semantic", "hybrid"):
        hits = retriever.search("ASUS RAM", mode=mode)
        assert len(hits) == 5 and all(h.mode == mode for h in hits)
        assert all("evidence_notes" in h.metadata for h in hits)
    assert mock_embeddings.query_calls == 1
    assert retriever.search("", mode="semantic") == []
    with pytest.raises(ValueError):
        retriever.search("RAM", top_k=0)


def test_missing_dependencies_and_lexical_offline(retriever):
    retriever.provider, retriever.index = None, None
    assert retriever.search("RAM", mode="lexical")
    with pytest.raises(RuntimeError, match="provider"):
        retriever.search("RAM", mode="semantic")


def test_comparison_catalog_authority_and_ambiguity(retriever):
    package = retriever.retrieve("Giá ASUS so với Lenovo?", mode="hybrid")
    assert package.status == "ok"
    assert set(package.sku_ids) == {"LAPTOP-ASUS-001", "LAPTOP-LENOVO-002"}
    assert {fact.value for fact in package.catalog_evidence} == {26500000, 25690000}
    assert all(len(h.metadata["sku_ids"]) == 2 for h in package.faq_hits)
    comparison = retriever.retrieve("ASUS so với Lenovo khác nhau thế nào?")
    assert len(comparison.catalog_evidence) == 2
    assert {e.source_ref for e in comparison.catalog_evidence} == {
        "catalog:LAPTOP-ASUS-001", "catalog:LAPTOP-LENOVO-002"}
    ambiguous = retriever.retrieve("Máy đó giá bao nhiêu?", mode="hybrid")
    assert ambiguous.status == "insufficient_evidence" and ambiguous.sku_ids == ()
    assert ambiguous.reason == "AMBIGUOUS_SKU"
    conflict = retriever.retrieve("Giá ASUS và Lenovo?", sku_ids=("LAPTOP-ASUS-001",))
    assert conflict.reason == "SKU_SCOPE_CONFLICT" and not conflict.catalog_evidence


def test_ood_and_review_evidence(retriever):
    assert retriever.retrieve("Hôm nay đội nào thắng bóng đá?").status == "no_hit"
    package = retriever.retrieve("Shop có trả góp freeship không?", top_k=39)
    hit = next(h for h in package.faq_hits if h.metadata["faq_id"] == "FAQ-SALES-002")
    assert hit.metadata["needs_review"] is True
    assert hit.metadata["evidence_refs"] == ()
    assert "Catalog hai SKU" in hit.metadata["evidence_notes"]
    assert "FAQ_NEEDS_REVIEW" in package.warnings
    null = retriever.retrieve("ASUS nâng SSD được không?")
    assert null.catalog_evidence[0].value["upgradable"] is None
