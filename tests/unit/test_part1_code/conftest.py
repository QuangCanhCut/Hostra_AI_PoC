"""Các fixture dùng chung để đọc policy và 20 bình luận mẫu."""

from pathlib import Path

import pytest

from hostra_ai.part1_agent_tts.comment_ingest import ingest_comments, load_catalog_skus
from hostra_ai.part1_agent_tts.comment_policy import load_policy

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def policy():
    return load_policy(ROOT / "configs/comment_policy.yaml")


@pytest.fixture
def events():
    return ingest_comments(ROOT / "shared_data/inputs/mock_comments.json", run_id="RUN-001",
                           catalog_skus=load_catalog_skus(ROOT / "shared_data/inputs/catalog_skus.json"))
