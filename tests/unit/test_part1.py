"""Unit tests for all five HOSTRA AI Part 1 data contracts."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from hostra_ai.core.schemas.part1 import (
    AgentResponse,
    AudioArtifact,
    CommentDecision,
    CommentEvent,
    SpeechTurn,
)


NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def make_comment(**changes):
    data = {
        "comment_id": "cmt_001",
        "run_id": "run_001",
        "viewer_id": "viewer_001",
        "source": "mock",
        "text": "  Cho mình hỏi giá?  ",
        "active_sku_id": "sku_A",
        "received_at": NOW,
    }
    data.update(changes)
    return CommentEvent(**data)


def make_decision(**changes):
    data = {
        "decision_id": "dec_001",
        "run_id": "run_001",
        "comment_id": "cmt_001",
        "action": "selected",
        "reason_code": None,
        "priority_score": 85,
        "duplicate_of": None,
        "policy_version": "policy_20261025",
        "decided_at": NOW,
    }
    data.update(changes)
    return CommentDecision(**data)


def make_response(**changes):
    data = {
        "response_id": "resp_001",
        "comment_id": "cmt_001",
        "run_id": "run_001",
        "viewer_id": "viewer_001",
        "resolved_sku_id": "sku_A",
        "status": "answered",
        "answer_text": "  Sản phẩm có giá theo catalog.  ",
        "evidence_refs": ("catalog:sku_A:price",),
        "reason_code": None,
        "created_at": NOW,
    }
    data.update(changes)
    return AgentResponse(**data)


def make_turn(**changes):
    data = {
        "speech_turn_id": "turn_001",
        "run_id": "run_001",
        "speech_type": "comment_reply",
        "sku_id": "sku_A",
        "text": "  Sản phẩm có giá theo catalog.  ",
        "response_id": "resp_001",
        "script_ref": None,
        "priority": 80,
        "created_at": NOW,
    }
    data.update(changes)
    return SpeechTurn(**data)


def make_audio(**changes):
    data = {
        "audio_id": "audio_001",
        "speech_turn_id": "turn_001",
        "response_id": "resp_001",
        "run_id": "run_001",
        "voice_id": "voice_001",
        "file_path": "shared_data/runs/run_001/step1_agent_audio/audio/audio_001.wav",
        "format": "wav",
        "codec": "pcm_s16le",
        "sample_rate_hz": 24000,
        "channels": 1,
        "duration_ms": 3200,
        "created_at": NOW,
    }
    data.update(changes)
    return AudioArtifact(**data)


# ---------------------------------------------------------------------------
# CommentEvent
# ---------------------------------------------------------------------------


def test_comment_normalizes_text_and_utc():
    local_time = datetime(2026, 10, 25, 19, 0, tzinfo=timezone(timedelta(hours=7)))
    value = make_comment(received_at=local_time)
    assert value.text == "Cho mình hỏi giá?"
    assert value.received_at == NOW
    assert value.received_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    "bad",
    [
        {"text": "   "},
        {"source": "tiktok"},
        {"active_sku_id": ""},
        {"comment_id": "bad id"},
        {"received_at": datetime(2026, 10, 25, 12)},
    ],
)
def test_comment_rejects_invalid_values(bad):
    with pytest.raises(ValidationError):
        make_comment(**bad)


def test_comment_requires_active_sku_and_forbids_extra():
    with pytest.raises(ValidationError):
        CommentEvent(**{k: v for k, v in make_comment().model_dump().items() if k != "active_sku_id"})
    with pytest.raises(ValidationError):
        make_comment(unexpected=True)


# ---------------------------------------------------------------------------
# CommentDecision
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "action,reason,duplicate",
    [
        ("selected", None, None),
        ("deferred", "LOW_PRIORITY", None),
        ("deferred", "QUEUE_BUSY", None),
        ("deferred", "RATE_LIMITED", None),
        ("skipped", "SPAM", None),
        ("skipped", "OFF_TOPIC", None),
        ("skipped", "EXPIRED", None),
        ("skipped", "DUPLICATE", "cmt_000"),
        ("escalated", "HUMAN_REQUIRED", None),
    ],
)
def test_decision_valid_action_reason_pairs(action, reason, duplicate):
    result = make_decision(action=action, reason_code=reason, duplicate_of=duplicate)
    assert result.action == action


@pytest.mark.parametrize(
    "bad",
    [
        {"action": "selected", "reason_code": "SPAM"},
        {"action": "deferred", "reason_code": None},
        {"action": "deferred", "reason_code": "SPAM"},
        {"action": "skipped", "reason_code": "LOW_PRIORITY"},
        {"action": "escalated", "reason_code": "OFF_TOPIC"},
        {"action": "skipped", "reason_code": "DUPLICATE", "duplicate_of": None},
        {"action": "skipped", "reason_code": "DUPLICATE", "duplicate_of": "cmt_001"},
        {"action": "selected", "duplicate_of": "cmt_000"},
        {"priority_score": -1},
        {"priority_score": 101},
        {"priority_score": True},
        {"policy_version": ""},
    ],
)
def test_decision_rejects_inconsistent_data(bad):
    with pytest.raises(ValidationError):
        make_decision(**bad)


def test_decision_normalizes_timezone_and_is_frozen():
    local = datetime(2026, 10, 25, 19, 0, tzinfo=timezone(timedelta(hours=7)))
    decision = make_decision(decided_at=local)
    assert decision.decided_at.utcoffset() == timedelta(0)
    with pytest.raises(ValidationError):
        decision.action = "skipped"


# ---------------------------------------------------------------------------
# AgentResponse
# ---------------------------------------------------------------------------


def test_agent_answer_requires_evidence_for_specific_sku():
    assert make_response().answer_text == "Sản phẩm có giá theo catalog."
    with pytest.raises(ValidationError):
        make_response(evidence_refs=())


def test_agent_answer_without_sku_still_requires_evidence():
    with pytest.raises(ValidationError, match="EVIDENCE_REQUIRED"):
        make_response(resolved_sku_id=None, evidence_refs=())


def test_agent_general_policy_answer_uses_faq_evidence():
    result = make_response(
        resolved_sku_id=None,
        answer_text="Shop hỗ trợ giao hỏa tốc theo chính sách.",
        evidence_refs=("faq:shipping_express",),
    )
    assert result.status == "answered"
    assert result.evidence_refs == ("faq:shipping_express",)


def test_agent_clarification_is_valid():
    result = make_response(
        status="clarification_needed",
        answer_text="Bạn muốn hỏi mẫu nào?",
        reason_code="REFERENCE_AMBIGUOUS",
        resolved_sku_id=None,
        evidence_refs=(),
    )
    assert result.answer_text == "Bạn muốn hỏi mẫu nào?"


def test_agent_blocked_requires_null_text_and_block_reason():
    blocked = make_response(
        status="blocked",
        answer_text=None,
        reason_code="VERIFICATION_FAILED",
        evidence_refs=(),
    )
    assert blocked.answer_text is None
    with pytest.raises(ValidationError):
        make_response(status="blocked", reason_code="VERIFICATION_FAILED")
    with pytest.raises(ValidationError):
        make_response(status="blocked", answer_text=None, reason_code="DETAIL_MISSING")
    with pytest.raises(ValidationError, match="BLOCKED_RESPONSE_CANNOT_HAVE_EVIDENCE"):
        make_response(
            status="blocked",
            answer_text=None,
            reason_code="VERIFICATION_FAILED",
            evidence_refs=("catalog:sku_A:price",),
        )


@pytest.mark.parametrize(
    "evidence",
    [
        ("",),
        ("same", " same "),
        ("x" * 129,),
        ("catalog:sku_A\ncorrupted",),
        ("faq:shipping\tcorrupted",),
        ("faq:shipping\x7fcorrupted",),
    ],
)
def test_agent_rejects_invalid_evidence(evidence):
    with pytest.raises(ValidationError):
        make_response(evidence_refs=evidence)


def test_agent_json_roundtrip():
    source = make_response()
    recovered = AgentResponse.model_validate_json(source.model_dump_json())
    assert recovered == source


# ---------------------------------------------------------------------------
# SpeechTurn
# ---------------------------------------------------------------------------


def test_comment_reply_and_clarification_use_agent_response():
    turn = make_turn()
    assert turn.text == "Sản phẩm có giá theo catalog."
    clarification = make_turn(sku_id=None, text="Bạn muốn hỏi mẫu nào?")
    assert clarification.sku_id is None


def test_product_intro_uses_approved_script_reference():
    turn = make_turn(
        speech_type="product_intro",
        response_id=None,
        script_ref="demo_scenario:intro_sku_A",
        text="Đây là sản phẩm A.",
    )
    assert turn.script_ref == "demo_scenario:intro_sku_A"


def test_safe_fallback_may_have_no_sku():
    turn = make_turn(
        speech_type="safe_fallback",
        sku_id=None,
        response_id=None,
        script_ref="demo_scenario:safe_wait",
        priority=100,
    )
    assert turn.priority == 100


def test_safe_fallback_can_trace_blocked_response():
    blocked = make_response(
        status="blocked",
        answer_text=None,
        reason_code="VERIFICATION_FAILED",
        evidence_refs=(),
    )
    turn = make_turn(
        speech_type="safe_fallback",
        response_id=blocked.response_id,
        sku_id=None,
        text="Mình xin nhờ nhân viên kiểm tra lại thông tin nhé.",
        script_ref="demo_scenario:verification_fallback",
    )
    assert turn.response_id == blocked.response_id
    assert turn.script_ref == "demo_scenario:verification_fallback"


@pytest.mark.parametrize(
    "bad",
    [
        {"speech_type": "comment_reply", "response_id": None},
        {"speech_type": "comment_reply", "script_ref": "intro"},
        {"speech_type": "product_intro", "script_ref": "intro"},
        {"speech_type": "product_intro", "response_id": None, "script_ref": None},
        {"speech_type": "product_intro", "response_id": None, "script_ref": "intro", "sku_id": None},
        {"speech_type": "safe_fallback", "script_ref": None},
        {"speech_type": "safe_fallback", "response_id": None, "script_ref": None},
        {"text": "   "},
        {"text": "x" * 501},
        {"priority": 101},
        {"priority": -1},
        {"priority": True},
        {"script_ref": "bad\nref"},
        {"script_ref": "bad\x7fref"},
    ],
)
def test_speech_turn_rejects_inconsistent_data(bad):
    with pytest.raises(ValidationError):
        make_turn(**bad)


def test_speech_turn_requires_explicit_nullable_source_fields():
    payload = make_turn().model_dump()
    payload.pop("script_ref")
    with pytest.raises(ValidationError):
        SpeechTurn(**payload)


# ---------------------------------------------------------------------------
# AudioArtifact
# ---------------------------------------------------------------------------


def test_audio_from_agent_response():
    audio = make_audio()
    assert audio.speech_turn_id == "turn_001"
    assert audio.response_id == "resp_001"


def test_audio_from_product_intro_without_agent_response():
    audio = make_audio(response_id=None)
    assert audio.response_id is None
    payload = make_audio().model_dump()
    payload.pop("response_id")
    with pytest.raises(ValidationError, match="response_id"):
        AudioArtifact(**payload)
    payload["response_id"] = None
    assert AudioArtifact(**payload).response_id is None


def test_audio_can_trace_blocked_fallback_without_speaking_blocked_text():
    audio = make_audio(response_id="resp_blocked_001")
    assert audio.response_id == "resp_blocked_001"
    # Nguồn text thực sự phải là script fallback đã duyệt:
    # việc đối chiếu SpeechTurn/AgentResponse thuộc service.


@pytest.mark.parametrize(
    "filename",
    [
        "audio 001.wav",
        "audio'001.wav",
        "audio;001.wav",
        "audio\x7f001.wav",
    ],
)
def test_audio_rejects_unsafe_basename(filename):
    with pytest.raises(ValidationError, match="INVALID_AUDIO_FILE_PATH"):
        make_audio(
            file_path=f"shared_data/runs/run_001/step1_agent_audio/audio/{filename}"
        )


def test_audio_filename_must_match_audio_id():
    with pytest.raises(ValidationError, match="AUDIO_FILENAME_ID_MISMATCH"):
        make_audio(
            file_path="shared_data/runs/run_001/step1_agent_audio/audio/other_001.wav"
        )


@pytest.mark.parametrize(
    "bad",
    [
        {"file_path": "other_folder/audio_001.wav"},
        {"file_path": "shared_data/runs/run_other/step1_agent_audio/audio/a.wav"},
        {"file_path": "shared_data/runs/run_001/step1_agent_audio/other/a.wav"},
        {"file_path": "shared_data/runs/run_001/step1_agent_audio/audio/sub/a.wav"},
        {"file_path": "shared_data/runs/run_001/step1_agent_audio/audio/../a.wav"},
        {"file_path": "/shared_data/runs/run_001/step1_agent_audio/audio/a.wav"},
        {"file_path": "shared_data\\runs\\run_001\\step1_agent_audio\\audio\\a.wav"},
        {"file_path": "shared_data/runs/run_001/step1_agent_audio/audio/a.mp3"},
        {"format": "mp3"},
        {"codec": "mp3"},
        {"channels": 2},
        {"sample_rate_hz": 7999},
        {"sample_rate_hz": 96001},
        {"duration_ms": 0},
        {"duration_ms": True},
        {"speech_turn_id": ""},
    ],
)
def test_audio_rejects_invalid_metadata(bad):
    with pytest.raises(ValidationError):
        make_audio(**bad)


def test_audio_requires_speech_turn_and_forbids_extra():
    payload = make_audio().model_dump()
    payload.pop("speech_turn_id")
    with pytest.raises(ValidationError):
        AudioArtifact(**payload)
    with pytest.raises(ValidationError):
        make_audio(unexpected=True)


def test_audio_json_roundtrip():
    audio = make_audio(response_id=None)
    assert AudioArtifact.model_validate_json(audio.model_dump_json()) == audio
