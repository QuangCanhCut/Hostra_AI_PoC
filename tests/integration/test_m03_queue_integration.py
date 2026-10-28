from pathlib import Path
from hostra_ai.part1_agent_tts.comment_ingest import ingest_comments, load_catalog_skus
from hostra_ai.part1_agent_tts.comment_policy import load_policy
from hostra_ai.part1_agent_tts.comment_queue import CommentQueue
from hostra_ai.part1_agent_tts.comment_triage import CommentTriage
from hostra_ai.part1_agent_tts.knowledge_engine import KnowledgeEngine
from hostra_ai.part1_agent_tts.verified_agent import VerifiedAgent

ROOT = Path(__file__).resolve().parents[2]


def test_selected_comment_from_queue_reaches_verified_agent():
    policy = load_policy(ROOT / 'configs/comment_policy.yaml')
    catalog = ROOT / 'shared_data/inputs/catalog_skus.json'
    events = ingest_comments(ROOT / 'shared_data/inputs/mock_comments.json', run_id='RUN-001', catalog_skus=load_catalog_skus(catalog))
    event = events[0]
    decision = CommentTriage(policy).evaluate(event)
    queue = CommentQueue(policy)
    queue.admit(event, decision, now=event.received_at)
    item = queue.pop(now=event.received_at)
    assert item is not None
    engine = KnowledgeEngine(catalog, ROOT / 'shared_data/inputs/product_faq.md')
    result = VerifiedAgent(engine).process_queue_item(item)
    assert result.status == 'answered'
    assert result.comment_id == event.comment_id
    assert result.evidence_refs == ('catalog:LAPTOP-ASUS-001',)


def test_all_mock_comments_through_triage_queue_and_agent():
    policy = load_policy(ROOT / 'configs/comment_policy.yaml')
    catalog = ROOT / 'shared_data/inputs/catalog_skus.json'
    events = ingest_comments(ROOT / 'shared_data/inputs/mock_comments.json', run_id='RUN-001', catalog_skus=load_catalog_skus(catalog))
    queue, triage = CommentQueue(policy), CommentTriage(policy)
    agent = VerifiedAgent(KnowledgeEngine(catalog, ROOT / 'shared_data/inputs/product_faq.md'))
    outcomes = {}
    for event in events:
        decision = triage.evaluate(event)
        queue.admit(event, decision, now=event.received_at)
        item = queue.pop(now=event.received_at)
        outcomes[event.comment_id] = agent.process_queue_item(item) if item else decision
    assert len(outcomes) == 20
    for cid in ('CMT-005', 'CMT-015', 'CMT-016'):
        assert outcomes[cid].action == 'skipped'
    for cid in ('CMT-001', 'CMT-002', 'CMT-003', 'CMT-004', 'CMT-006', 'CMT-007', 'CMT-008', 'CMT-009', 'CMT-010', 'CMT-017', 'CMT-020'):
        assert outcomes[cid].status == 'answered', cid
    for cid in ('CMT-011', 'CMT-012', 'CMT-013', 'CMT-014', 'CMT-018', 'CMT-019'):
        assert outcomes[cid].status == 'blocked', cid
    for cid in ('CMT-004', 'CMT-009', 'CMT-017'):
        assert outcomes[cid].resolved_sku_id is None
        assert any(ref.startswith('faq:') for ref in outcomes[cid].evidence_refs)
    assert '810.000' in outcomes['CMT-010'].answer_text
    assert 'faq:FAQ-SALES-005' in outcomes['CMT-020'].evidence_refs
