"""Demo tìm FAQ bằng BM25 hoặc đo Recall@K trên bộ câu hỏi local."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from hostra_ai.part1_agent_tts.knowledge_engine import load_knowledge


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Tìm FAQ bằng BM25 offline")
    parser.add_argument("query", nargs="?", help="Câu hỏi; bỏ trống để nhập tương tác")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--sku", action="append", help="Lọc FAQ chứa tất cả SKU được truyền")
    parser.add_argument("--eval", action="store_true", help="Đo Recall@1 và Recall@3 trên fixture")
    args = parser.parse_args()
    if args.top_k <= 0:
        parser.error("--top-k phải là số nguyên dương")
    engine = load_knowledge(ROOT / "shared_data/inputs/catalog_skus.json", ROOT / "shared_data/inputs/product_faq.md")
    if args.eval:
        if args.query is not None or args.sku:
            parser.error("--eval không nhận query hoặc --sku")
        cases = json.loads((ROOT / "tests/fixtures/rag/lexical_eval.json").read_text(encoding="utf-8"))
        totals = {1: 0.0, 3: 0.0}
        for case in cases:
            relevant = set(case["relevant_faq_ids"])
            if not relevant:
                raise ValueError("Mỗi câu hỏi đánh giá cần ít nhất một FAQ liên quan")
            hits = engine.search_faq(case["query"], top_k=3)
            for k in totals:
                totals[k] += len(relevant & {hit.chunk_id for hit in hits[:k]}) / len(relevant)
            print(f"{case['query']} | expected={sorted(relevant)} | top3={[hit.chunk_id for hit in hits]}")
        if not cases:
            raise ValueError("Bộ đánh giá không được rỗng")
        print(f"Macro Recall@1: {totals[1] / len(cases):.3f}; Recall@3: {totals[3] / len(cases):.3f}; queries: {len(cases)}")
        return
    query = args.query if args.query is not None else input("Câu hỏi: ")
    hits = engine.search_faq(query, args.top_k, tuple(args.sku) if args.sku else None)
    if not hits:
        print("Không tìm thấy FAQ có từ khóa khớp.")
    for hit in hits:
        record = engine.get_faq(hit.metadata["faq_id"])
        print(f"{hit.rank}. {hit.chunk_id} | BM25={hit.score:.4f} | {record.title}")
        print(f"   SKU={hit.metadata['sku_ids']} | source={hit.source_ref}")
        print(f"   evidence={hit.metadata['evidence_refs']} | needs_review={hit.metadata['needs_review']}")
        if hit.metadata["evidence_notes"]:
            print(f"   evidence_notes={hit.metadata['evidence_notes']}")


if __name__ == "__main__":
    main()
