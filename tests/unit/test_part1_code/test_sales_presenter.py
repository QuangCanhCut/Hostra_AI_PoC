"""Offline tests for conversational style and experimental LLM safety."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from hostra_ai.core.schemas import CommentEvent
from hostra_ai.part1_agent_tts.answer_verifier import AnswerVerifier, CandidateAnswer
from hostra_ai.part1_agent_tts.knowledge_engine import KnowledgeEngine
from hostra_ai.part1_agent_tts.verified_agent import ExperimentalOpenAISalesProvider, VerifiedAgent

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def setup():
    inputs = ROOT / 'shared_data/inputs'
    engine = KnowledgeEngine(inputs / 'catalog_skus.json', inputs / 'product_faq.md')
    events = [CommentEvent.model_validate(x) for x in json.loads((inputs / 'mock_comments.json').read_text(encoding='utf-8'))]
    return engine, events


def test_natural_prices_and_no_repeated_followup(setup):
    engine, events = setup
    agent = VerifiedAgent(engine)
    first = agent.process_comment(events[0])
    assert first.status == 'answered'
    assert '26.500.000' in first.answer_text and 'phiên demo HOSTRA' in first.answer_text
    assert '?' in first.answer_text and not any(x in first.answer_text for x in ('**', 'catalog:', 'faq:'))
    again = agent.process_comment(events[0].model_copy(update={'text': 'Vậy giá máy này bao nhiêu?'}))
    assert again.status == 'answered' and '?' not in again.answer_text
    other = agent.process_comment(events[1])
    assert '25.690.000' in other.answer_text and '?' in other.answer_text


def test_conversation_style_cannot_hide_unsupported_claim(setup):
    engine, events = setup
    class BadProvider:
        def generate(self, query, skus, intent, evidence):
            return CandidateAnswer('Giá ASUS trong phiên demo HOSTRA là 20.000.000 đồng. Bạn muốn mình tư vấn thêm về cấu hình của mẫu này không ạ?', skus, (f'catalog:{skus[0]}',))
    assert VerifiedAgent(engine, provider=BadProvider()).process_comment(events[0]).reason_code == 'VERIFICATION_FAILED'


@pytest.mark.parametrize('text', [
    'Bạn muốn mình tư vấn thêm về cấu hình của mẫu này không ạ?',
    'Giá ASUS trong phiên demo HOSTRA là 26.500.000 đồng. Máy chắc chắn đạt 200 FPS.',
    'Giá ASUS trong phiên demo HOSTRA là 26.500.000 đồng. Lenovo tặng quà.',
])
def test_followup_cannot_replace_fact_or_mask_unverified_claim(setup, text):
    engine, events = setup
    class BadProvider:
        def generate(self, query, skus, intent, evidence):
            return CandidateAnswer(text, skus, (f'catalog:{skus[0]}',))
    assert VerifiedAgent(engine, provider=BadProvider()).process_comment(events[0]).reason_code == 'VERIFICATION_FAILED'


def test_experimental_disabled_never_calls_client_and_falls_back(setup):
    engine, events = setup
    class Forbidden:
        def __getattr__(self, name):
            raise AssertionError('No API access allowed')
    provider = ExperimentalOpenAISalesProvider.from_files(ROOT / 'configs/app.yaml', ROOT / 'configs/sales_persona.yaml', client=Forbidden())
    result = VerifiedAgent(engine, provider=provider).process_comment(events[0])
    assert result.status == 'answered' and '26.500.000' in result.answer_text


@pytest.mark.parametrize('mode', ['invalid_json', 'wrong_price', 'timeout'])
def test_experimental_llm_rejected_or_failure_uses_verified_fallback(setup, mode):
    engine, events = setup
    class Responses:
        def create(self, **kwargs):
            assert 'viewer_question' in json.loads(kwargs['input'])
            assert 'untrusted' in kwargs['instructions']
            if mode == 'timeout':
                raise TimeoutError()
            if mode == 'invalid_json':
                return SimpleNamespace(output_text='{')
            payload = {'answer_text': 'Giá ASUS trong phiên demo HOSTRA là 20.000.000 đồng.',
                       'claimed_sku_ids': ['LAPTOP-ASUS-001'],
                       'cited_evidence_refs': ['catalog:LAPTOP-ASUS-001'], 'claims': []}
            return SimpleNamespace(output_text=json.dumps(payload))
    fake = SimpleNamespace(responses=Responses())
    persona = ExperimentalOpenAISalesProvider.from_files(ROOT / 'configs/app.yaml', ROOT / 'configs/sales_persona.yaml', client=fake)
    persona.enabled = True
    result = VerifiedAgent(engine, provider=persona).process_comment(events[0])
    assert result.status == 'answered' and '26.500.000' in result.answer_text
    assert '20.000.000' not in result.answer_text


def test_experimental_verified_candidate_is_accepted(setup):
    engine, events = setup
    class Responses:
        def create(self, **kwargs):
            payload = {'answer_text': 'Giá ASUS trong phiên demo HOSTRA là 26.500.000 đồng.',
                       'claimed_sku_ids': ['LAPTOP-ASUS-001'],
                       'cited_evidence_refs': ['catalog:LAPTOP-ASUS-001'], 'claims': []}
            return SimpleNamespace(output_text=json.dumps(payload))
    provider = ExperimentalOpenAISalesProvider(model='test', instructions='untrusted', enabled=True,
                                               client=SimpleNamespace(responses=Responses()))
    result = VerifiedAgent(engine, provider=provider).process_comment(events[0])
    assert result.status == 'answered' and result.answer_text == 'Giá ASUS trong phiên demo HOSTRA là 26.500.000 đồng.'
