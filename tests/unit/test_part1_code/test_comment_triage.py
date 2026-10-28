"""Kiểm thử các quy tắc duplicate, spam, off-topic và điểm ưu tiên."""

from datetime import timedelta

import pytest

from hostra_ai.part1_agent_tts.comment_triage import CommentTriage, normalize_text, score_comment


def test_mock_decisions(events, policy):
    triage = CommentTriage(policy)
    decisions = [triage.evaluate(e) for e in events]
    assert (decisions[4].reason_code, decisions[4].duplicate_of) == ("DUPLICATE", "CMT-001")
    assert decisions[14].reason_code == "SPAM"
    assert decisions[15].reason_code == "OFF_TOPIC"
    assert decisions[1].action == decisions[8].action == "selected"
    assert all(0 <= d.priority_score <= 100 for d in decisions)


def test_duplicates_scope_window_and_accents(events, policy):
    base = events[0]
    triage = CommentTriage(policy)
    assert triage.evaluate(base).action == "selected"
    def make(id, seconds, **changes):
        return base.model_copy(update={"comment_id": id, "received_at": base.received_at + timedelta(seconds=seconds), **changes})
    assert triage.evaluate(make("other-viewer", 1, viewer_id="another")).action == "selected"
    assert triage.evaluate(make("other-run", 2, run_id="other")).action == "selected"
    assert triage.evaluate(make("equal", 30)).reason_code == "DUPLICATE"
    # Dùng triage mới để kiểm tra ngoài biên mà không có bản trùng xen giữa.
    fresh = CommentTriage(policy)
    fresh.evaluate(base)
    assert fresh.evaluate(make("outside", 31)).action == "selected"
    assert normalize_text(" GIÁ   MÁY ") == "giá máy"
    assert normalize_text("GIÁ") != normalize_text("GIA")


def test_conservative_rules_and_unique_decisions(events, policy):
    triage = CommentTriage(policy)
    event = events[0].model_copy(update={"text": "ASUS GIÁ BAO NHIÊU?"})
    first, second = triage.evaluate(event), triage.evaluate(event)
    assert first.action == second.action == "selected"
    assert first.decision_id != second.decision_id
    assert score_comment("Tôi muốn đặt mua và so sánh giá RAM", policy) <= 100
    with pytest.raises(ValueError):
        triage.evaluate(event.model_copy(update={"received_at": event.received_at - timedelta(seconds=1)}))
