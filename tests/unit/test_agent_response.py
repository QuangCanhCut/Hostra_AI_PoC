
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from hostra_ai.core.schemas import AgentResponse


def valid_payload():
    """Dữ liệu AgentResponse hợp lệ mặc định."""
    return {
        "response_id": "resp001",
        "comment_id": "c001",
        "run_id": "demo_001",
        "viewer_id": "viewer_01",
        "resolved_sku_id": "SKU-A",
        "status": "answered",
        "answer_text": "Sản phẩm A hiện vẫn còn hàng ạ!",
        "evidence_refs": ["catalog:SKU-A:stock"],
        "reason_code": None,
        "created_at": datetime.now(timezone.utc),
    }


# 1. Agent trả lời thành công
def test_answered_valid():
    response = AgentResponse(**valid_payload())

    assert response.status == "answered"
    assert response.resolved_sku_id == "SKU-A"
    assert response.answer_text is not None
    assert len(response.evidence_refs) == 1


# 2. Agent cần hỏi lại viewer
def test_clarification_valid():
    data = valid_payload()

    data.update({
        "status": "clarification_needed",
        "resolved_sku_id": None,
        "answer_text": "Bạn đang hỏi sản phẩm nào ạ?",
        "evidence_refs": [],
        "reason_code": "REFERENCE_AMBIGUOUS",
    })

    response = AgentResponse(**data)

    assert response.status == "clarification_needed"
    assert response.resolved_sku_id is None
    assert response.answer_text is not None


# 3. Agent bị chặn, không có nội dung TTS
def test_blocked_valid():
    data = valid_payload()

    data.update({
        "status": "blocked",
        "resolved_sku_id": None,
        "answer_text": None,
        "evidence_refs": [],
        "reason_code": "CATALOG_UNAVAILABLE",
    })

    response = AgentResponse(**data)

    assert response.status == "blocked"
    assert response.answer_text is None
    assert response.reason_code == "CATALOG_UNAVAILABLE"


# 4. Chuẩn hóa nội dung câu trả lời
def test_answer_text_trimmed():
    data = valid_payload()
    data["answer_text"] = "  Sản phẩm A còn hàng ạ!  "

    response = AgentResponse(**data)

    assert response.answer_text == "Sản phẩm A còn hàng ạ!"


# 5. Chuẩn hóa evidence references
def test_evidence_refs_trimmed():
    data = valid_payload()

    data["evidence_refs"] = [
        "  catalog:SKU-A:stock  ",
        "catalog:SKU-A:price",
    ]

    response = AgentResponse(**data)

    # Internally, evidence_refs is immutable tuple
    assert response.evidence_refs == (
        "catalog:SKU-A:stock",
        "catalog:SKU-A:price",
    )

    # JSON contract still represents evidence_refs as an array
    assert response.model_dump(mode="json")["evidence_refs"] == [
        "catalog:SKU-A:stock",
        "catalog:SKU-A:price",
    ]

# 6. Kiểm tra nhiều trường hợp không hợp lệ
@pytest.mark.parametrize(
    "updates",
    [
        # answered nhưng không có câu trả lời
        {"answer_text": None},

        # answer_text chỉ chứa khoảng trắng
        {"answer_text": "   "},

        # Câu trả lời vượt quá 500 ký tự
        {"answer_text": "A" * 501},

        # Trả lời về SKU nhưng thiếu bằng chứng
        {"evidence_refs": []},

        # answered không được có reason_code
        {"reason_code": "VERIFICATION_FAILED"},

        # clarification nhưng thiếu nội dung hỏi lại
        {
            "status": "clarification_needed",
            "resolved_sku_id": None,
            "answer_text": None,
            "evidence_refs": [],
            "reason_code": "REFERENCE_AMBIGUOUS",
        },

        # clarification sử dụng reason_code của blocked
        {
            "status": "clarification_needed",
            "reason_code": "CATALOG_UNAVAILABLE",
        },

        # blocked nhưng vẫn chứa nội dung TTS
        {
            "status": "blocked",
            "reason_code": "CATALOG_UNAVAILABLE",
        },

        # blocked nhưng không có lý do
        {
            "status": "blocked",
            "answer_text": None,
            "reason_code": None,
        },

        # Bằng chứng trùng lặp
        {
            "evidence_refs": [
                "catalog:SKU-A:stock",
                "catalog:SKU-A:stock",
            ],
        },

        # Timestamp không có timezone
        {
            "created_at": datetime(2026, 10, 23, 10, 0),
        },

        # ID chứa khoảng trắng
        {
            "response_id": "invalid id",
        },
    ],
)
def test_invalid_agent_responses(updates):
    data = valid_payload()
    data.update(updates)

    with pytest.raises(ValidationError):
        AgentResponse(**data)
