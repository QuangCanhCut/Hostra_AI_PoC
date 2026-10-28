"""Offline integration and failure checks for the Part 1 pipeline."""
import inspect
import json
from pathlib import Path

import pytest

from hostra_ai.core.schemas import AgentResponse
from hostra_ai.part1_agent_tts.pipeline import Part1Pipeline, PipelineError
from hostra_ai.part1_agent_tts.verified_agent import VerifiedAgent

ROOT = Path(__file__).resolve().parents[2]


def make_pipeline(tmp_path, **kwargs):
    return Part1Pipeline(project_root=ROOT, output_root=tmp_path,
        comments_path=kwargs.pop('comments_path', ROOT / 'shared_data/inputs/mock_comments.json'),
        config_path=kwargs.pop('config_path', ROOT / 'configs/app.yaml'), **kwargs)


def test_golden_run_outputs_and_no_overwrite(tmp_path):
    result = make_pipeline(tmp_path).run('RUN-M05-TEST')
    assert result['status'] == 'completed'
    assert result['comments'] == 20 and result['decisions'] == {'selected': 17, 'skipped': 3}
    assert result['responses'] == {'answered': 11, 'blocked': 6}
    assert result['audio_files'] == result['tts_calls'] == 11
    rows = {r['comment_id']: r for r in result['rows']}
    assert rows['CMT-002']['resolved_sku_id'] == 'LAPTOP-LENOVO-002'
    assert rows['CMT-010']['resolved_sku_id'] is None
    assert rows['CMT-011']['outcome'] == 'blocked_no_fallback_configured'
    assert rows['CMT-015']['decision_reason'] == 'SPAM'
    out = tmp_path / 'shared_data/runs/RUN-M05-TEST/step1_agent_audio'
    assert len(list((out / 'audio').glob('*.wav'))) == 11
    assert len(json.loads((out / 'evaluation.json').read_text(encoding='utf-8'))['rows']) == 20
    with pytest.raises(PipelineError, match='RUN_ALREADY_EXISTS'):
        make_pipeline(tmp_path).run('RUN-M05-TEST')


def test_two_runs_have_equivalent_business_results_and_isolated_files(tmp_path):
    a = make_pipeline(tmp_path).run('RUN-A')
    b = make_pipeline(tmp_path).run('RUN-B')
    def normalized(rows):
        return [{k: v for k, v in row.items() if k != 'audio_id'} for row in rows]
    assert normalized(a['rows']) == normalized(b['rows'])
    assert set(r['audio_id'] for r in a['rows'] if r['audio_id']).isdisjoint(
        r['audio_id'] for r in b['rows'] if r['audio_id'])


def test_boundary_has_no_external_response_input_and_checks_mismatched_ids(tmp_path, monkeypatch):
    assert 'response' not in inspect.signature(Part1Pipeline.run).parameters
    original = VerifiedAgent.process_queue_item
    def mismatched(self, item):
        response = original(self, item)
        return response.model_copy(update={'viewer_id': 'OTHER'})
    monkeypatch.setattr(VerifiedAgent, 'process_queue_item', mismatched)
    result = make_pipeline(tmp_path).run('RUN-MISMATCH')
    assert result['status'] == 'partial' and result['audio_files'] == 0
    assert any(row.get('error_type') == 'PipelineError' for row in result['rows'])


def test_invalid_evidence_and_forged_answer_are_not_forwarded(tmp_path, monkeypatch):
    original = VerifiedAgent.process_queue_item
    def bad_ref(self, item):
        response = original(self, item)
        if response.status == 'answered':
            return response.model_copy(update={'evidence_refs': ('catalog:UNKNOWN',)})
        return response
    monkeypatch.setattr(VerifiedAgent, 'process_queue_item', bad_ref)
    result = make_pipeline(tmp_path).run('RUN-BAD-REF')
    assert result['status'] == 'partial' and result['audio_files'] == 0


def test_invalid_input_configuration_and_output_root(tmp_path):
    with pytest.raises(FileNotFoundError):
        make_pipeline(tmp_path, comments_path=tmp_path / 'missing.json').run('RUN-X')
    with pytest.raises(FileNotFoundError):
        make_pipeline(tmp_path, config_path=tmp_path / 'missing.yaml').run('RUN-X')
    with pytest.raises(PipelineError, match='INVALID_RUN_ID'):
        make_pipeline(tmp_path).run('../escape')
    with pytest.raises(PipelineError, match='INVALID_SERVICE_INTERVAL'):
        make_pipeline(tmp_path, service_interval_seconds=-1)


def test_queue_deferred_policy_is_not_bypassed(tmp_path):
    result = make_pipeline(tmp_path, service_interval_seconds=12).run('RUN-DEFERRED')
    out = tmp_path / 'shared_data/runs/RUN-DEFERRED/step1_agent_audio'
    decisions = json.loads((out / 'comment_decisions.json').read_text(encoding='utf-8'))
    assert result['comments'] == 20
    assert any(d['action'] == 'deferred' for d in decisions)
    assert all(row['audio_id'] is None for row in result['rows'] if row['decision_action'] == 'skipped')


def test_tts_error_is_partial_and_other_comments_continue(tmp_path, monkeypatch):
    from hostra_ai.part1_agent_tts.tts_provider import MockTTSProvider
    original = MockTTSProvider.synthesize
    calls = []
    def fail_once(self, text, config):
        calls.append(1)
        if len(calls) == 1:
            raise TimeoutError('simulated')
        return original(self, text, config)
    monkeypatch.setattr(MockTTSProvider, 'synthesize', fail_once)
    result = make_pipeline(tmp_path).run('RUN-PARTIAL')
    assert result['status'] == 'partial' and result['errors'] == 1
    assert result['tts_calls'] == 11 and result['audio_files'] == 10


def test_approved_fixture_fallback_and_pending_scripts(tmp_path):
    fixture = tmp_path / 'scripts.json'
    fixture.write_text(json.dumps({'scripts': [{'script_id': 'SAFE', 'speech_type': 'safe_fallback',
        'sku_id': None, 'text': 'Fixture fallback.', 'approval': {'status': 'approved',
        'approved_by': 'test-only', 'approved_at': '2026-01-01T00:00:00Z'}}]}), encoding='utf-8')
    result = make_pipeline(tmp_path, scripts_path=fixture, fallback_script_id='SAFE').run('RUN-FALLBACK')
    assert result['audio_files'] == 17
    assert sum(r['speech_type'] == 'safe_fallback' for r in result['rows']) == 6
    pending = make_pipeline(tmp_path, fallback_script_id='SCRIPT-FALLBACK-002').run('RUN-PENDING')
    assert pending['audio_files'] == 11
    assert sum(r['outcome'] == 'fallback_rejected' for r in pending['rows']) == 6


def test_duplicate_response_id_cannot_create_second_audio(tmp_path, monkeypatch):
    original = VerifiedAgent.process_queue_item
    def duplicate(self, item):
        response = original(self, item)
        return response.model_copy(update={'response_id': 'REUSED-RESPONSE'})
    monkeypatch.setattr(VerifiedAgent, 'process_queue_item', duplicate)
    with pytest.raises(PipelineError, match='DUPLICATE_OUTPUT_ID'):
        make_pipeline(tmp_path).run('RUN-DUPLICATE-RESPONSE')
    out = tmp_path / 'shared_data/runs/RUN-DUPLICATE-RESPONSE/step1_agent_audio'
    assert len(list((out / 'audio').glob('*.wav'))) == 1
    assert not (out / 'evaluation.json').exists()


def test_no_forged_candidate_and_missing_answer_evidence(tmp_path, monkeypatch):
    original = VerifiedAgent.process_queue_item
    def missing_evidence(self, item):
        response = original(self, item)
        if response.status == 'answered':
            return response.model_copy(update={'evidence_refs': ()})
        return response
    monkeypatch.setattr(VerifiedAgent, 'process_queue_item', missing_evidence)
    result = make_pipeline(tmp_path).run('RUN-NO-EVIDENCE')
    assert result['status'] == 'partial' and result['audio_files'] == 0
