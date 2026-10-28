"""Phân tích các mục FAQ từ Markdown, giữ nguyên nội dung và nguồn ghi chú."""

import re
from pathlib import Path

from .catalog_repository import CatalogRepository
from .models import FAQRecord


HEADING = re.compile(r"^###\s+(FAQ-[A-Za-z0-9-]+)\s+—\s+(.+?)\s*$")
ANY_HEADING = re.compile(r"^#{1,3}\s+")
FIELD = re.compile(r"^- \*\*(SKU|Câu hỏi|Trả lời gợi ý|Hỏi thêm|Bằng chứng):\*\* ?(.*)$")
SKU_TOKEN = re.compile(r"`([^`]+)`")
REF = re.compile(r"(?<![\w:-])catalog:([A-Za-z0-9][A-Za-z0-9._-]*)")
FIELDS = ("SKU", "Câu hỏi", "Trả lời gợi ý", "Hỏi thêm", "Bằng chứng")


def parse_faq(path: str | Path, catalog: CatalogRepository, *, source_id: str | None = None) -> list[FAQRecord]:
    """Đọc FAQ; source_id tùy chọn là định danh nguồn ổn định do bên gọi cấp."""
    if source_id is not None and not source_id.strip():
        raise ValueError("source_id không được rỗng")
    source = source_id if source_id is not None else str(path)
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    records: list[FAQRecord] = []
    seen: set[str] = set()
    heading: tuple[str, str] | None = None
    fields: dict[str, list[str]] = {}
    current: str | None = None

    def finish() -> None:
        if heading is None:
            return
        faq_id, title = heading
        if faq_id in seen:
            raise ValueError(f"FAQ ID trùng: {faq_id}")
        # Dải phân cách cuối mục, sau field Bằng chứng và trước heading tiếp theo,
        # không thuộc nội dung field. Quy ước này không áp dụng trong câu trả lời.
        if current == "Bằng chứng":
            parts = fields[current]
            end = len(parts)
            while end and not parts[end - 1].strip():
                end -= 1
            if end >= 2 and parts[end - 1].strip() == "---" and not parts[end - 2].strip():
                del parts[end - 1:]
        # Chỉ bỏ các dòng trống phân cách cuối field, không cắt Markdown trong nội dung.
        values = {name: "\n".join(parts).rstrip("\n") for name, parts in fields.items()}
        missing = [name for name in FIELDS if not values.get(name, "").strip()]
        if missing:
            raise ValueError(f"{faq_id}: thiếu trường {', '.join(missing)}")
        sku_raw = values["SKU"]
        skus = SKU_TOKEN.findall(sku_raw)
        if not skus or re.sub(r"[\s,;]+", "", SKU_TOKEN.sub("", sku_raw)):
            raise ValueError(f"{faq_id}: SKU không đúng định dạng: {sku_raw}")
        if len(set(skus)) != len(skus):
            raise ValueError(f"{faq_id}: SKU bị lặp")
        for sku in skus:
            if sku not in catalog.sku_ids:
                raise ValueError(f"{faq_id}: SKU không tồn tại: {sku}")
        raw = values["Bằng chứng"]
        matches = list(REF.finditer(raw))
        refs: list[str] = []
        for match in matches:
            sku = match.group(1)
            if sku not in catalog.sku_ids:
                raise ValueError(f"{faq_id}: evidence SKU không tồn tại: {sku}")
            ref = f"catalog:{sku}"
            if ref not in refs:
                refs.append(ref)
        # Chỉ loại các ref tường minh và dấu phân cách; phần còn lại là ghi chú nguồn.
        remainder = re.sub(r"`(catalog:[A-Za-z0-9][A-Za-z0-9._-]*)`", r"\1", raw)
        remainder = REF.sub("", remainder)
        notes = tuple(piece.strip(" \t\n,;") for piece in re.split(r"[;\n]", remainder)
                      if piece.strip(" \t\n,;"))
        records.append(FAQRecord(faq_id, title, tuple(skus), values["Câu hỏi"],
            values["Trả lời gợi ý"], values["Hỏi thêm"], tuple(refs), raw,
            notes, bool(notes) or not refs, source))
        seen.add(faq_id)

    for line in lines:
        match = HEADING.match(line)
        if match:
            finish()
            heading = (match.group(1), match.group(2))
            fields, current = {}, None
        elif re.match(r"^###\s+FAQ-", line):
            raise ValueError(f"Heading FAQ không hợp lệ: {line}")
        elif ANY_HEADING.match(line):
            finish()
            heading, fields, current = None, {}, None
        elif heading is not None:
            field = FIELD.match(line)
            if field:
                current = field.group(1)
                if current in fields:
                    raise ValueError(f"{heading[0]}: trường {current} bị lặp")
                fields[current] = [field.group(2)]
            elif current is not None:
                fields[current].append(line)
    finish()
    return records
