"""Kiểm thử mỗi FAQ tạo đúng một chunk đầy đủ và ổn định."""

from pathlib import Path

import pytest

from hostra_ai.part1_agent_tts.knowledge.catalog_repository import CatalogRepository
from hostra_ai.part1_agent_tts.knowledge.chunking import chunk_faqs
from hostra_ai.part1_agent_tts.knowledge.faq_parser import parse_faq

ROOT = Path(__file__).resolve().parents[3]


def test_chunk_metadata_and_original_answer():
    catalog = CatalogRepository(ROOT / "shared_data/inputs/catalog_skus.json")
    records = parse_faq(ROOT / "shared_data/inputs/product_faq.md", catalog)
    chunks = chunk_faqs(records)
    assert len(chunks) == len({c.chunk_id for c in chunks}) == 39
    assert [c.chunk_id for c in chunk_faqs(records)] == [c.chunk_id for c in chunks]
    record = next(r for r in records if r.faq_id == "FAQ-COMPARE-001")
    chunk = next(c for c in chunks if c.chunk_id == record.faq_id)
    assert chunk.metadata["sku_ids"] == ("LAPTOP-ASUS-001", "LAPTOP-LENOVO-002")
    assert chunk.metadata["evidence_refs"] == record.evidence_refs
    assert chunk.metadata["evidence_notes"] == record.evidence_notes
    assert chunk.metadata["source_file"] == record.source_file
    assert chunk.source_ref == "faq:FAQ-COMPARE-001"
    assert chunk.retrieval_text == f"{record.title}\n{record.question}\n{record.answer_suggestion}"
    with pytest.raises(ValueError, match="trùng"):
        chunk_faqs([record, record])
    review = next(r for r in records if r.faq_id == "FAQ-LENOVO-008")
    metadata = chunk_faqs([review])[0].metadata
    assert metadata["evidence_notes"] == ("nguồn tham khảo Lenovo",)
    assert metadata["evidence_refs"] == ("catalog:LAPTOP-LENOVO-002",)
    assert metadata["needs_review"] is True
