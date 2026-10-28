"""Cấu hình sai phải bị từ chối trước khi khởi tạo SDK hoặc đọc key."""

from pathlib import Path

import pytest
import yaml

from hostra_ai.part1_agent_tts.knowledge.retriever import load_rag_config

ROOT = Path(__file__).resolve().parents[3]


def test_real_config_uses_app_model():
    config = load_rag_config(ROOT / "configs/app.yaml", ROOT / "configs/rag.yaml")
    assert config.embedding.model == "text-embedding-3-small"
    assert config.retrieval.default_mode == "lexical"


@pytest.mark.parametrize("section,key,value", [
    ("embedding", "dimensions", 0), ("embedding", "dimensions", "1536"),
    ("embedding", "batch_size", 0), ("embedding", "max_retries", 5),
    ("embedding", "timeout_seconds", -1.), ("retrieval", "candidate_k", 1),
    ("retrieval", "rrf_k", 0), ("retrieval", "sku_boost", .5),
    ("vector_index", "metric", "dot"), ("retrieval", "top_k", True),
])
def test_invalid_config(tmp_path, section, key, value):
    data = yaml.safe_load((ROOT / "configs/rag.yaml").read_text(encoding="utf-8"))
    data[section][key] = value
    path = tmp_path / "rag.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Cấu hình RAG"):
        load_rag_config(ROOT / "configs/app.yaml", path)


def test_missing_fields(tmp_path):
    path = tmp_path / "rag.yaml"
    path.write_text("embedding: {}", encoding="utf-8")
    with pytest.raises(ValueError):
        load_rag_config(ROOT / "configs/app.yaml", path)
