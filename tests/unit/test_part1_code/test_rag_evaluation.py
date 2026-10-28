"""Tính tay macro Recall và MRR; câu không có relevant không vào mẫu số recall."""

from pathlib import Path
import runpy
from types import SimpleNamespace as NS

import pytest

ROOT = Path(__file__).resolve().parents[3]


def test_macro_recall_and_mrr_by_hand(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts/script_rag"))
    evaluate = runpy.run_path(str(ROOT / "scripts/script_rag/evaluate_rag.py"))["evaluate"]
    def record(name):
        return NS(faq_id=name, evidence_refs=(), evidence_notes=(), sku_ids=(), needs_review=False)
    def hit(name):
        return NS(chunk_id=name, source_ref=f"faq:{name}", score=1., metadata={
            "faq_id": name, "evidence_refs": (), "evidence_notes": (), "sku_ids": (), "needs_review": False})
    engine = NS(search=lambda query, **kwargs: [hit("A")] if query == "q1" else [hit("X"), hit("C")],
                retrieve=lambda query, **kwargs: NS(status="no_hit" if query == "ood" else "ok", reason=None),
                get_faq=record, index_status=lambda: {"ready": False})
    report = evaluate(engine, [{"query": "q1", "relevant_faq_ids": ["A", "B"]},
                               {"query": "q2", "relevant_faq_ids": ["C"]},
                               {"query": "ood", "relevant_faq_ids": [], "expected_status": "no_hit"}], "lexical")
    assert report["metrics"]["Recall@1"] == pytest.approx(.25)
    assert report["metrics"]["Recall@3"] == pytest.approx(.75)
    assert report["metrics"]["MRR@10"] == pytest.approx(.75)
    assert report["relevant_queries"] == 2 and report["rejected"] == 1
