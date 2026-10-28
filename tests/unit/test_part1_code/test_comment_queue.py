"""Kiểm thử thứ tự, fairness, trạng thái deferred và đồng hồ mô phỏng."""

from dataclasses import replace
from datetime import timedelta

import pytest

from hostra_ai.part1_agent_tts.comment_queue import CommentQueue
from hostra_ai.part1_agent_tts.comment_decisions import make_decision


def decision(event, policy, score=50, action="selected", reason=None):
    return make_decision(event, action=action, reason=reason, score=score,
                         policy_version=policy.version, now=event.received_at)


def test_priority_fifo_fairness_and_no_reprocessing(events, policy):
    policy = replace(policy, max_queue_size=10, max_consecutive_per_viewer=2)
    queue = CommentQueue(policy)
    now = events[3].received_at
    # Ba bình luận của cùng viewer có điểm cao hơn; fairness nhường một lượt cho viewer khác.
    a, b, c, d = [e.model_copy(update={"viewer_id": "v1" if i < 3 else "v2"}) for i, e in enumerate(events[:4])]
    for e, score in zip((a, b, c, d), (90, 90, 90, 10)):
        queue.admit(e, decision(e, policy, score), now=now)
    assert [queue.pop(now=now).event.comment_id for _ in range(4)] == [a.comment_id, b.comment_id, d.comment_id, c.comment_id]
    assert queue.pop(now=now) is None
    with pytest.raises(ValueError, match="already"):
        queue.admit(a, decision(a, policy), now=now)


def test_defer_promote_and_expire(events, policy):
    policy = replace(policy, max_queue_size=1)
    queue = CommentQueue(policy)
    a, b, c = events[:3]
    queue.admit(a, decision(a, policy), now=a.received_at)
    assert queue.admit(b, decision(b, policy, 80), now=b.received_at).reason_code == "QUEUE_BUSY"
    queue.pop(now=b.received_at)
    promoted = queue.reevaluate(now=b.received_at)
    assert promoted[0].action == "selected" and promoted[0].decision_id != queue.decisions[2].decision_id
    queue.admit(c, decision(c, policy), now=c.received_at)
    expired = queue.reevaluate(now=c.received_at + timedelta(seconds=30))
    assert expired[0].reason_code == "EXPIRED"
    assert queue.deferred_count == 0
    with pytest.raises(ValueError):
        queue.admit(c, decision(c, policy), now=c.received_at + timedelta(seconds=30))


def test_explicit_clock_and_validation(events, policy):
    queue = CommentQueue(policy)
    event = events[0]
    deferred = decision(event, policy, action="deferred", reason="LOW_PRIORITY")
    queue.admit(event, deferred, now=event.received_at)
    assert queue.reevaluate(now=event.received_at + timedelta(seconds=29))[0].action == "selected"
    with pytest.raises(ValueError, match="backwards"):
        queue.pop(now=event.received_at)
    with pytest.raises(ValueError, match="timezone"):
        CommentQueue(policy).pop(now=event.received_at.replace(tzinfo=None))
    with pytest.raises(ValueError, match="match"):
        CommentQueue(policy).admit(events[1], deferred, now=events[1].received_at)
