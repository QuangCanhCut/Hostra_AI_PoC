"""Chuẩn bị tri thức M02.1 từ dữ liệu local, không gọi API."""

from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from hostra_ai.part1_agent_tts.knowledge_engine import load_knowledge


def main() -> None:
    """In thống kê và metadata mẫu để kiểm tra nhanh dữ liệu đã chuẩn bị."""
    # Windows có thể mặc định dùng cp1252, không biểu diễn được tiếng Việt.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    engine = load_knowledge(ROOT / "shared_data/inputs/catalog_skus.json",
                            ROOT / "shared_data/inputs/product_faq.md")
    chunks = engine.list_faq_chunks()
    groups = Counter(chunk.metadata["faq_id"].split("-")[1] for chunk in chunks)
    print(f"Products: {len(engine.catalog.sku_ids)}")
    print(f"FAQ: {len(chunks)}; groups: {dict(groups)}")
    print(f"Chunks: {len(chunks)}")
    print(f"Needs review: {sum(chunk.metadata['needs_review'] for chunk in chunks)}")
    if chunks:
        print(f"Sample chunk: {chunks[0].chunk_id}; source_ref: {chunks[0].source_ref}")
        print(f"Sample metadata: {chunks[0].metadata}")
    for chunk in chunks:
        record = engine.get_faq(chunk.metadata["faq_id"])
        if record.needs_review:
            print(f"Review {record.faq_id}: {record.evidence_notes}")


if __name__ == "__main__":
    main()
