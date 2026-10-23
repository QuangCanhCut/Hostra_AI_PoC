
from datetime import timezone

import pytest
from pydantic import ValidationError

from hostra_ai.core.schemas import AudioArtifact


@pytest.fixture
def valid_audio():
    return {
        "audio_id": "aud_001",
        "response_id": "resp_001",
        "run_id": "demo_001",
        "voice_id": "demo_voice_01",
        "file_path": "outputs/audio/aud_001.wav",
        "format": "wav",
        "codec": "pcm_s16le",
        "sample_rate_hz": 24000,
        "channels": 1,
        "duration_ms": 3200,
        "created_at": "2026-10-23T09:30:00+07:00",
    }


def test_valid_audio_artifact(valid_audio):
    artifact = AudioArtifact(**valid_audio)

    assert artifact.audio_id == "aud_001"
    assert artifact.duration_ms == 3200


def test_timestamp_normalized_to_utc(valid_audio):
    artifact = AudioArtifact(**valid_audio)

    assert artifact.created_at.tzinfo == timezone.utc
    assert artifact.created_at.hour == 2
    assert artifact.created_at.minute == 30


@pytest.mark.parametrize(
    "field,value",
    [
        ("audio_id", "invalid/id"),
        ("voice_id", ""),
        ("file_path", "../secret.wav"),
        ("file_path", "outputs/../secret.wav"),
        ("file_path", r"C:\audio\test.wav"),
        ("file_path", "/tmp/test.wav"),
        ("file_path", "outputs/audio/test.mp3"),
        ("format", "mp3"),
        ("codec", "mp3"),
        ("sample_rate_hz", 4000),
        ("channels", 2),
        ("duration_ms", 0),
        ("created_at", "2026-10-23T09:30:00"),
    ],
)
def test_invalid_audio_artifact(valid_audio, field, value):
    payload = valid_audio.copy()
    payload[field] = value

    with pytest.raises(ValidationError):
        AudioArtifact(**payload)


def test_extra_field_rejected(valid_audio):
    payload = {
        **valid_audio,
        "unexpected_field": "invalid",
    }

    with pytest.raises(ValidationError):
        AudioArtifact(**payload)


def test_model_is_frozen(valid_audio):
    artifact = AudioArtifact(**valid_audio)

    with pytest.raises(ValidationError):
        artifact.duration_ms = 5000
