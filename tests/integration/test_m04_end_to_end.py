import json
from pathlib import Path

import pytest

from hostra_ai.core.schemas import CommentEvent, SpeechTurn
from hostra_ai.part1_agent_tts.knowledge_engine import KnowledgeEngine
from hostra_ai.part1_agent_tts.verified_agent import VerifiedAgent
from hostra_ai.part1_agent_tts.speech_planner import PlanningError, SpeechAdmission, SpeechPlanner
from hostra_ai.part1_agent_tts.tts_provider import MockTTSProvider, TTSConfig, TTSService, TTSError

ROOT = Path(__file__).resolve().parents[2]


def test_verified_response_to_wav_and_pending_fallback(tmp_path):
    inputs = ROOT / 'shared_data/inputs'
    events = [CommentEvent.model_validate(x) for x in json.loads((inputs / 'mock_comments.json').read_text(encoding='utf-8'))]
    agent = VerifiedAgent(KnowledgeEngine(inputs / 'catalog_skus.json', inputs / 'product_faq.md'))
    planner = SpeechPlanner.from_file(inputs / 'approved_product_scripts.json')
    admission = SpeechAdmission(planner)
    service = TTSService(admission, MockTTSProvider(), TTSConfig('mock', 'fixture', 'fixture-voice'), workspace=tmp_path)
    first = agent.process_comment(events[0])
    clarification = agent.process_comment(events[2].model_copy(update={'viewer_id': 'NEW'}))
    assert first.status == 'answered' and clarification.status == 'clarification_needed'
    turns = [planner.from_response(r, run_id='RUN-001') for r in (first, clarification)]
    for decision in admission.admit(turns, run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001'):
        assert decision.accepted
        assert SpeechTurn.model_validate_json(decision.turn.model_dump_json()) == decision.turn
        artifact = service.synthesize(decision.turn)
        assert artifact.run_id == decision.turn.run_id
        assert artifact.response_id == decision.turn.response_id
        assert (tmp_path / artifact.file_path).is_file()
    blocked = agent.process_comment(events[10])
    assert blocked.status == 'blocked'
    with pytest.raises(PlanningError, match='SCRIPT_NOT_APPROVED'):
        planner.from_response(blocked, run_id='RUN-001', fallback_script_id='SCRIPT-FALLBACK-002')


@pytest.mark.parametrize('payload', [b'', b'invalid', b'RIFF\x01\x00\x00\x00WAVE'])
def test_invalid_provider_output_has_no_artifact(tmp_path, payload):
    class BadProvider:
        def synthesize(self, text, config):
            return payload
    inputs = ROOT / 'shared_data/inputs'
    event = CommentEvent.model_validate(json.loads((inputs / 'mock_comments.json').read_text(encoding='utf-8'))[0])
    agent = VerifiedAgent(KnowledgeEngine(inputs / 'catalog_skus.json', inputs / 'product_faq.md'))
    planner = SpeechPlanner({'scripts': []})
    turn = planner.from_response(agent.process_comment(event), run_id='RUN-001')
    admission = SpeechAdmission(planner)
    assert admission.admit([turn], run_id='RUN-001', active_sku_id='LAPTOP-ASUS-001')[0].accepted
    service = TTSService(admission, BadProvider(), TTSConfig('mock', 'fixture', 'fixture'), workspace=tmp_path)
    with pytest.raises(TTSError):
        service.synthesize(turn)
    assert not list(tmp_path.rglob('*.wav'))
