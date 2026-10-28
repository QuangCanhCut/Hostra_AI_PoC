"""Tạo chunk theo cấu trúc FAQ thay vì cắt văn bản theo kích thước."""

from .models import FAQChunk, FAQRecord


def chunk_faqs(records: list[FAQRecord]) -> list[FAQChunk]:
    """Mỗi FAQ tạo một chunk ổn định; không tách hoặc thay nội dung câu trả lời."""
    if len({record.faq_id for record in records}) != len(records):
        raise ValueError("Không thể tạo chunk từ FAQ ID trùng")
    return [FAQChunk(
        chunk_id=record.faq_id,
        retrieval_text=f"{record.title}\n{record.question}\n{record.answer_suggestion}",
        metadata={"faq_id": record.faq_id, "sku_ids": record.sku_ids,
                  "source_file": record.source_file, "evidence_refs": record.evidence_refs,
                  "evidence_notes": record.evidence_notes,
                  "needs_review": record.needs_review},
        source_ref=f"faq:{record.faq_id}",
    ) for record in records]
