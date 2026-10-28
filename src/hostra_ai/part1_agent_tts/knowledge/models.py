"""Các mô hình nội bộ cho bước chuẩn bị tri thức, không phải public contract."""

from dataclasses import dataclass, field
from typing import Any

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


@dataclass(frozen=True)
class FAQRecord:
    """Một mục FAQ cùng nội dung Markdown và thông tin nguồn chưa xác minh."""

    faq_id: str
    title: str
    sku_ids: tuple[str, ...]
    question: str
    answer_suggestion: str
    follow_up: str
    evidence_refs: tuple[str, ...]
    evidence_raw: str
    evidence_notes: tuple[str, ...]
    needs_review: bool
    source_file: str


@dataclass(frozen=True)
class FAQChunk:
    """Một đơn vị truy xuất, giữ trọn câu hỏi và câu trả lời của FAQ."""

    chunk_id: str
    retrieval_text: str
    metadata: dict[str, Any]
    source_ref: str


@dataclass(frozen=True)
class LexicalSearchHit:
    """Kết quả truy xuất nội bộ; score không phải xác suất hoặc xác minh."""

    chunk_id: str
    source_ref: str
    score: float
    rank: int
    metadata: dict[str, Any]
    retrieval_text: str


@dataclass(frozen=True)
class CatalogEvidence:
    """Giá trị đọc trực tiếp từ catalog, có thể là None nếu nguồn ghi null."""

    sku_id: str
    field_path: str | None
    value: Any
    source_ref: str
    data_type: str


# ============================================================
# 1. CẤU HÌNH NỘI BỘ — KHÔNG THAY ĐỔI PUBLIC DATA CONTRACTS
# ============================================================

class EmbeddingConfig(BaseModel):
    """Model do app.yaml cung cấp; tham số vận hành lấy từ rag.yaml."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    provider: Literal["openai"] = "openai"
    model: str = Field(default="text-embedding-3-small", min_length=1)
    dimensions: int | None = Field(default=None, gt=0)
    batch_size: int = Field(default=32, ge=1, le=128)
    timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    max_retries: int = Field(default=1, ge=0, le=2)


class VectorIndexConfig(BaseModel):
    """Một file JSON chứa manifest, chunks và vectors; chưa cần vector server."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    path: str = Field(default="shared_data/indexes/rag/index.json", min_length=1)
    metric: Literal["cosine"] = "cosine"


class RetrievalConfig(BaseModel):
    """Giới hạn candidates, RRF và heuristic từ chối phải nhìn thấy trong config."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    default_mode: Literal["lexical", "semantic", "hybrid"] = "lexical"
    top_k: int = Field(default=5, gt=0, le=100)
    candidate_k: int = Field(default=20, gt=0, le=100)
    rrf_k: int = Field(default=60, ge=1, le=1000)
    sku_boost: float = Field(default=0.05, ge=0, le=0.1)
    no_hit_policy: Literal["domain_terms"] = "domain_terms"
    domain_terms: tuple[str, ...] = (
        "laptop", "máy", "giá", "ram", "ssd", "cpu", "gpu", "pin", "màn hình",
        "docker", "it", "nâng cấp", "ngân sách", "bảo hành", "trả góp", "fps",
        "game", "mua", "chơi game", "freeship", "webcam", "cổng", "học", "thiết kế",
    )

    @model_validator(mode="after")
    def validate_limits(self):
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k phải >= top_k")
        if not self.domain_terms or any(not term.strip() for term in self.domain_terms):
            raise ValueError("domain_terms phải có từ khóa không rỗng")
        return self


class RagConfig(BaseModel):
    """Cấu hình của M02; mặc định vẫn khởi động hoàn toàn offline."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vector_index: VectorIndexConfig = Field(default_factory=VectorIndexConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)


# ============================================================
# 2. INDEX MANIFEST VÀ KẾT QUẢ BÀN GIAO CHO M03
# ============================================================

class IndexManifest(BaseModel):
    """Kiểm tra compatibility trước khi dùng vectors; thời gian build có múi giờ."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal[1] = 1
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    dimension: int = Field(gt=0)
    requested_dimensions: int | None
    source_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    payload_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    chunk_count: int = Field(gt=0)
    configuration: dict[str, str]
    built_at: AwareDatetime


@dataclass(frozen=True)
class RetrievalHit:
    """Score tùy mode; component ranks/scores dùng debug, không phải confidence."""

    chunk_id: str
    source_ref: str
    score: float
    rank: int
    metadata: dict[str, Any]
    retrieval_text: str
    mode: str
    component_scores: dict[str, float] = field(default_factory=dict)
    component_ranks: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidencePackage:
    """Các nguồn ứng viên cho Agent; status ok chưa có nghĩa claim được xác minh."""

    query: str
    mode: str
    status: Literal["ok", "no_hit", "insufficient_evidence"]
    reason: str | None
    sku_ids: tuple[str, ...]
    faq_hits: tuple[RetrievalHit, ...]
    catalog_evidence: tuple[CatalogEvidence, ...]
    warnings: tuple[str, ...] = ()
