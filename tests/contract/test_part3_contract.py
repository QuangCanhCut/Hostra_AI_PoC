
"""Contract tests: Public API và Part 2 -> Part 3 handoff."""

import pytest

from hostra_ai.core.schemas import (
    AuditRecord,
    RunManifest,
    TimelineEvent,
    VideoArtifact,
)


@pytest.fixture
def records():

    # ========================================================
    # RUN MANIFEST
    # ========================================================

    manifest = RunManifest.model_validate({
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
    })

    # ========================================================
    # VIDEO ARTIFACT - PART 2
    # ========================================================

    # Metadata giả lập từ Part 2.
    # Schema test không cần file MP4 thật.

    video = VideoArtifact.model_validate({
        "video_id": "vid-01",
        "render_job_id": "job-01",
        "audio_id": "audio-01",
        "run_id": "run-01",
        "speech_turn_id": "turn-01",
        "file_path": (
            "shared_data/runs/run-01/"
            "step2_lipsync/overlays/vid-01.mp4"
        ),
        "format": "mp4",
        "codec": "h264",
        "duration_ms": 3000,
        "width_px": 1280,
        "height_px": 720,
        "fps": 25.0,
        "has_audio_track": False,
        "created_at": "2026-10-25T10:00:01Z",
    })

    # ========================================================
    # TIMELINE EVENT
    # ========================================================

    # FrameMapper đã chuyển:
    # 1000ms -> frame 25
    # 4000ms -> frame 100
    # tại 25 FPS.

    event = TimelineEvent.model_validate({
        "event_id": "evt-01",
        "run_id": "run-01",
        "event_type": "clip",
        "start_ms": 1000,
        "end_ms": 4000,
        "start_frame": 25,
        "end_frame": 100,
        "comment_id": "cmt-01",
        "speech_turn_id": "turn-01",
        "audio_id": "audio-01",
        "video_id": "vid-01",
        "sku_id": "sku-01",
        "created_at": "2026-10-25T10:00:02Z",
    })

    # ========================================================
    # AUDIT RECORD
    # ========================================================

    audit = AuditRecord.model_validate({
        "audit_id": "audit-01",
        "run_id": "run-01",
        "correlation_id": "evt-01",
        "module": "compositor",
        "action": "clip_composed",
        "entity_type": "timeline_event",
        "entity_id": "evt-01",
        "outcome": "succeeded",
        "reason_code": None,
        "created_at": "2026-10-25T10:00:03Z",
    })

    return manifest, video, event, audit


# ============================================================
# PUBLIC EXPORTS
# ============================================================

def test_public_exports():
    assert RunManifest.__name__ == "RunManifest"
    assert TimelineEvent.__name__ == "TimelineEvent"
    assert AuditRecord.__name__ == "AuditRecord"
    assert VideoArtifact.__name__ == "VideoArtifact"


# ============================================================
# SCHEMA FIELD STABILITY
# ============================================================

def test_part3_field_sets():

    assert set(RunManifest.model_fields) == {
        "run_id",
        "base_video_path",
        "base_duration_ms",
        "fps",
        "width_px",
        "height_px",
        "active_sku_id",
        "avatar_id",
        "license_ref",
        "execution_mode",
        "output_video_path",
        "timeline_start_at",
        "created_at",
    }

    assert set(TimelineEvent.model_fields) == {
        "event_id",
        "run_id",
        "event_type",
        "start_ms",
        "end_ms",
        "start_frame",
        "end_frame",
        "comment_id",
        "speech_turn_id",
        "audio_id",
        "video_id",
        "sku_id",
        "created_at",
    }

    assert set(AuditRecord.model_fields) == {
        "audit_id",
        "run_id",
        "correlation_id",
        "module",
        "action",
        "entity_type",
        "entity_id",
        "outcome",
        "reason_code",
        "created_at",
    }


# ============================================================
# JSON ROUND-TRIP
# ============================================================

@pytest.mark.parametrize("index", [0, 2, 3])
def test_part3_json_roundtrip(records, index):

    model = records[index]

    restored = type(model).model_validate_json(
        model.model_dump_json()
    )

    assert restored == model


# ============================================================
# PART 2 -> PART 3 HANDOFF
# ============================================================

def test_video_artifact_handoff_example(records):

    manifest, video, event, audit = records

    assert (
        manifest.run_id
        == video.run_id
        == event.run_id
        == audit.run_id
    )

    assert (
        event.speech_turn_id,
        event.audio_id,
        event.video_id,
    ) == (
        video.speech_turn_id,
        video.audio_id,
        video.video_id,
    )

    # 75 frames ở 25 FPS tương ứng 3000ms.
    assert event.end_frame - event.start_frame == 75

    assert (
        event.end_ms - event.start_ms
        == video.duration_ms
    )

    assert audit.correlation_id == event.event_id


# ============================================================
# BOUNDARY FIELD PRESERVATION
# ============================================================

def test_new_boundary_fields_are_preserved(records):

    manifest, _, event, _ = records

    manifest_json = manifest.model_dump(mode="json")
    event_json = event.model_dump(mode="json")

    assert "timeline_start_at" in manifest_json

    assert event_json["start_frame"] == 25
    assert event_json["end_frame"] == 100


# ============================================================
# NULL SERIALIZATION
# ============================================================

def test_explicit_null_remains_in_payload(records):

    _, _, event, audit = records

    assert "comment_id" in event.model_dump(mode="json")

    assert "reason_code" in audit.model_dump(mode="json")


# ============================================================
# VALIDATION BOUNDARIES
# ============================================================

def test_cross_record_integrity_belongs_to_service(records):

    _, video, event, _ = records

    wrong_reference = event.model_dump(mode="json")

    wrong_reference["video_id"] = "vid-other"

    # Schema chỉ kiểm tra bản ghi độc lập.
    # Service phải phát hiện VideoArtifact không khớp.

    valid_shape = TimelineEvent.model_validate(
        wrong_reference
    )

    assert valid_shape.video_id != video.video_id


def test_manifest_does_not_require_media_file(records):

    manifest, _, _, _ = records

    data = manifest.model_dump(mode="json")

    data["base_video_path"] = (
        "shared_data/inputs/does_not_exist.mp4"
    )

    model = RunManifest.model_validate(data)

    assert model.base_video_path.endswith(".mp4")
