"""Các mô hình nội bộ cho bước chuẩn bị tri thức, không phải public contract."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FAQRecord:
    """Một mục FAQ cùng nội dung Markdown và thông tin nguồn chưa xác minh."""

    faq_id: str
    title: str
    sku_ids: tuple[str, ...]
    question: str
    answer_suggestion: str
    follow_up: str
    evidence_refs: tuple[str, ...]
    evidence_raw: str
    evidence_notes: tuple[str, ...]
    needs_review: bool
    source_file: str


@dataclass(frozen=True)
class FAQChunk:
    """Một đơn vị truy xuất, giữ trọn câu hỏi và câu trả lời của FAQ."""

    chunk_id: str
    retrieval_text: str
    metadata: dict[str, Any]
    source_ref: str


@dataclass(frozen=True)
class LexicalSearchHit:
    """Kết quả truy xuất nội bộ; score không phải xác suất hoặc xác minh."""

    chunk_id: str
    source_ref: str
    score: float
    rank: int
    metadata: dict[str, Any]
    retrieval_text: str


@dataclass(frozen=True)
class CatalogEvidence:
    """Giá trị đọc trực tiếp từ catalog, có thể là None nếu nguồn ghi null."""

    sku_id: str
    field_path: str | None
    value: Any
    source_ref: str
    data_type: str
