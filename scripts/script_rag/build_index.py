"""Build/reuse index có chủ đích; --smoke gọi API thật có giới hạn."""

import argparse
from pathlib import Path
import sys

# Khi chạy file trực tiếp, sys.path chỉ có thư mục script. Thêm project root
# để import namespace scripts hoạt động như cách chạy python -m scripts....
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.script_rag._common import engine_from_args, print_hits, provider_from_args, runtime_arguments
from hostra_ai.part1_agent_tts.knowledge.embedding_provider import EmbeddingError
from hostra_ai.part1_agent_tts.knowledge.vector_index import IndexError, VectorIndex


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Build local cosine index cho FAQ")
    runtime_arguments(parser)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="Một input ngắn, tối đa 39 FAQ, hai query semantic/hybrid")
    args = parser.parse_args()
    try:
        if args.smoke and not args.allow_api:
            raise ValueError("Live smoke cần --allow-api rõ ràng")
        engine, path = engine_from_args(args)
        config = engine.config.embedding
        if path.exists() and not args.rebuild:
            index = VectorIndex.load(path, engine.list_faq_chunks(), provider=config.provider,
                                     model=config.model, dimensions=config.dimensions)
            print(f"Reused index: {path}; model={index.model}; dimension={index.dimension}; chunks={index.chunk_count}")
            if not args.smoke:
                return 0
        elif not args.allow_api:
            print(f"DRY RUN: {len(engine.list_faq_chunks())} chunks; model={config.model}; path={path}")
            print("Dùng --allow-api để build; --rebuild để thay index cũ có chủ đích.")
            return 0
        provider = provider_from_args(args, engine)
        if args.smoke:
            if len(engine.list_faq_chunks()) > 39:
                raise ValueError("Smoke test chỉ cho tối đa 39 chunks")
            vector = provider.embed_query("Kiểm tra embedding laptop")
            print(f"Live authentication/embedding: PASS; dimensions={len(vector)}")
        if not path.exists() or args.rebuild:
            index = engine.build_vector_index(provider)
            index.save(path)
        else:
            engine.use_vector_index(index, provider)
        print(f"Index: {path}; model={index.model}; dimension={index.dimension}; chunks={index.chunk_count}")
        if args.smoke:
            for query in ("ASUS nâng RAM được không?", "Giá Lenovo bao nhiêu?"):
                for mode in ("semantic", "hybrid"):
                    print(f"Query: {query}")
                    print_hits(engine, engine.search(query, mode=mode, top_k=5))
            print("Live semantic/hybrid smoke: PASS")
        print(f"Embedding requests={provider.request_count}; total_tokens={provider.total_tokens}")
        return 0
    except (EmbeddingError, IndexError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
