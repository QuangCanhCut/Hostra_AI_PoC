"""Demo tìm FAQ bằng BM25 hoặc đo Recall@K trên bộ câu hỏi local."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
# Namespace scripts cần project root; package hostra_ai nằm dưới src.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from hostra_ai.part1_agent_tts.knowledge_engine import load_knowledge
from scripts.script_rag._common import connect_index, engine_from_args, print_hits, runtime_arguments
from hostra_ai.part1_agent_tts.knowledge.embedding_provider import EmbeddingError
from hostra_ai.part1_agent_tts.knowledge.vector_index import IndexError


def _run() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Tìm FAQ bằng BM25 offline")
    parser.add_argument("query", nargs="?", help="Câu hỏi; bỏ trống để nhập tương tác")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--sku", action="append", help="Lọc FAQ chứa tất cả SKU được truyền")
    parser.add_argument("--eval", action="store_true", help="Đo Recall@1 và Recall@3 trên fixture")
    parser.add_argument("--mode", choices=("lexical", "semantic", "hybrid"), default="lexical")
    runtime_arguments(parser)
    args = parser.parse_args()
    if args.top_k <= 0:
        parser.error("--top-k phải là số nguyên dương")
    engine, index_path = engine_from_args(args)
    if args.mode != "lexical":
        connect_index(args, engine, index_path)
    if args.eval:
        if args.query is not None or args.sku:
            parser.error("--eval không nhận query hoặc --sku")
        cases = json.loads((ROOT / "tests/fixtures/rag/lexical_eval.json").read_text(encoding="utf-8"))
        totals = {1: 0.0, 3: 0.0}
        for case in cases:
            relevant = set(case["relevant_faq_ids"])
            if not relevant:
                raise ValueError("Mỗi câu hỏi đánh giá cần ít nhất một FAQ liên quan")
            hits = engine.search(case["query"], mode=args.mode, top_k=3)
            for k in totals:
                totals[k] += len(relevant & {hit.chunk_id for hit in hits[:k]}) / len(relevant)
            print(f"{case['query']} | expected={sorted(relevant)} | top3={[hit.chunk_id for hit in hits]}")
        if not cases:
            raise ValueError("Bộ đánh giá không được rỗng")
        print(f"Macro Recall@1: {totals[1] / len(cases):.3f}; Recall@3: {totals[3] / len(cases):.3f}; queries: {len(cases)}")
        return
    query = args.query if args.query is not None else input("Câu hỏi: ")
    hits = engine.search(query, mode=args.mode, top_k=args.top_k, sku_ids=tuple(args.sku) if args.sku else None)
    if not hits:
        print("Không tìm thấy FAQ có từ khóa khớp.")
    print_hits(engine, hits)


def main() -> int:
    try:
        _run()
        return 0
    except (EmbeddingError, IndexError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
