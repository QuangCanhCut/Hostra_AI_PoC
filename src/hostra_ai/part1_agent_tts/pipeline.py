"""Sequential offline Part 1 run with an in-process M03-to-M04 boundary."""
from collections import Counter
from dataclasses import replace
from datetime import timedelta
import json
from pathlib import Path
import re
from time import perf_counter

from hostra_ai.core.schemas import AgentResponse, AudioArtifact, CommentDecision, CommentEvent, SpeechTurn
from hostra_ai.core.schemas.common import ID_PATTERN
from .comment_ingest import ingest_comments, load_catalog_skus
from .comment_policy import load_policy
from .comment_queue import CommentQueue
from .comment_triage import CommentTriage
from .knowledge_engine import KnowledgeEngine
from .speech_planner import PlanningError, SpeechAdmission, SpeechPlanner
from .tts_provider import MockTTSProvider, TTSService, load_tts_config, validate_wav, write_run_metadata
from .verified_agent import VerifiedAgent


class PipelineError(RuntimeError):
    """Pipeline input, integrity, or run lifecycle failure."""


def _write_json(path: Path, payload) -> None:
    """Create a UTF-8 JSON file exclusively, without replacing existing output."""
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def _validate_response(response: AgentResponse, event: CommentEvent, engine: KnowledgeEngine) -> None:
    """Validate links and reference existence after the trusted agent returns."""
    response = AgentResponse.model_validate(response.model_dump())
    if (response.run_id, response.comment_id, response.viewer_id) != (event.run_id, event.comment_id, event.viewer_id):
        raise PipelineError('RESPONSE_EVENT_MISMATCH')
    if response.status == 'answered' and response.resolved_sku_id is not None and f'catalog:{response.resolved_sku_id}' not in response.evidence_refs:
        raise PipelineError('RESPONSE_SKU_EVIDENCE_MISMATCH')
    for ref in response.evidence_refs:
        if ref.startswith('catalog:'):
            engine.get_catalog_evidence(ref[8:])
        elif ref.startswith('faq:'):
            if engine.get_faq(ref[4:]).needs_review:
                raise PipelineError('FAQ_NEEDS_REVIEW')
        else:
            raise PipelineError('INVALID_EVIDENCE_REFERENCE')


class Part1Pipeline:
    """One sequential run. No API accepts an externally supplied AgentResponse.

    Memory and semantic deduplication are scoped to this instance's one run.
    The caller must use a new run directory after interruption or restart.
    """
    def __init__(self, *, project_root: str | Path, output_root: str | Path,
                 comments_path: str | Path, config_path: str | Path,
                 catalog_path: str | Path | None = None, faq_path: str | Path | None = None,
                 policy_path: str | Path | None = None, scripts_path: str | Path | None = None,
                 service_interval_seconds: int = 0, fallback_script_id: str | None = None,
                 check_script=None):
        self.root = Path(project_root).resolve()
        self.output_root = Path(output_root).resolve()
        if not self.output_root.is_relative_to(self.root):
            raise PipelineError('OUTPUT_ROOT_OUTSIDE_PROJECT')
        self.comments_path, self.config_path = Path(comments_path), Path(config_path)
        self.catalog_path = Path(catalog_path or self.root / 'shared_data/inputs/catalog_skus.json')
        self.faq_path = Path(faq_path or self.root / 'shared_data/inputs/product_faq.md')
        self.policy_path = Path(policy_path or self.root / 'configs/comment_policy.yaml')
        self.scripts_path = Path(scripts_path or self.root / 'shared_data/inputs/approved_product_scripts.json')
        self.fallback_script_id, self.check_script = fallback_script_id, check_script
        if type(service_interval_seconds) is not int or service_interval_seconds < 0:
            raise PipelineError('INVALID_SERVICE_INTERVAL')
        self.service_interval_seconds = service_interval_seconds
        self._started = False

    def run(self, run_id: str) -> dict:
        """Run once with offline mock audio and persist verified artifacts."""
        if self._started:
            raise PipelineError('PIPELINE_ALREADY_USED')
        self._started = True
        if not isinstance(run_id, str) or len(run_id) > 64 or not re.fullmatch(ID_PATTERN, run_id):
            raise PipelineError('INVALID_RUN_ID')
        started = perf_counter()
        # Preserve the fixture's source run while explicitly remapping validated
        # events into the new output run. Never change the source dataset.
        raw = json.loads(self.comments_path.read_text(encoding='utf-8'))
        if not isinstance(raw, list) or not raw or not isinstance(raw[0], dict):
            raise PipelineError('INVALID_COMMENTS')
        source_run = raw[0].get('run_id')
        if not isinstance(source_run, str):
            raise PipelineError('INVALID_SOURCE_RUN')
        events = ingest_comments(self.comments_path, run_id=source_run, catalog_skus=load_catalog_skus(self.catalog_path))
        events = [CommentEvent.model_validate({**event.model_dump(), 'run_id': run_id}) for event in events]
        policy = load_policy(self.policy_path)
        engine = KnowledgeEngine(self.catalog_path, self.faq_path)
        planner = SpeechPlanner.from_file(self.scripts_path, check_script=self.check_script)
        config = replace(load_tts_config(self.config_path), provider='mock', live_api_opt_in=False)
        triage, queue = CommentTriage(policy), CommentQueue(policy)
        agent = VerifiedAgent(engine, mode='lexical')
        admission = SpeechAdmission(planner)
        tts = TTSService(admission, MockTTSProvider(), config, workspace=self.output_root)
        run_dir = self.output_root / 'shared_data' / 'runs' / run_id
        if not run_dir.resolve().is_relative_to(self.output_root / 'shared_data' / 'runs'):
            raise PipelineError('UNSAFE_RUN_PATH')
        run_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            run_dir.mkdir(exist_ok=False)
        except FileExistsError:
            raise PipelineError('RUN_ALREADY_EXISTS') from None
        out = run_dir / 'step1_agent_audio'
        out.mkdir()
        rows = {e.comment_id: {'comment_id': e.comment_id, 'viewer_id': e.viewer_id,
                 'text': e.text, 'active_sku_id': e.active_sku_id,
                 'response_status': None, 'reason_code': None, 'resolved_sku_id': None,
                 'evidence_refs': [], 'speech_type': None, 'admission': None,
                 'audio_id': None, 'duration_ms': None, 'outcome': None} for e in events}
        responses, turns, artifacts = [], [], []
        spoken: set[tuple[str, str, str]] = set()
        tts_calls = 0
        failures = 0
        timings = {'comment_processing': 0.0, 'agent': 0.0, 'speech_planning': 0.0, 'tts': 0.0}

        def handle(item):
            nonlocal tts_calls, failures
            row, event = rows[item.event.comment_id], item.event
            try:
                # This is the sole integration boundary: no external response is accepted.
                tick = perf_counter()
                response = agent.process_queue_item(item)
                timings['agent'] += perf_counter() - tick
                _validate_response(response, event, engine)
                responses.append(response)
                row.update(response_status=response.status, reason_code=response.reason_code,
                           resolved_sku_id=response.resolved_sku_id, evidence_refs=list(response.evidence_refs))
                if response.status == 'blocked' and self.fallback_script_id is None:
                    row['outcome'] = 'blocked_no_fallback_configured'
                    return
                speech_type = 'safe_fallback' if response.status == 'blocked' else 'comment_reply'
                key = (run_id, response.response_id, speech_type)
                if key in spoken:
                    row['outcome'] = 'duplicate_response'
                    failures += 1
                    return
                spoken.add(key)
                tick = perf_counter()
                try:
                    turn = planner.from_response(response, run_id=run_id,
                        fallback_script_id=self.fallback_script_id if response.status == 'blocked' else None,
                        active_sku_id=event.active_sku_id)
                except PlanningError as exc:
                    if response.status != 'blocked':
                        raise
                    row['outcome'] = 'fallback_rejected'
                    row['planning_reason'] = str(exc)
                    return
                turns.append(turn)
                row['speech_type'] = turn.speech_type
                decision = admission.admit([turn], run_id=run_id, active_sku_id=event.active_sku_id)[0]
                timings['speech_planning'] += perf_counter() - tick
                row['admission'] = decision.reason
                if not decision.accepted:
                    row['outcome'] = 'admission_rejected'
                    failures += 1
                    return
                tts_calls += 1
                tick = perf_counter()
                artifact = tts.synthesize(turn)
                timings['tts'] += perf_counter() - tick
                artifacts.append(artifact)
                row.update(audio_id=artifact.audio_id, duration_ms=artifact.duration_ms, outcome='audio_created')
            except Exception as exc:
                failures += 1
                row['outcome'] = 'processing_error'
                row['error_type'] = type(exc).__name__

        # A zero interval is an explicit immediate-service simulation; a positive
        # interval exercises the real queue's priority, fairness and deferred TTL.
        next_service = events[0].received_at
        for event in events:
            if self.service_interval_seconds:
                while next_service < event.received_at:
                    queue.reevaluate(now=next_service)
                    item = queue.pop(now=next_service)
                    if item:
                        handle(item)
                    next_service += timedelta(seconds=self.service_interval_seconds)
            tick = perf_counter()
            queue.reevaluate(now=event.received_at)
            queue.admit(event, triage.evaluate(event), now=event.received_at)
            timings['comment_processing'] += perf_counter() - tick
            if not self.service_interval_seconds:
                item = queue.pop(now=event.received_at)
                if item:
                    handle(item)
        if self.service_interval_seconds:
            while queue.ready_count or queue.deferred_count:
                queue.reevaluate(now=next_service)
                item = queue.pop(now=next_service)
                if item:
                    handle(item)
                next_service += timedelta(seconds=self.service_interval_seconds)
        latest = {d.comment_id: d for d in queue.decisions}
        for event in events:
            decision = latest[event.comment_id]
            rows[event.comment_id].update(decision_action=decision.action, decision_reason=decision.reason_code)
            if rows[event.comment_id]['outcome'] is None:
                rows[event.comment_id]['outcome'] = decision.action
        summary = {'run_id': run_id, 'source_run_id': source_run, 'status': 'partial' if failures else 'completed',
            'service_interval_seconds': self.service_interval_seconds, 'comments': len(events),
            'decisions': dict(Counter(d.action for d in latest.values())),
            'responses': dict(Counter(r.status for r in responses)), 'speech_turns': len(turns),
            'tts_calls': tts_calls, 'audio_files': len(artifacts),
            'audio_duration_ms': sum(a.duration_ms for a in artifacts), 'errors': failures,
            'elapsed_seconds': round(perf_counter() - started, 4), 'tts_provider': 'mock',
            'timings_seconds': {key: round(value, 6) for key, value in timings.items()},
            'input_dataset': str(self.comments_path), 'mock_voice': config.voice,
            'sample_rate_hz': config.sample_rate_hz,
            'decision_reasons': dict(Counter(d.reason_code for d in latest.values() if d.reason_code)),
            'agent_reasons': dict(Counter(r.reason_code for r in responses if r.reason_code)),
            'faq_grounded_answers': sum(any(ref.startswith('faq:') for ref in r.evidence_refs) for r in responses),
            'audio_note': 'Mock WAV contains silence, not speech.', 'rows': list(rows.values())}
        _write_json(out / 'comment_decisions.json', [d.model_dump(mode='json') for d in queue.decisions])
        _write_json(out / 'answers.json', [r.model_dump(mode='json') for r in responses])
        if turns:
            write_run_metadata(self.output_root, run_id, turns, artifacts)
        else:
            _write_json(out / 'speech_turns.json', [])
            _write_json(out / 'audio_artifacts.json', [])
        validate_run(self.output_root, run_id, events, scripts_path=self.scripts_path)
        _write_json(out / 'evaluation.json', summary)
        return summary


def validate_run(workspace: str | Path, run_id: str, events: list[CommentEvent], *, scripts_path: str | Path | None = None) -> None:
    """Read persisted public records and WAV files and verify their relationships."""
    if not isinstance(run_id, str) or len(run_id) > 64 or not re.fullmatch(ID_PATTERN, run_id):
        raise PipelineError('INVALID_RUN_ID')
    root = Path(workspace).resolve()
    out = root / 'shared_data' / 'runs' / run_id / 'step1_agent_audio'
    def read(name, model):
        return [model.model_validate(x) for x in json.loads((out / name).read_text(encoding='utf-8'))]
    decisions = read('comment_decisions.json', CommentDecision)
    responses = read('answers.json', AgentResponse)
    turns = read('speech_turns.json', SpeechTurn)
    artifacts = read('audio_artifacts.json', AudioArtifact)
    source = {(e.run_id, e.comment_id): e for e in events}
    selected = {(d.run_id, d.comment_id) for d in decisions if d.action == 'selected'}
    if any((d.run_id, d.comment_id) not in source for d in decisions):
        raise PipelineError('DECISION_SOURCE_MISMATCH')
    by_response = {r.response_id: r for r in responses}
    by_turn = {t.speech_turn_id: t for t in turns}
    if len(by_response) != len(responses) or len(by_turn) != len(turns):
        raise PipelineError('DUPLICATE_OUTPUT_ID')
    if len({(r.run_id, r.comment_id) for r in responses}) != len(responses):
        raise PipelineError('DUPLICATE_RESPONSE_FOR_COMMENT')
    if len({(t.run_id, t.response_id, t.speech_type) for t in turns}) != len(turns):
        raise PipelineError('DUPLICATE_RESPONSE_TURN')
    if len({a.audio_id for a in artifacts}) != len(artifacts):
        raise PipelineError('DUPLICATE_AUDIO_ID')
    for response in responses:
        event = source.get((response.run_id, response.comment_id))
        if event is None or event.viewer_id != response.viewer_id or (response.run_id, response.comment_id) not in selected:
            raise PipelineError('RESPONSE_SOURCE_MISMATCH')
    for turn in turns:
        response = by_response.get(turn.response_id)
        if response is None or turn.run_id != response.run_id:
            raise PipelineError('TURN_SOURCE_MISMATCH')
        if turn.speech_type == 'comment_reply':
            if response.status == 'blocked' or turn.text != response.answer_text:
                raise PipelineError('TURN_SOURCE_MISMATCH')
        elif turn.speech_type == 'safe_fallback' and response.status == 'blocked' and scripts_path is not None:
            library = json.loads(Path(scripts_path).read_text(encoding='utf-8'))
            matches = [s for s in library['scripts'] if s.get('script_id') == turn.script_ref]
            if len(matches) != 1 or matches[0].get('speech_type') != 'safe_fallback' or matches[0].get('text', '').strip() != turn.text or matches[0].get('approval', {}).get('status') != 'approved':
                raise PipelineError('FALLBACK_SOURCE_MISMATCH')
        else:
            raise PipelineError('TURN_SOURCE_MISMATCH')
    seen_turns = set()
    for artifact in artifacts:
        turn = by_turn.get(artifact.speech_turn_id)
        if turn is None or turn.run_id != artifact.run_id or turn.response_id != artifact.response_id or turn.speech_turn_id in seen_turns:
            raise PipelineError('AUDIO_SOURCE_MISMATCH')
        seen_turns.add(turn.speech_turn_id)
        path = root.joinpath(*artifact.file_path.split('/'))
        if not path.resolve().is_relative_to((root / 'shared_data' / 'runs' / run_id).resolve()):
            raise PipelineError('AUDIO_PATH_MISMATCH')
        if validate_wav(path.read_bytes(), artifact.sample_rate_hz) != artifact.duration_ms:
            raise PipelineError('AUDIO_DURATION_MISMATCH')
