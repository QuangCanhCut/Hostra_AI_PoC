import io
import json
import struct
import wave
from pathlib import Path

import pytest

from hostra_ai.core.schemas import AgentResponse
from hostra_ai.part1_agent_tts.speech_planner import PlanningError, SpeechAdmission, SpeechPlanner
from hostra_ai.part1_agent_tts.tts_provider import (MockTTSProvider, OpenAITTSProvider, TTSConfig,
    TTSError, TTSService, normalize_wav, validate_wav, load_tts_config, write_run_metadata)

ROOT = Path(__file__).resolve().parents[3]


def response(status='answered', run='RUN-001'):
    return AgentResponse(response_id='RESP-1', comment_id='CMT-1', run_id=run, viewer_id='VIEWER-1',
        resolved_sku_id='LAPTOP-ASUS-001', status=status,
        answer_text=None if status == 'blocked' else 'Giá trong phiên demo.',
        evidence_refs=() if status != 'answered' else ('catalog:LAPTOP-ASUS-001',),
        reason_code={'answered': None, 'blocked': 'UNSUPPORTED_REQUEST', 'clarification_needed': 'REFERENCE_AMBIGUOUS'}[status],
        created_at='2026-10-27T13:00:00Z')


def script(script_id, kind, sku=None, status='approved'):
    return {'script_id': script_id, 'speech_type': kind, 'sku_id': sku, 'text': 'Nội dung an toàn.',
            'approval': {'status': status, 'approved_by': 'fixture-reviewer', 'approved_at': '2026-10-27T00:00:00Z'}}


@pytest.fixture
def planner():
    return SpeechPlanner({'scripts': [script('INTRO', 'product_intro', 'LAPTOP-ASUS-001'),
                                      script('FALLBACK', 'safe_fallback')]})


def test_planning_and_approval(planner):
    for status in ('answered', 'clarification_needed'):
        turn = planner.from_response(response(status), run_id='RUN-001')
        assert turn.speech_type == 'comment_reply' and turn.text == response(status).answer_text
        assert turn.response_id == 'RESP-1'
    blocked = response('blocked')
    with pytest.raises(PlanningError, match='NO_APPROVED_FALLBACK'):
        planner.from_response(blocked, run_id='RUN-001')
    turn = planner.from_response(blocked, run_id='RUN-001', fallback_script_id='FALLBACK')
    assert turn.speech_type == 'safe_fallback' and turn.response_id == blocked.response_id
    with pytest.raises(PlanningError, match='RUN_MISMATCH'):
        planner.from_response(response(), run_id='RUN-002')
    with pytest.raises(PlanningError, match='ACTIVE_SKU_MISMATCH'):
        planner.product_intro('INTRO', run_id='RUN-001', active_sku_id='LAPTOP-LENOVO-002')
    with pytest.raises(PlanningError, match='SCRIPT_NOT_FOUND'):
        planner.product_intro('UNKNOWN', run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')
    with pytest.raises(PlanningError, match='DUPLICATE_SCRIPT_ID'):
        SpeechPlanner({'scripts': [script('X', 'safe_fallback'), script('X', 'safe_fallback')]})


def test_real_scripts_pending_and_conditions_fail_closed():
    planner = SpeechPlanner.from_file(ROOT / 'shared_data/inputs/approved_product_scripts.json')
    with pytest.raises(PlanningError, match='SCRIPT_NOT_APPROVED'):
        planner.product_intro('SCRIPT-ASUS-001', run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')
    item = script('I', 'product_intro', 'LAPTOP-ASUS-001')
    item['use_when'] = 'Requires operator review'
    planner = SpeechPlanner({'scripts': [item]})
    with pytest.raises(PlanningError, match='SCRIPT_CONDITIONS_NOT_VERIFIED'):
        planner.product_intro('I', run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')


def test_admission_order_duplicates_untrusted_and_one_time(planner, tmp_path):
    reply = planner.from_response(response(), run_id='RUN-001')
    intro = planner.product_intro('INTRO', run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')
    fallback = planner.from_response(response('blocked'), run_id='RUN-001', fallback_script_id='FALLBACK')
    forged = reply.model_copy(update={'text': 'Giá bịa đặt'})
    admission = SpeechAdmission(planner)
    results = admission.admit([intro, reply, fallback, reply, forged, {}], run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')
    assert [d.turn.speech_type for d in results if d.accepted] == ['safe_fallback', 'comment_reply', 'product_intro']
    assert {d.reason for d in results if not d.accepted} == {'DUPLICATE_TURN', 'INVALID_TURN'}
    cfg = TTSConfig('mock', 'fixture', 'test-voice')
    service = TTSService(admission, MockTTSProvider(), cfg, workspace=tmp_path)
    artifact = service.synthesize(reply)
    assert artifact.response_id == reply.response_id and artifact.duration_ms == 250
    assert validate_wav((tmp_path / artifact.file_path).read_bytes(), 16000) == 250
    assert type(artifact).model_validate_json(artifact.model_dump_json()) == artifact
    write_run_metadata(tmp_path, reply.run_id, [reply], [artifact])
    metadata = tmp_path / 'shared_data/runs/RUN-001/step1_agent_audio'
    assert json.loads((metadata / 'audio_artifacts.json').read_text(encoding='utf-8'))[0]['audio_id'] == artifact.audio_id
    with pytest.raises(TTSError, match='METADATA_WRITE_FAILED'):
        write_run_metadata(tmp_path, reply.run_id, [reply], [artifact])
    with pytest.raises(PlanningError, match='TURN_NOT_ADMITTED'):
        service.synthesize(reply)


def test_resampling_and_wav_rejection():
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(24000)
        wav.writeframes(struct.pack('<' + 'h' * 4800, *([1000, -500] * 2400)))
    data = normalize_wav(output.getvalue(), 16000)
    assert validate_wav(data, 16000) == 100
    with wave.open(io.BytesIO(data), 'rb') as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) == (1, 2, 16000, 1600)
        assert struct.unpack('<h', wav.readframes(1))[0] == 250
    for invalid in (b'', b'not wav', output.getvalue()[:-4]):
        with pytest.raises(TTSError):
            normalize_wav(invalid, 16000)


def test_openai_opt_in_and_injected_client():
    calls = []
    class AudioResponse:
        def read(self):
            return b'fixture'
    class Speech:
        def create(self, **kwargs):
            calls.append(kwargs)
            return AudioResponse()
    class Audio:
        speech = Speech()
    class Client:
        audio = Audio()
    provider = OpenAITTSProvider(client=Client())
    cfg = load_tts_config(ROOT / 'configs/app.yaml')
    with pytest.raises(TTSError, match='LIVE_API_NOT_ENABLED'):
        provider.synthesize('test', cfg)
    assert not calls
    cfg = TTSConfig('openai', 'configured-model', 'alloy', live_api_opt_in=True)
    assert provider.synthesize('test', cfg) == b'fixture'
    assert calls[0]['input'] == 'test' and calls[0]['response_format'] == 'wav'


def test_fallback_and_intro_produce_valid_audio(planner, tmp_path):
    turns = [planner.from_response(response('blocked'), run_id='RUN-001', fallback_script_id='FALLBACK'),
             planner.product_intro('INTRO', run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')]
    admission = SpeechAdmission(planner)
    decisions = admission.admit(turns, run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')
    service = TTSService(admission, MockTTSProvider(), TTSConfig('mock', 'fixture', 'fixture'), workspace=tmp_path)
    artifacts = [service.synthesize(d.turn) for d in decisions if d.accepted]
    assert artifacts[0].response_id == 'RESP-1' and artifacts[1].response_id is None
    assert all((tmp_path / artifact.file_path).exists() for artifact in artifacts)


def test_timeout_and_write_failure_do_not_create_artifact(planner, tmp_path, monkeypatch):
    admission = SpeechAdmission(planner)
    class TimeoutProvider:
        def synthesize(self, text, config):
            raise TimeoutError()
    cfg = TTSConfig('mock', 'fixture', 'fixture')
    first = planner.from_response(response(), run_id='RUN-001')
    admission.admit([first], run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')
    with pytest.raises(TTSError, match='SYNTHESIS_FAILED'):
        TTSService(admission, TimeoutProvider(), cfg, workspace=tmp_path).synthesize(first)
    second = planner.from_response(response(), run_id='RUN-001')
    admission.admit([second], run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')
    def deny(*args, **kwargs):
        raise OSError('write denied')
    monkeypatch.setattr('hostra_ai.part1_agent_tts.tts_provider.os.link', deny)
    with pytest.raises(TTSError, match='AUDIO_WRITE_FAILED'):
        TTSService(admission, MockTTSProvider(), cfg, workspace=tmp_path).synthesize(second)
    assert not list(tmp_path.rglob('*.wav')) and not list(tmp_path.rglob('*.tmp'))
