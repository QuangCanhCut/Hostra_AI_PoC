"""Kiểm thử kiểm tra dữ liệu đầu vào, chuẩn hóa và sắp xếp bình luận."""

import json
from datetime import timedelta

import pytest

from hostra_ai.part1_agent_tts.comment_ingest import ingest_comments


def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_mock_and_normalization(events, tmp_path):
    assert len(events) == 20
    assert events[0].text == "Shop ơi, ASUS Vivobook giá bao nhiêu ạ?"
    raw = events[0].model_dump(mode="json")
    raw.update(text="  Giá?  ", received_at="2026-10-27T20:00:08+07:00")
    result = ingest_comments(write(tmp_path / "input.json", [raw]), run_id=raw["run_id"], catalog_skus={raw["active_sku_id"]})
    assert result[0].text == "Giá?" and result[0].received_at.utcoffset() == timedelta(0)
    assert result[0].received_at == events[0].received_at


@pytest.mark.parametrize("change", [{"text": "  "}, {"text": "x" * 1001}, {"source": "bad"},
    {"received_at": "2026-10-27T13:00:00"}, {"active_sku_id": "unknown"},
    {"run_id": "other"}, {"extra": 1}, {"comment_id": "bad id"}])
def test_invalid_record(events, tmp_path, change):
    raw = events[0].model_dump(mode="json") | change
    with pytest.raises(ValueError, match="record 0"):
        ingest_comments(write(tmp_path / "x.json", [raw]), run_id="RUN-001", catalog_skus={events[0].active_sku_id})


def test_duplicate_id_and_invalid_structure(events, tmp_path):
    raw = events[0].model_dump(mode="json")
    for records in ([raw, raw], {}, [42]):
        with pytest.raises(ValueError):
            ingest_comments(write(tmp_path / "x.json", records), run_id="RUN-001", catalog_skus={raw["active_sku_id"]})


def test_stable_sort_and_duplicate_text(events, tmp_path):
    a = events[0].model_dump(mode="json")
    b = dict(a, comment_id="B")
    c = dict(a, comment_id="C", received_at="2026-10-27T12:59:00Z")
    result = ingest_comments(write(tmp_path / "x.json", [a, b, c]), run_id="RUN-001", catalog_skus={a["active_sku_id"]})
    assert [e.comment_id for e in result] == ["C", a["comment_id"], "B"]
