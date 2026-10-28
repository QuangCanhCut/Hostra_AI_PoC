"""Tiện ích CLI dùng chung: cấu hình, API permission và in evidence an toàn."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from hostra_ai.part1_agent_tts.knowledge.embedding_provider import OpenAIEmbeddingProvider
from hostra_ai.part1_agent_tts.knowledge.retriever import load_rag_config
from hostra_ai.part1_agent_tts.knowledge.vector_index import VectorIndex
from hostra_ai.part1_agent_tts.knowledge_engine import load_knowledge


def runtime_arguments(parser):
    """CLI lexical không gọi load_dotenv hay tạo OpenAI client."""
    parser.add_argument("--app-config", type=Path, default=ROOT / "configs/app.yaml")
    parser.add_argument("--rag-config", type=Path, default=ROOT / "configs/rag.yaml")
    parser.add_argument("--index-path", type=Path)
    parser.add_argument("--allow-api", action="store_true", help="Cho phép gửi nội dung retrieval tới OpenAI Embeddings")


def engine_from_args(args):
    config = load_rag_config(args.app_config, args.rag_config)
    engine = load_knowledge(ROOT / "shared_data/inputs/catalog_skus.json",
                            ROOT / "shared_data/inputs/product_faq.md", config=config)
    path = args.index_path or ROOT / config.vector_index.path
    return engine, path


def provider_from_args(args, engine):
    if not args.allow_api:
        raise ValueError("Semantic/hybrid cần --allow-api; lexical vẫn chạy offline")
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
    return OpenAIEmbeddingProvider(engine.config.embedding)


def connect_index(args, engine, path):
    """Kiểm tra file local trước khi tạo client; không tự rebuild khi query."""
    config = engine.config.embedding
    index = VectorIndex.load(path, engine.list_faq_chunks(), provider=config.provider,
                             model=config.model, dimensions=config.dimensions)
    provider = provider_from_args(args, engine)
    engine.use_vector_index(index, provider)
    return provider


def print_hits(engine, hits):
    for hit in hits:
        record = engine.get_faq(hit.metadata["faq_id"])
        print(f"{hit.rank}. {hit.chunk_id} | mode={hit.mode} | score={hit.score:.4f} | {record.title}")
        print(f"   component_scores={hit.component_scores}; component_ranks={hit.component_ranks}")
        print(f"   SKU={hit.metadata['sku_ids']}; source={hit.source_ref}")
        print(f"   evidence={hit.metadata['evidence_refs']}; needs_review={hit.metadata['needs_review']}")
        print(f"   evidence_notes={hit.metadata['evidence_notes']}")
