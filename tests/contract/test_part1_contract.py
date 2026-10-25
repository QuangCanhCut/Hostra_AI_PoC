"""Contract tests for the five HOSTRA AI PoC Part 1 schemas.

These tests lock the public JSON shape, required/nullable fields, and
serialization compatibility. Pydantic unit validators are covered by
tests/unit/test_part1.py in the application repository.

The service layer must separately enforce cross-record references,
approved text sources, queue policies, Active SKU and actual WAV files.
"""

import json

import pytest
from pydantic import ValidationError

from hostra_ai.core.schemas.part1 import (
    AgentResponse,
    AudioArtifact,
    CommentDecision,
    CommentEvent,
    SpeechTurn,
)


TIMESTAMP = "2026-10-25T12:00:00Z"


@pytest.fixture
def comment_payload():
    return {
        "comment_id": "cmt_001",
        "run_id": "demo_001",
        "viewer_id": "viewer_001",
        "source": "mock",
        "text": "Sản phẩm này giá bao nhiêu?",
        "active_sku_id": "sku_A",
        "received_at": TIMESTAMP,
    }


@pytest.fixture
def decision_payload():
    return {
        "decision_id": "dec_001",
        "run_id": "demo_001",
        "comment_id": "cmt_001",
        "action": "selected",
        "reason_code": None,
        "priority_score": 85,
        "duplicate_of": None,
        "policy_version": "policy_20261025",
        "decided_at": TIMESTAMP,
    }


@pytest.fixture
def response_payload():
    return {
        "response_id": "resp_001",
        "comment_id": "cmt_001",
        "run_id": "demo_001",
        "viewer_id": "viewer_001",
        "resolved_sku_id": "sku_A",
        "status": "answered",
        "answer_text": "Giá sản phẩm được lấy từ catalog.",
        "evidence_refs": ["catalog:sku_A:price"],
        "reason_code": None,
        "created_at": TIMESTAMP,
    }


@pytest.fixture
def reply_turn_payload():
    return {
        "speech_turn_id": "turn_reply_001",
        "run_id": "demo_001",
        "speech_type": "comment_reply",
        "sku_id": "sku_A",
        "text": "Giá sản phẩm được lấy từ catalog.",
        "response_id": "resp_001",
        "script_ref": None,
        "priority": 80,
        "created_at": TIMESTAMP,
    }


@pytest.fixture
def audio_payload():
    return {
        "audio_id": "aud_001",
        "speech_turn_id": "turn_reply_001",
        "response_id": "resp_001",
        "run_id": "demo_001",
        "voice_id": "demo_voice_01",
        "file_path": (
            "shared_data/runs/demo_001/"
            "step1_agent_audio/audio/aud_001.wav"
        ),
        "format": "wav",
        "codec": "pcm_s16le",
        "sample_rate_hz": 24000,
        "channels": 1,
        "duration_ms": 3200,
        "created_at": TIMESTAMP,
    }


@pytest.fixture
def contract_cases(
    comment_payload,
    decision_payload,
    response_payload,
    reply_turn_payload,
    audio_payload,
):
    return [
        (CommentEvent, comment_payload),
        (CommentDecision, decision_payload),
        (AgentResponse, response_payload),
        (SpeechTurn, reply_turn_payload),
        (AudioArtifact, audio_payload),
    ]


def test_all_five_contracts_accept_valid_payloads(contract_cases):
    for schema, payload in contract_cases:
        assert isinstance(schema.model_validate(payload), schema)


def test_json_round_trip_for_every_contract(contract_cases):
    for schema, payload in contract_cases:
        instance = schema.model_validate(payload)
        wire_json = instance.model_dump_json()
        recovered = schema.model_validate_json(wire_json)
        assert recovered == instance, schema.__name__


def test_public_json_keys_match_contracts(contract_cases):
    """A changed field name should be an intentional contract update."""
    expected = {
        "CommentEvent": {
            "comment_id", "run_id", "viewer_id", "source",
            "text", "active_sku_id", "received_at",
        },
        "CommentDecision": {
            "decision_id", "run_id", "comment_id", "action",
            "reason_code", "priority_score", "duplicate_of",
            "policy_version", "decided_at",
        },
        "AgentResponse": {
            "response_id", "comment_id", "run_id", "viewer_id",
            "resolved_sku_id", "status", "answer_text",
            "evidence_refs", "reason_code", "created_at",
        },
        "SpeechTurn": {
            "speech_turn_id", "run_id", "speech_type", "sku_id",
            "text", "response_id", "script_ref", "priority", "created_at",
        },
        "AudioArtifact": {
            "audio_id", "speech_turn_id", "response_id", "run_id",
            "voice_id", "file_path", "format", "codec",
            "sample_rate_hz", "channels", "duration_ms", "created_at",
        },
    }
    for schema, payload in contract_cases:
        wire = json.loads(schema.model_validate(payload).model_dump_json())
        assert set(wire) == expected[schema.__name__]


def test_required_fields_are_enforced(contract_cases):
    """Field(...), even when nullable, is required in the payload."""
    for schema, payload in contract_cases:
        required = {
            name for name, field in schema.model_fields.items()
            if field.is_required()
        }
        for field_name in required:
            incomplete = payload.copy()
            incomplete.pop(field_name)
            with pytest.raises(ValidationError):
                schema.model_validate(incomplete)


def test_all_part1_fields_are_explicitly_required(contract_cases):
    optional = {
        schema.__name__: {
            name for name, field in schema.model_fields.items()
            if not field.is_required()
        }
        for schema, _ in contract_cases
    }
    assert optional == {
        "CommentEvent": set(),
        "CommentDecision": set(),
        "AgentResponse": set(),
        "SpeechTurn": set(),
        "AudioArtifact": set(),
    }


def test_nullable_fields_remain_explicit_in_json(
    decision_payload, response_payload, reply_turn_payload
):
    decision = json.loads(
        CommentDecision.model_validate(decision_payload).model_dump_json()
    )
    assert decision["reason_code"] is None
    assert decision["duplicate_of"] is None

    response = response_payload.copy()
    response["resolved_sku_id"] = None
    response["status"] = "clarification_needed"
    response["answer_text"] = "Bạn đang hỏi sản phẩm nào?"
    response["evidence_refs"] = []
    response["reason_code"] = "REFERENCE_AMBIGUOUS"
    wire_response = json.loads(AgentResponse(**response).model_dump_json())
    assert wire_response["resolved_sku_id"] is None
    assert wire_response["evidence_refs"] == []

    turn = json.loads(SpeechTurn(**reply_turn_payload).model_dump_json())
    assert "script_ref" in turn and turn["script_ref"] is None


def test_evidence_refs_is_json_array(response_payload):
    response = AgentResponse(**response_payload)
    assert isinstance(response.evidence_refs, tuple)
    wire = json.loads(response.model_dump_json())
    assert wire["evidence_refs"] == ["catalog:sku_A:price"]


def test_timestamps_are_serialized_as_utc(contract_cases):
    time_fields = {
        "CommentEvent": "received_at",
        "CommentDecision": "decided_at",
        "AgentResponse": "created_at",
        "SpeechTurn": "created_at",
        "AudioArtifact": "created_at",
    }
    for schema, payload in contract_cases:
        field = time_fields[schema.__name__]
        wire = json.loads(schema(**payload).model_dump_json())
        assert wire[field] == TIMESTAMP


def test_comment_reply_pipeline_carries_traceable_ids(
    comment_payload,
    decision_payload,
    response_payload,
    reply_turn_payload,
    audio_payload,
):
    """Sample valid exchange; the runtime must enforce these relationships."""
    comment = CommentEvent(**comment_payload)
    decision = CommentDecision(**decision_payload)
    response = AgentResponse(**response_payload)
    turn = SpeechTurn(**reply_turn_payload)
    audio = AudioArtifact(**audio_payload)

    assert {x.run_id for x in (comment, decision, response, turn, audio)} == {
        "demo_001"
    }
    assert decision.comment_id == response.comment_id == comment.comment_id
    assert response.viewer_id == comment.viewer_id
    assert turn.response_id == response.response_id
    assert audio.speech_turn_id == turn.speech_turn_id
    assert audio.response_id == response.response_id


def test_product_intro_audio_requires_no_agent_response(audio_payload):
    intro_turn = SpeechTurn(
        speech_turn_id="turn_intro_001",
        run_id="demo_001",
        speech_type="product_intro",
        sku_id="sku_A",
        text="Xin giới thiệu sản phẩm A.",
        response_id=None,
        script_ref="demo_scenario:intro_sku_A",
        priority=20,
        created_at=TIMESTAMP,
    )
    intro_audio_payload = audio_payload.copy()
    intro_audio_payload["speech_turn_id"] = intro_turn.speech_turn_id
    intro_audio_payload["response_id"] = None  # Required key, nullable value.

    intro_audio = AudioArtifact(**intro_audio_payload)
    assert intro_audio.response_id is None
    assert intro_audio.speech_turn_id == intro_turn.speech_turn_id
    wire = json.loads(intro_audio.model_dump_json())
    assert wire["response_id"] is None


def test_safe_fallback_is_script_backed():
    fallback = SpeechTurn(
        speech_turn_id="turn_fallback_001",
        run_id="demo_001",
        speech_type="safe_fallback",
        sku_id=None,
        text="Xin vui lòng chờ trong giây lát.",
        response_id=None,
        script_ref="demo_scenario:safe_wait",
        priority=100,
        created_at=TIMESTAMP,
    )
    assert SpeechTurn.model_validate_json(fallback.model_dump_json()) == fallback


def test_blocked_response_safe_fallback_trace_round_trip(response_payload, audio_payload):
    blocked_payload = {
        **response_payload,
        "response_id": "resp_blocked_001",
        "status": "blocked",
        "answer_text": None,
        "evidence_refs": [],
        "reason_code": "VERIFICATION_FAILED",
    }
    blocked = AgentResponse.model_validate(blocked_payload)

    fallback = SpeechTurn(
        speech_turn_id="turn_fallback_blocked_001",
        run_id=blocked.run_id,
        speech_type="safe_fallback",
        sku_id=None,
        text="Mình xin nhờ nhân viên kiểm tra lại nhé.",
        response_id=blocked.response_id,
        script_ref="demo_scenario:verification_fallback",
        priority=100,
        created_at=TIMESTAMP,
    )
    audio = AudioArtifact.model_validate({
        **audio_payload,
        "speech_turn_id": fallback.speech_turn_id,
        "response_id": fallback.response_id,
    })

    assert fallback.response_id == blocked.response_id == audio.response_id
    assert audio.speech_turn_id == fallback.speech_turn_id
    assert SpeechTurn.model_validate_json(fallback.model_dump_json()) == fallback
    assert AudioArtifact.model_validate_json(audio.model_dump_json()) == audio
    # Việc xác minh các ID thật sự tồn tại và script_ref được duyệt
    # là trách nhiệm service, không phải của schema.


def test_generic_answer_requires_faq_evidence(response_payload):
    general = {**response_payload, "resolved_sku_id": None}
    general["evidence_refs"] = ["faq:shipping_express"]
    assert AgentResponse.model_validate(general).evidence_refs == (
        "faq:shipping_express",
    )

    general["evidence_refs"] = []
    with pytest.raises(ValidationError, match="EVIDENCE_REQUIRED"):
        AgentResponse.model_validate(general)


def test_blocked_response_does_not_expose_unverified_evidence(response_payload):
    blocked = {
        **response_payload,
        "status": "blocked",
        "answer_text": None,
        "reason_code": "VERIFICATION_FAILED",
    }
    with pytest.raises(ValidationError, match="BLOCKED_RESPONSE_CANNOT_HAVE_EVIDENCE"):
        AgentResponse.model_validate(blocked)


def test_audio_filename_is_bound_to_audio_id(audio_payload):
    bad = {**audio_payload, "file_path": (
        "shared_data/runs/demo_001/step1_agent_audio/audio/other_audio.wav"
    )}
    with pytest.raises(ValidationError, match="AUDIO_FILENAME_ID_MISMATCH"):
        AudioArtifact.model_validate(bad)


def test_audio_contract_rejects_legacy_payload_without_speech_turn_id(
    audio_payload,
):
    legacy = audio_payload.copy()
    legacy.pop("speech_turn_id")
    with pytest.raises(ValidationError) as exc:
        AudioArtifact(**legacy)
    assert "speech_turn_id" in str(exc.value)


def test_wire_contract_forbids_unknown_fields(comment_payload):
    changed = {**comment_payload, "extra_field": "not in contract"}
    with pytest.raises(ValidationError):
        CommentEvent(**changed)
