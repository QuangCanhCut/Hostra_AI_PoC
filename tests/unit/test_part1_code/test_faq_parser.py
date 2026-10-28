"""Kiểm thử parser FAQ, nguồn tường minh và ghi chú cần review."""

from collections import Counter
from pathlib import Path

import pytest

from hostra_ai.part1_agent_tts.knowledge.catalog_repository import CatalogRepository
from hostra_ai.part1_agent_tts.knowledge.faq_parser import parse_faq

ROOT = Path(__file__).resolve().parents[3]
FAQ = ROOT / "shared_data/inputs/product_faq.md"
CATALOG = ROOT / "shared_data/inputs/catalog_skus.json"


@pytest.fixture
def catalog():
    return CatalogRepository(CATALOG)


def test_real_faq_counts_and_review(catalog):
    original = FAQ.read_bytes()
    records = parse_faq(FAQ, catalog)
    assert len(records) == len({r.faq_id for r in records}) == 39
    assert Counter(r.faq_id.split("-")[1] for r in records) == {"ASUS": 10, "LENOVO": 10, "COMPARE": 11, "SALES": 8}
    review = {r.faq_id: r for r in records if r.needs_review}
    assert set(review) == {"FAQ-LENOVO-008", "FAQ-LENOVO-009", "FAQ-COMPARE-010", "FAQ-SALES-002", "FAQ-SALES-003", "FAQ-SALES-006"}
    assert review["FAQ-LENOVO-008"].evidence_refs == ("catalog:LAPTOP-LENOVO-002",)
    assert review["FAQ-LENOVO-008"].evidence_notes == ("nguồn tham khảo Lenovo",)
    assert review["FAQ-SALES-002"].evidence_refs == ()
    assert "Catalog hai SKU" in review["FAQ-SALES-002"].evidence_raw
    assert review["FAQ-SALES-006"].evidence_notes[-1] == "**không có benchmark**"
    assert FAQ.read_bytes() == original


def sample(sku="`LAPTOP-ASUS-001`", evidence="`catalog:LAPTOP-ASUS-001`"):
    return ("### FAQ-TEST-001 — Tiêu đề\n"
            f"- **SKU:** {sku}\n- **Câu hỏi:** Câu **hỏi**?\n"
            "- **Trả lời gợi ý:** Nội dung **gốc**.\n- **Hỏi thêm:** Hỏi thêm?\n"
            f"- **Bằng chứng:** {evidence}\n")


def parse_text(tmp_path, catalog, content):
    path = tmp_path / "faq.md"
    path.write_text(content, encoding="utf-8")
    return parse_faq(path, catalog)


def test_explicit_refs_and_free_text_are_separate(tmp_path, catalog):
    record = parse_text(tmp_path, catalog, sample(evidence="`catalog:LAPTOP-ASUS-001`; nguồn tham khảo Lenovo"))[0]
    assert record.evidence_raw == "`catalog:LAPTOP-ASUS-001`; nguồn tham khảo Lenovo"
    assert record.evidence_refs == ("catalog:LAPTOP-ASUS-001",)
    assert record.evidence_notes == ("nguồn tham khảo Lenovo",) and record.needs_review
    assert record.answer_suggestion == "Nội dung **gốc**."
    note_only = parse_text(tmp_path, catalog, sample(evidence="Catalog hai SKU"))[0]
    assert note_only.evidence_refs == () and note_only.needs_review


@pytest.mark.parametrize("content, error", [
    (sample() + sample(), "trùng"),
    (sample(sku="`UNKNOWN`"), "SKU không tồn tại"),
    (sample(evidence="`catalog:UNKNOWN`"), "evidence SKU"),
    (sample().replace("- **Hỏi thêm:** Hỏi thêm?\n", ""), "thiếu trường"),
    (sample().replace("- **Câu hỏi:** Câu **hỏi**?", "- **Câu hỏi:**"), "thiếu trường"),
])
def test_rejects_bad_faq(tmp_path, catalog, content, error):
    with pytest.raises(ValueError, match=error):
        parse_text(tmp_path, catalog, content)


def test_non_faq_headings_excluded(tmp_path, catalog):
    records = parse_text(tmp_path, catalog, sample() + "\n## Fallback\n- **Bằng chứng:** không dùng\n### Ghi chú\nText\n")
    assert len(records) == 1 and records[0].evidence_raw == "`catalog:LAPTOP-ASUS-001`"


def test_malformed_heading_and_note_markdown(tmp_path, catalog):
    with pytest.raises(ValueError, match="Heading FAQ"):
        parse_text(tmp_path, catalog, sample().replace(" — ", " - ", 1))
    record = parse_text(tmp_path, catalog, sample(evidence="`catalog:LAPTOP-ASUS-001`; `nguồn khác`"))[0]
    assert record.evidence_notes == ("`nguồn khác`",)


def test_preserves_multiline_answer_markdown(tmp_path, catalog):
    content = sample().replace("Nội dung **gốc**.", "Nội dung **gốc**.  \n\nDòng tiếp theo")
    record = parse_text(tmp_path, catalog, content)[0]
    assert record.answer_suggestion == "Nội dung **gốc**.  \n\nDòng tiếp theo"


def test_horizontal_rule_in_answer_and_section_separator(tmp_path, catalog):
    content = sample().replace("Nội dung **gốc**.", "Đoạn đầu\n\n---\n\nĐoạn sau")
    content += "\n---\n\n## Fallback\nKhông phải FAQ\n"
    record = parse_text(tmp_path, catalog, content)[0]
    assert record.answer_suggestion == "Đoạn đầu\n\n---\n\nĐoạn sau"
    assert record.evidence_raw == "`catalog:LAPTOP-ASUS-001`"
    assert not record.needs_review
