
import json
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from hostra_ai.core.schemas import AgentResponse


EXPECTED_FIELDS = {
    "response_id",
    "comment_id",
    "run_id",
    "viewer_id",
    "resolved_sku_id",
    "status",
    "answer_text",
    "evidence_refs",
    "reason_code",
    "created_at",
}


def valid_json_payload():
    return {
        "response_id": "resp001",
        "comment_id": "c001",
        "run_id": "demo_001",
        "viewer_id": "viewer_01",
        "resolved_sku_id": "SKU-A",
        "status": "answered",
        "answer_text": "Sản phẩm A còn hàng ạ!",
        "evidence_refs": ["catalog:SKU-A:stock"],
        "reason_code": None,
        "created_at": "2026-10-23T10:00:02+07:00",
    }


# 1. Kiểm tra JSON của cả ba trạng thái
@pytest.mark.parametrize(
    "status",
    [
        "answered",
        "clarification_needed",
        "blocked",
    ],
)
def test_json_roundtrip_for_all_statuses(status):
    payload = valid_json_payload()

    if status == "clarification_needed":
        payload.update({
            "status": "clarification_needed",
            "resolved_sku_id": None,
            "answer_text": "Bạn đang hỏi mẫu nào ạ?",
            "evidence_refs": [],
            "reason_code": "REFERENCE_AMBIGUOUS",
        })

    elif status == "blocked":
        payload.update({
            "status": "blocked",
            "resolved_sku_id": None,
            "answer_text": None,
            "evidence_refs": [],
            "reason_code": "CATALOG_UNAVAILABLE",
        })

    response = AgentResponse.model_validate_json(
        json.dumps(payload)
    )

    output = json.loads(response.model_dump_json())

    assert set(output.keys()) == EXPECTED_FIELDS
    assert output["status"] == status
    assert output["comment_id"] == "c001"

    # blocked không có nội dung để đưa sang TTS
    if status == "blocked":
        assert output["answer_text"] is None
    else:
        assert output["answer_text"] is not None

    # Timestamp đầu ra phải được chuẩn hóa UTC
    timestamp = datetime.fromisoformat(
        output["created_at"].replace("Z", "+00:00")
    )

    assert timestamp.utcoffset() == timedelta(0)


# 2. JSON Schema phải có đủ 10 trường bắt buộc
def test_contract_required_fields():
    schema = AgentResponse.model_json_schema()

    assert set(schema["required"]) == EXPECTED_FIELDS
    assert schema["additionalProperties"] is False


# 3. Thiếu trường bắt buộc phải bị từ chối
@pytest.mark.parametrize(
    "missing_field",
    [
        "comment_id",
        "reason_code",
    ],
)
def test_missing_required_fields(missing_field):
    payload = valid_json_payload()
    del payload[missing_field]

    with pytest.raises(ValidationError):
        AgentResponse.model_validate_json(
            json.dumps(payload)
        )


# 4. Không chấp nhận trường ngoài contract
def test_extra_field_rejected():
    payload = valid_json_payload()

    payload["unknown_field"] = "unexpected"

    with pytest.raises(ValidationError):
        AgentResponse.model_validate_json(
            json.dumps(payload)
        )
