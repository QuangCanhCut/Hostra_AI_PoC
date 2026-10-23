
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from hostra_ai.core.schemas import CommentEvent


# Dữ liệu mẫu hợp lệ, dùng chung cho các test
def valid_payload():
    return {
        "comment_id": "c001",
        "run_id": "demo_001",
        "viewer_id": "viewer_01",
        "source": "web",
        "text": "Sản phẩm A còn hàng không?",
        "active_sku_id": "SKU-A",
        "received_at": datetime.now(timezone.utc),
    }


# Test 1: Dữ liệu hợp lệ phải được chấp nhận
def test_valid_comment_event():
    event = CommentEvent(**valid_payload())

    assert event.comment_id == "c001"
    assert event.viewer_id == "viewer_01"
    assert event.active_sku_id == "SKU-A"


# Test 2: Tự động loại bỏ khoảng trắng ở đầu và cuối
def test_text_is_trimmed():
    data = valid_payload()
    data["text"] = "  Sản phẩm A còn hàng không?  "

    event = CommentEvent(**data)

    assert event.text == "Sản phẩm A còn hàng không?"


# Test 3: Những giá trị không hợp lệ phải bị từ chối
@pytest.mark.parametrize(
    "field,value",
    [
        ("text", "   "),
        ("text", 123),
        ("source", "facebook"),
        ("viewer_id", ""),
        ("active_sku_id", ""),
        ("comment_id", "invalid id"),
    ],
)
def test_invalid_fields(field, value):
    data = valid_payload()
    data[field] = value

    with pytest.raises(ValidationError):
        CommentEvent(**data)


# Test 4: Thiếu viewer_id phải bị từ chối
def test_missing_viewer_id():
    data = valid_payload()
    del data["viewer_id"]

    with pytest.raises(ValidationError):
        CommentEvent(**data)


# Test 5: Timestamp không có timezone phải bị từ chối
def test_naive_datetime_rejected():
    data = valid_payload()
    data["received_at"] = datetime(2026, 10, 23, 12, 0)

    with pytest.raises(ValidationError):
        CommentEvent(**data)


# Test 6: Timestamp có timezone phải được chuẩn hóa về UTC
def test_timestamp_normalized_to_utc():
    data = valid_payload()

    vietnam_tz = timezone(timedelta(hours=7))
    data["received_at"] = datetime(
        2026, 10, 23, 12, 0, tzinfo=vietnam_tz
    )

    event = CommentEvent(**data)

    assert event.received_at.utcoffset() == timedelta(0)
    assert event.received_at.hour == 5


# Test 7: Không chấp nhận field ngoài contract
def test_extra_field_rejected():
    data = valid_payload()
    data["unknown_field"] = "unexpected"

    with pytest.raises(ValidationError):
        CommentEvent(**data)
