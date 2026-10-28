"""Kiểm thử toàn bộ luồng xử lý và tính nhất quán khi chạy lại."""

from datetime import timedelta
from pathlib import Path

from hostra_ai.core.schemas import CommentDecision
from hostra_ai.part1_agent_tts.comment_ingest import ingest_comments, load_catalog_skus
from hostra_ai.part1_agent_tts.comment_policy import load_policy
from hostra_ai.part1_agent_tts.comment_queue import CommentQueue
from hostra_ai.part1_agent_tts.comment_triage import CommentTriage

ROOT = Path(__file__).resolve().parents[2]


def replay():
    policy = load_policy(ROOT / "configs/comment_policy.yaml")
    events = ingest_comments(ROOT / "shared_data/inputs/mock_comments.json", run_id="RUN-001",
        catalog_skus=load_catalog_skus(ROOT / "shared_data/inputs/catalog_skus.json"))
    triage, queue = CommentTriage(policy), CommentQueue(policy)
    for event in events:
        queue.reevaluate(now=event.received_at)
        queue.admit(event, triage.evaluate(event), now=event.received_at)
    now = events[-1].received_at + timedelta(seconds=30)
    queue.reevaluate(now=now)
    while queue.pop(now=now):
        pass
    for d in queue.decisions:
        assert CommentDecision.model_validate(d.model_dump(mode="json")) == d
    return events, [(d.comment_id, d.action, d.reason_code, d.priority_score, d.duplicate_of, d.decided_at) for d in queue.decisions]


def test_replay_is_business_deterministic():
    events, first = replay()
    _, second = replay()
    assert len(events) == 20
    assert first == second
    assert any(d[2] == "DUPLICATE" for d in first)
