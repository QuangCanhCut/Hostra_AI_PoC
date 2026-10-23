
import json
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from hostra_ai.core.schemas import CommentEvent


EXPECTED_FIELDS = {
    "comment_id",
    "run_id",
    "viewer_id",
    "source",
    "text",
    "active_sku_id",
    "received_at",
}


def normalized_payload(source="web"):
    """Comment đã được backend bổ sung metadata."""
    return {
        "comment_id": "c001",
        "run_id": "demo_001",
        "viewer_id": "viewer_01",
        "source": source,
        "text": "Sản phẩm A còn hàng không?",
        "active_sku_id": "SKU-A",
        "received_at": "2026-10-23T10:00:00+07:00",
    }


# 1. Cả mock và web phải tuân theo cùng một contract
@pytest.mark.parametrize("source", ["mock", "web"])
def test_both_sources_use_same_contract(source):
    raw_json = json.dumps(normalized_payload(source))

    event = CommentEvent.model_validate_json(raw_json)
    output = json.loads(event.model_dump_json())

    assert set(output.keys()) == EXPECTED_FIELDS
    assert output["source"] == source
    assert output["viewer_id"] == "viewer_01"
    assert output["active_sku_id"] == "SKU-A"


# 2. Contract phải khai báo đủ 7 trường bắt buộc
def test_json_schema_required_fields():
    schema = CommentEvent.model_json_schema()

    assert set(schema["required"]) == EXPECTED_FIELDS
    assert schema["additionalProperties"] is False


# 3. JSON thiếu thông tin định danh phải bị từ chối
@pytest.mark.parametrize(
    "missing_field",
    ["viewer_id", "active_sku_id"],
)
def test_missing_required_field(missing_field):
    payload = normalized_payload()
    del payload[missing_field]

    with pytest.raises(ValidationError):
        CommentEvent.model_validate_json(json.dumps(payload))


# 4. JSON đầu ra phải dùng timestamp UTC
def test_serialized_timestamp_is_utc():
    event = CommentEvent.model_validate_json(
        json.dumps(normalized_payload())
    )

    output = json.loads(event.model_dump_json())

    timestamp = datetime.fromisoformat(
        output["received_at"].replace("Z", "+00:00")
    )

    assert timestamp.utcoffset() == timedelta(0)
