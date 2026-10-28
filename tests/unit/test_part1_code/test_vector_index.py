"""Kiểm tra cosine, manifest, stale source và lưu/tải local index."""

from copy import deepcopy
import json
import math

import pytest

from hostra_ai.part1_agent_tts.knowledge.models import FAQChunk
from hostra_ai.part1_agent_tts.knowledge.vector_index import IndexError, VectorIndex


def chunks():
    return [FAQChunk(name, "RAM SSD", {"faq_id": name, "sku_ids": skus,
        "source_file": "faq.md", "evidence_refs": ("catalog:A",),
        "evidence_notes": ("cần review",), "needs_review": True}, f"faq:{name}")
        for name, skus in (("A", ("A",)), ("B", ("A", "B")), ("C", ("B",)))]


def make_index(source=None):
    return VectorIndex(source or chunks(), [[1., 0.], [1., 1.], [0., 1.]], provider="mock", model="test", requested_dimensions=2)


def test_cosine_ranking_filter_and_snapshot():
    source = chunks()
    index = make_index(source)
    hits = index.search([1., 0.])
    assert [h.chunk_id for h in hits] == ["A", "B", "C"]
    assert [h.score for h in hits] == pytest.approx([1., 1 / math.sqrt(2), 0.])
    assert [h.chunk_id for h in index.search([1., 0.], sku_ids=("A", "B"))] == ["B"]
    source[0].metadata["needs_review"] = False
    hits[0].metadata["evidence_notes"] = ()
    assert index.search([1., 0.])[0].metadata["needs_review"] is True
    assert index.search([1., 0.])[0].metadata["evidence_notes"] == ("cần review",)
    tie = VectorIndex(list(reversed(chunks())), [[1., 0.]] * 3, provider="mock", model="test")
    assert [h.chunk_id for h in tie.search([1., 0.])] == ["A", "B", "C"]


@pytest.mark.parametrize("vector", [[], [1.], [0., 0.], [float("nan"), 1.], [float("inf"), 1.], [True, 1.]])
def test_invalid_query_vectors(vector):
    with pytest.raises(ValueError):
        make_index().search(vector)


def test_invalid_build_and_compatibility():
    with pytest.raises(ValueError):
        VectorIndex(chunks(), [[1., 0.]], provider="mock", model="test")
    with pytest.raises(ValueError):
        VectorIndex([chunks()[0]] * 2, [[1., 0.]] * 2, provider="mock", model="test")
    index = make_index()
    with pytest.raises(IndexError, match="model"):
        index.check_compatibility(chunks(), provider="mock", model="wrong", dimensions=2)
    changed = chunks()
    changed[0].metadata["needs_review"] = False
    with pytest.raises(IndexError, match="Stale"):
        index.check_compatibility(changed, provider="mock", model="test", dimensions=2)


def test_round_trip_and_no_input_overwrite(tmp_path):
    source = chunks()
    before = deepcopy(source)
    index = make_index(source)
    path = tmp_path / "index.json"
    index.save(path)
    loaded = VectorIndex.load(path, chunks(), provider="mock", model="test", dimensions=2)
    assert loaded.search([1., 0.]) == index.search([1., 0.])
    assert source == before
    with pytest.raises(IndexError):
        index.save(tmp_path / "catalog_skus.json")
    with pytest.raises(IndexError):
        index.save(tmp_path / "shared_data/inputs/index.json")


@pytest.mark.parametrize("change", ["manifest", "vectors", "metadata", "json"])
def test_corrupt_file(tmp_path, change):
    path = tmp_path / "index.json"
    make_index().save(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if change == "manifest":
        del data["manifest"]["model"]
    elif change == "vectors":
        data["vectors"].pop()
    elif change == "metadata":
        del data["chunks"][0]["metadata"]["needs_review"]
    path.write_text("{" if change == "json" else json.dumps(data), encoding="utf-8")
    with pytest.raises(IndexError):
        VectorIndex.load(path, chunks(), provider="mock", model="test", dimensions=2)


def test_missing_file_and_stale_load(tmp_path):
    path = tmp_path / "index.json"
    with pytest.raises(IndexError):
        VectorIndex.load(path, chunks(), provider="mock", model="test", dimensions=2)
    make_index().save(path)
    changed = chunks()
    changed[0].metadata["evidence_notes"] = ("nguồn mới",)
    with pytest.raises(IndexError, match="Stale"):
        VectorIndex.load(path, changed, provider="mock", model="test", dimensions=2)


@pytest.mark.parametrize("value", [[[0., 0.]], [[float("nan"), 1.]], [[float("inf"), 1.]], [[]]])
def test_invalid_document_vectors(value):
    with pytest.raises(ValueError):
        VectorIndex([chunks()[0]], value, provider="mock", model="test")


def test_manifest_counts_model_dimension_and_atomic_preservation(tmp_path, monkeypatch):
    import hostra_ai.part1_agent_tts.knowledge.vector_index as module
    path = tmp_path / "index.json"
    index = make_index()
    index.save(path)
    with pytest.raises(IndexError, match="model"):
        VectorIndex.load(path, chunks(), provider="mock", model="other", dimensions=2)
    with pytest.raises(IndexError, match="dimensions"):
        VectorIndex.load(path, chunks(), provider="mock", model="test", dimensions=3)
    original = path.read_bytes()
    def fail_replace(*args):
        raise OSError("Giả lập lỗi ổ đĩa")
    monkeypatch.setattr(module.os, "replace", fail_replace)
    with pytest.raises(OSError):
        index.save(path)
    assert path.read_bytes() == original
    assert list(tmp_path.glob("*.tmp")) == []
