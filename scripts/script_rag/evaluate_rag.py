"""Đánh giá cùng labels/công thức cho ba mode; không dùng mock làm benchmark live."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from time import perf_counter

# Cho phép chạy file trực tiếp từ bất kỳ cwd nào, không phụ thuộc PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.script_rag._common import ROOT, connect_index, engine_from_args, runtime_arguments
from hostra_ai.part1_agent_tts.knowledge.embedding_provider import EmbeddingError
from hostra_ai.part1_agent_tts.knowledge.vector_index import IndexError


# ============================================================
# METRICS — OOD/AMBIGUOUS CÓ RELEVANT RỖNG ĐƯỢC ĐO RIÊNG
# ============================================================

def evaluate(engine, cases, mode, provider=None):
    """Raw search đo relevance không dùng expected SKU làm filter để tránh lộ nhãn.

    Package guards và explicit filter correctness được đo riêng. Latency API lấy
    từ provider; hybrid có thể hưởng query cache được làm nóng bởi semantic.
    """
    totals = {"Recall@1": 0.0, "Recall@3": 0.0, "Recall@5": 0.0, "MRR@10": 0.0}
    relevant_count = rejection_count = rejected = false_accept = false_reject = 0
    source_ok = source_total = sku_ok = sku_total = 0
    per_query = []
    started = perf_counter()
    api_before = getattr(provider, "api_seconds", 0.0)
    for position, case in enumerate(cases):
        relevant = set(case["relevant_faq_ids"])
        query_id = case.get("query_id", f"baseline-{position + 1:02}")
        hits = engine.search(case["query"], mode=mode, top_k=10) if relevant else []
        if relevant:
            relevant_count += 1
            for k in (1, 3, 5):
                totals[f"Recall@{k}"] += len(relevant & {hit.metadata["faq_id"] for hit in hits[:k]}) / len(relevant)
            totals["MRR@10"] += next((1 / rank for rank, hit in enumerate(hits, start=1)
                                       if hit.metadata["faq_id"] in relevant), 0.0)
        package = engine.retrieve(case["query"], mode=mode, top_k=5)
        expected_status = case.get("expected_status")
        if expected_status:
            rejection_count += 1
            rejected += package.status != "ok"
            false_accept += package.status == "ok"
        elif relevant:
            false_reject += package.status != "ok"
        for hit in hits:
            source_total += 1
            record = engine.get_faq(hit.metadata["faq_id"])
            source_ok += (hit.source_ref == f"faq:{record.faq_id}"
                and tuple(hit.metadata["evidence_refs"]) == record.evidence_refs
                and tuple(hit.metadata["evidence_notes"]) == record.evidence_notes
                and tuple(hit.metadata["sku_ids"]) == record.sku_ids
                and hit.metadata["needs_review"] == record.needs_review)
        expected_skus = tuple(case.get("expected_sku_ids", []))
        if expected_skus:
            # Chỉ phép đo filter riêng mới nhận scope từ fixture.
            filtered = engine.search(case["query"], mode=mode, top_k=5, sku_ids=expected_skus)
            sku_total += 1
            sku_ok += bool(filtered) and all(set(expected_skus).issubset(hit.metadata["sku_ids"]) for hit in filtered)
        per_query.append({"query_id": query_id, "query": case["query"], "category": case.get("category", "baseline"),
            "relevant": sorted(relevant), "top5": [hit.chunk_id for hit in hits[:5]],
            "scores5": [hit.score for hit in hits[:5]], "status": package.status, "reason": package.reason,
            "expected_status": expected_status,
            "recall3": len(relevant & {hit.chunk_id for hit in hits[:3]}) / len(relevant) if relevant else None})
    elapsed = perf_counter() - started
    api_seconds = getattr(provider, "api_seconds", 0.0) - api_before
    metrics = {name: value / relevant_count if relevant_count else None for name, value in totals.items()}
    return {"mode": mode, "metrics": metrics, "relevant_queries": relevant_count,
        "rejection_queries": rejection_count, "rejected": rejected, "false_accepts": false_accept,
        "false_rejects": false_reject, "source_integrity": [source_ok, source_total],
        "sku_filter_correctness": [sku_ok, sku_total], "seconds_total": elapsed,
        "seconds_api": api_seconds, "seconds_local_estimate": max(0, elapsed - api_seconds),
        "index_status": engine.index_status(), "per_query": per_query}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Đánh giá lexical/semantic/hybrid bằng cùng dataset")
    runtime_arguments(parser)
    parser.add_argument("--dataset", type=Path, default=ROOT / "tests/fixtures/rag/retrieval_eval.json")
    parser.add_argument("--output", type=Path, help="Lưu JSON kết quả thực đo")
    args = parser.parse_args()
    try:
        engine, path = engine_from_args(args)
        cases = json.loads(args.dataset.read_text(encoding="utf-8"))
        if not isinstance(cases, list) or not cases or len(cases) > 100:
            raise ValueError("Dataset cần 1–100 queries để evaluation có giới hạn")
        for case in cases:
            if not isinstance(case, dict) or not isinstance(case.get("query"), str) or not isinstance(case.get("relevant_faq_ids"), list):
                raise ValueError("Query hoặc relevant labels thiếu/sai")
            for faq_id in case["relevant_faq_ids"]:
                engine.get_faq(faq_id)
        reports = [evaluate(engine, cases, "lexical")]
        live_error = None
        if args.allow_api:
            try:
                provider = connect_index(args, engine, path)
                for mode in ("semantic", "hybrid"):
                    reports.append(evaluate(engine, cases, mode, provider))
                print(f"Query embedding requests={provider.request_count}; total_tokens={provider.total_tokens}")
            except (EmbeddingError, IndexError, ValueError) as exc:
                live_error = str(exc)
                print(f"Semantic/hybrid BLOCKED: {exc}")
        else:
            print("Semantic/hybrid NOT RUN: cần index tương thích và --allow-api.")
        print("Mode       Recall@1  Recall@3  Recall@5  MRR@10")
        for report in reports:
            values = report["metrics"]
            print(f"{report['mode']:10} " + "  ".join("N/A" if values[key] is None else f"{values[key]:.3f}"
                for key in ("Recall@1", "Recall@3", "Recall@5", "MRR@10")))
            print(f"  rejection={report['rejected']}/{report['rejection_queries']}; false_accept={report['false_accepts']}; false_reject={report['false_rejects']}")
            print(f"  source={report['source_integrity']}; SKU filter={report['sku_filter_correctness']}; total={report['seconds_total']:.3f}s; API={report['seconds_api']:.3f}s")
            for row in report["per_query"]:
                if (row["recall3"] is not None and row["recall3"] < 1) or (row["expected_status"] and row["status"] != row["expected_status"]):
                    print(f"  CHECK {row['query_id']}: top5={row['top5']}; status={row['status']}; Recall@3={row['recall3']}")
        if args.output:
            target = args.output.resolve()
            if target.suffix != ".json" or target == args.dataset.resolve() or ROOT / "shared_data/inputs" in target.parents:
                raise ValueError("Output phải là JSON riêng ngoài input/dataset")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"dataset": str(args.dataset), "reports": reports, "live_error": live_error},
                ensure_ascii=False, indent=2), encoding="utf-8")
        return 1 if live_error else 0
    except (OSError, ValueError, KeyError, EmbeddingError, IndexError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
