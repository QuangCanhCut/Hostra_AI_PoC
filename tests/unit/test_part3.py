
"""Unit tests Part 3: field bounds, invariants, timestamps, paths."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from hostra_ai.core.schemas.part3 import (
    AuditRecord,
    RunManifest,
    TimelineEvent,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def manifest_data():
    return {
        "run_id": "run-01",
        "base_video_path": "shared_data/inputs/base_operator.mp4",
        "base_duration_ms": 60_000,
        "fps": 25.0,
        "width_px": 1280,
        "height_px": 720,
        "active_sku_id": "sku-01",
        "avatar_id": "avatar-01",
        "license_ref": "license-01",
        "execution_mode": "pre_rendered",
        "output_video_path": (
            "shared_data/runs/run-01/"
            "step3_final/hostra_demo.mp4"
        ),
        "timeline_start_at": "2026-10-25T10:00:00+07:00",
        "created_at": "2026-10-25T10:10:00+07:00",
    }


@pytest.fixture
def event_data():
    return {
        "event_id": "evt-01",
        "run_id": "run-01",
        "event_type": "clip",
        "start_ms": 1001,
        "end_ms": 4000,
        "start_frame": 26,
        "end_frame": 100,
        "comment_id": "cmt-01",
        "speech_turn_id": "turn-01",
        "audio_id": "audio-01",
        "video_id": "vid-01",
        "sku_id": "sku-01",
        "created_at": "2026-10-25T10:00:01Z",
    }


@pytest.fixture
def audit_data():
    return {
        "audit_id": "audit-01",
        "run_id": "run-01",
        "correlation_id": "evt-01",
        "module": "teleprompter",
        "action": "operator_confirm_simulated",
        "entity_type": "speech_turn",
        "entity_id": "turn-01",
        "outcome": "succeeded",
        "reason_code": None,
        "created_at": "2026-10-25T10:00:02Z",
    }


# ============================================================
# RUN MANIFEST
# ============================================================

def test_manifest_has_distinct_timeline_anchor(manifest_data):
    obj = RunManifest.model_validate(manifest_data)

    assert obj.timeline_start_at.utcoffset() == timedelta(0)
    assert obj.created_at.utcoffset() == timedelta(0)

    # Mock run: manifest có thể tạo sau mốc kịch bản.
    assert obj.timeline_start_at < obj.created_at


@pytest.mark.parametrize(
    "mode",
    ["pre_rendered", "mock"],
)
def test_manifest_valid_modes(manifest_data, mode):
    manifest_data["execution_mode"] = mode

    assert (
        RunManifest.model_validate(manifest_data).execution_mode
        == mode
    )


@pytest.mark.parametrize(
    "mode",
    ["live", "realtime", None, ""],
)
def test_manifest_invalid_modes(manifest_data, mode):
    manifest_data["execution_mode"] = mode

    with pytest.raises(ValidationError):
        RunManifest.model_validate(manifest_data)


@pytest.mark.parametrize(
    "source",
    [
        "/shared_data/inputs/base_operator.mp4",
        "shared_data/inputs/../base_operator.mp4",
        "shared_data/inputs/sub/base_operator.mp4",
        "shared_data//inputs/base_operator.mp4",
        "shared_data\\inputs\\base_operator.mp4",
        "shared_data/inputs/bad:name.mp4",
        "shared_data/inputs/bad\nname.mp4",
        "shared_data/inputs/bad\tname.mp4",
        "shared_data/inputs/bad\rname.mp4",
        "shared_data/inputs/bad\x7fname.mp4",
        "shared_data/inputs/base_operator.MP4",
        " shared_data/inputs/base_operator.mp4",
    ],
)
def test_manifest_rejects_unsafe_source(
    manifest_data,
    source,
):
    manifest_data["base_video_path"] = source

    with pytest.raises(ValidationError):
        RunManifest.model_validate(manifest_data)


@pytest.mark.parametrize(
    "path",
    [
        "shared_data/runs/other/step3_final/hostra_demo.mp4",
        "shared_data/runs/run-01/step2_lipsync/hostra_demo.mp4",
        "shared_data/runs/run-01/step3_final/../hostra_demo.mp4",
        "shared_data/runs/run-01/step3_final/hostra_demo.mp4\n",
        "shared_data/runs/run-01/step3_final/hostra:demo.mp4",
    ],
)
def test_manifest_rejects_unsafe_destination(
    manifest_data,
    path,
):
    manifest_data["output_video_path"] = path

    with pytest.raises(ValidationError):
        RunManifest.model_validate(manifest_data)


@pytest.mark.parametrize(
    "fps",
    [
        0,
        -1,
        121,
        float("nan"),
        float("inf"),
        -float("inf"),
    ],
)
def test_manifest_rejects_invalid_fps(
    manifest_data,
    fps,
):
    manifest_data["fps"] = fps

    with pytest.raises(ValidationError):
        RunManifest.model_validate(manifest_data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("base_duration_ms", 0),
        ("base_duration_ms", True),
        ("base_duration_ms", "1000"),
        ("width_px", 20),
        ("height_px", 5000),
        ("run_id", "../invalid"),
        ("license_ref", ""),
    ],
)
def test_manifest_rejects_invalid_fields(
    manifest_data,
    field,
    value,
):
    manifest_data[field] = value

    with pytest.raises(ValidationError):
        RunManifest.model_validate(manifest_data)


@pytest.mark.parametrize(
    "field",
    ["created_at", "timeline_start_at"],
)
def test_manifest_requires_aware_datetimes(
    manifest_data,
    field,
):
    manifest_data[field] = "2026-10-25T10:00:00"

    with pytest.raises(ValidationError):
        RunManifest.model_validate(manifest_data)


def test_manifest_requires_timeline_anchor_key(manifest_data):
    manifest_data.pop("timeline_start_at")

    with pytest.raises(ValidationError):
        RunManifest.model_validate(manifest_data)


# ============================================================
# TIMELINE EVENT
# ============================================================

def test_timeline_valid_clip_preserves_boundaries(event_data):
    event = TimelineEvent.model_validate(event_data)

    assert (event.start_ms, event.end_ms) == (1001, 4000)
    assert (event.start_frame, event.end_frame) == (26, 100)


def test_timeline_clip_may_not_have_comment(event_data):
    event_data["comment_id"] = None

    assert (
        TimelineEvent.model_validate(event_data).comment_id
        is None
    )


def test_timeline_valid_pause(event_data):
    event_data.update(
        event_type="pause",
        comment_id=None,
        speech_turn_id=None,
        audio_id=None,
        video_id=None,
        sku_id=None,
    )

    model = TimelineEvent.model_validate(event_data)

    assert model.event_type == "pause"


@pytest.mark.parametrize(
    ("start_frame", "end_frame"),
    [
        (10, 10),
        (20, 10),
        (-1, 10),
        (True, 10),
        (1, 1.5),
        (1, "5"),
    ],
)
def test_timeline_rejects_invalid_frame_range(
    event_data,
    start_frame,
    end_frame,
):
    event_data.update(
        start_frame=start_frame,
        end_frame=end_frame,
    )

    with pytest.raises(ValidationError):
        TimelineEvent.model_validate(event_data)


@pytest.mark.parametrize(
    ("start_ms", "end_ms"),
    [
        (1000, 1000),
        (2000, 1000),
        (-1, 1000),
        (True, 1000),
    ],
)
def test_timeline_rejects_invalid_time_range(
    event_data,
    start_ms,
    end_ms,
):
    event_data.update(
        start_ms=start_ms,
        end_ms=end_ms,
    )

    with pytest.raises(ValidationError):
        TimelineEvent.model_validate(event_data)


@pytest.mark.parametrize(
    "field",
    ["speech_turn_id", "audio_id", "video_id"],
)
def test_clip_requires_media_references(
    event_data,
    field,
):
    event_data[field] = None

    with pytest.raises(ValidationError):
        TimelineEvent.model_validate(event_data)


@pytest.mark.parametrize(
    "field",
    [
        "comment_id",
        "speech_turn_id",
        "audio_id",
        "video_id",
        "sku_id",
    ],
)
def test_pause_forbids_all_references(
    event_data,
    field,
):
    event_data.update(
        event_type="pause",
        comment_id=None,
        speech_turn_id=None,
        audio_id=None,
        video_id=None,
        sku_id=None,
    )

    event_data[field] = "unexpected-01"

    with pytest.raises(ValidationError):
        TimelineEvent.model_validate(event_data)


@pytest.mark.parametrize(
    "field",
    ["comment_id", "start_frame", "end_frame"],
)
def test_timeline_required_keys(
    event_data,
    field,
):
    event_data.pop(field)

    with pytest.raises(ValidationError):
        TimelineEvent.model_validate(event_data)


# ============================================================
# AUDIT RECORD
# ============================================================

def test_audit_success_without_reason(audit_data):
    obj = AuditRecord.model_validate(audit_data)

    assert obj.reason_code is None
    assert obj.action == "operator_confirm_simulated"


@pytest.mark.parametrize(
    "outcome",
    ["blocked", "failed"],
)
def test_audit_failure_needs_reason(
    audit_data,
    outcome,
):
    audit_data["outcome"] = outcome

    with pytest.raises(ValidationError):
        AuditRecord.model_validate(audit_data)

    audit_data["reason_code"] = "OPERATOR_NOT_CONFIRMED"

    assert (
        AuditRecord.model_validate(audit_data).reason_code
        == "OPERATOR_NOT_CONFIRMED"
    )


def test_audit_success_forbids_reason(audit_data):
    audit_data["reason_code"] = "NOT_NEEDED"

    with pytest.raises(ValidationError):
        AuditRecord.model_validate(audit_data)


@pytest.mark.parametrize(
    "code",
    [
        "lowercase",
        "Bad_Code",
        "CODE-WITH-DASH",
        "",
    ],
)
def test_audit_rejects_invalid_reason(
    audit_data,
    code,
):
    audit_data.update(
        outcome="blocked",
        reason_code=code,
    )

    with pytest.raises(ValidationError):
        AuditRecord.model_validate(audit_data)


# ============================================================
# COMMON PROPERTIES
# ============================================================

@pytest.mark.parametrize(
    ("fixture_name", "model_type"),
    [
        ("manifest_data", RunManifest),
        ("event_data", TimelineEvent),
        ("audit_data", AuditRecord),
    ],
)
def test_rejects_extra_fields(
    request,
    fixture_name,
    model_type,
):
    payload = request.getfixturevalue(fixture_name)
    payload["unknown"] = True

    with pytest.raises(ValidationError):
        model_type.model_validate(payload)


@pytest.mark.parametrize(
    ("fixture_name", "model_type"),
    [
        ("manifest_data", RunManifest),
        ("event_data", TimelineEvent),
        ("audit_data", AuditRecord),
    ],
)
def test_models_are_frozen(
    request,
    fixture_name,
    model_type,
):
    obj = model_type.model_validate(
        request.getfixturevalue(fixture_name)
    )

    with pytest.raises(ValidationError):
        obj.run_id = "modified"


@pytest.mark.parametrize(
    ("fixture_name", "model_type"),
    [
        ("manifest_data", RunManifest),
        ("event_data", TimelineEvent),
        ("audit_data", AuditRecord),
    ],
)
def test_json_round_trip(
    request,
    fixture_name,
    model_type,
):
    obj = model_type.model_validate(
        request.getfixturevalue(fixture_name)
    )

    restored = model_type.model_validate_json(
        obj.model_dump_json()
    )

    assert restored == obj
