
import json

import pytest
from pydantic import ValidationError

from hostra_ai.core.schemas import AudioArtifact


@pytest.fixture
def audio_payload():
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
        "created_at": "2026-10-23T02:30:00Z",
    }


def test_contract_required_fields(audio_payload):
    artifact = AudioArtifact(**audio_payload)

    assert set(artifact.model_dump().keys()) == {
        "audio_id",
        "response_id",
        "run_id",
        "voice_id",
        "file_path",
        "format",
        "codec",
        "sample_rate_hz",
        "channels",
        "duration_ms",
        "created_at",
    }


def test_contract_json_round_trip(audio_payload):
    artifact = AudioArtifact(**audio_payload)

    serialized = artifact.model_dump_json()
    restored = AudioArtifact.model_validate_json(serialized)

    assert restored == artifact


def test_contract_json_compatible(audio_payload):
    artifact = AudioArtifact(**audio_payload)

    payload = artifact.model_dump(mode="json")

    assert isinstance(payload["created_at"], str)
    assert json.loads(json.dumps(payload)) == payload


def test_contract_missing_field_rejected(audio_payload):
    del audio_payload["response_id"]

    with pytest.raises(ValidationError):
        AudioArtifact(**audio_payload)


def test_contract_unknown_field_rejected(audio_payload):
    audio_payload["tts_status"] = "success"

    with pytest.raises(ValidationError):
        AudioArtifact(**audio_payload)
