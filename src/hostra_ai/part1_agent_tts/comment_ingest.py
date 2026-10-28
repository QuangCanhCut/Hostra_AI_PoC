"""Đọc và kiểm tra bình luận đầu vào; chưa lọc spam hay nội dung trùng."""

import json
from pathlib import Path

from pydantic import ValidationError

from hostra_ai.core.schemas import CommentEvent


def load_catalog_skus(path: str | Path) -> set[str]:
    """Đọc catalog và trả về tập SKU hợp lệ để kiểm tra Active SKU.

    Catalog rỗng, thiếu SKU hoặc có SKU trùng sẽ gây lỗi thay vì bị bỏ qua.
    """
    with Path(path).open(encoding="utf-8") as stream:
        catalog = json.load(stream)
    try:
        products = catalog["products"]
        if not isinstance(products, list) or not products:
            raise ValueError("products must be a non-empty list")
        ids = [product["sku_id"] for product in products]
        if any(not isinstance(sku, str) or not sku for sku in ids) or len(set(ids)) != len(ids):
            raise ValueError("invalid or duplicate SKU")
        return set(ids)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid catalog {path}: {exc}") from exc


def ingest_comments(path: str | Path, *, run_id: str, catalog_skus: set[str]) -> list[CommentEvent]:
    """Chuyển danh sách JSON thành sự kiện hợp lệ của một phiên demo.

    run_id là phiên được phép nhận; catalog_skus chứa các SKU đã biết.
    Nếu một bản ghi sai, hàm báo lỗi kèm vị trí/ID và không trả kết quả dở dang.
    """
    with Path(path).open(encoding="utf-8") as stream:
        records = json.load(stream)
    if not isinstance(records, list):
        raise ValueError("Comments JSON must be a list")
    events: list[CommentEvent] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        label = f"record {index}"
        if not isinstance(record, dict):
            raise ValueError(f"{label}: expected object")
        label += f" (comment_id={record.get('comment_id')!r})"
        # Contract tự kiểm tra các trường, cắt khoảng trắng đầu/cuối và đổi giờ sang UTC.
        try:
            event = CommentEvent.model_validate(record)
        except ValidationError as exc:
            raise ValueError(f"{label}: {exc}") from exc
        if event.run_id != run_id:
            raise ValueError(f"{label}: run_id does not match {run_id}")
        if event.active_sku_id not in catalog_skus:
            raise ValueError(f"{label}: unknown active_sku_id {event.active_sku_id}")
        if event.comment_id in seen:
            raise ValueError(f"{label}: duplicate comment_id in run")
        seen.add(event.comment_id)
        events.append(event)
    # sorted ổn định: các bình luận cùng thời điểm giữ nguyên thứ tự trong file.
    return sorted(events, key=lambda event: event.received_at)
