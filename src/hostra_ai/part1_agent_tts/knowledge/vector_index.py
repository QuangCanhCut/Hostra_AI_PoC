"""Local exact cosine index cho corpus nhỏ; JSON có manifest và checksum."""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any

from .embedding_provider import validate_vectors
from .models import FAQChunk, IndexManifest, RetrievalHit


# ============================================================
# 1. FINGERPRINT VÀ VALIDATION SNAPSHOT
# ============================================================

INDEX_CONFIGURATION = {"metric": "cosine", "chunking": "one-faq-one-chunk-v1"}


class IndexError(RuntimeError):
    """Index thiếu/hỏng/cũ phải được rebuild có chủ đích, không gọi API tự động."""


def _digest(data: Any) -> str:
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def knowledge_fingerprint(chunks: list[FAQChunk]) -> str:
    """Hash cả nội dung và metadata nguồn/review; độc lập thứ tự truyền vào."""
    return _digest([asdict(chunk) for chunk in sorted(chunks, key=lambda item: item.chunk_id)])


def _validate_chunks(chunks: list[FAQChunk]) -> None:
    if not chunks or len({chunk.chunk_id for chunk in chunks}) != len(chunks):
        raise ValueError("Chunks rỗng hoặc duplicate chunk IDs")
    for chunk in chunks:
        metadata = chunk.metadata
        if not chunk.retrieval_text.strip() or not isinstance(metadata, dict):
            raise ValueError("Chunk thiếu nội dung/metadata")
        if (not isinstance(metadata.get("faq_id"), str) or chunk.chunk_id != metadata["faq_id"]
                or chunk.source_ref != f"faq:{metadata['faq_id']}"):
            raise ValueError("Chunk thiếu FAQ ID hoặc source_ref không khớp")
        if not isinstance(metadata.get("source_file"), str) or not metadata["source_file"]:
            raise ValueError("Chunk thiếu source_file")
        for key in ("sku_ids", "evidence_refs", "evidence_notes"):
            values = metadata.get(key)
            if not isinstance(values, (list, tuple)) or any(not isinstance(value, str) for value in values):
                raise ValueError(f"Chunk thiếu hoặc sai {key}")
        if type(metadata.get("needs_review")) is not bool:
            raise ValueError("Chunk thiếu needs_review")


# ============================================================
# 2. EXACT COSINE SEARCH VÀ COMPATIBILITY
# ============================================================

class VectorIndex:
    """Snapshot riêng của chunks/vectors; query không làm thay đổi index."""

    def __init__(self, chunks: list[FAQChunk], vectors: list[list[float]], *,
                 provider: str, model: str, requested_dimensions: int | None = None):
        _validate_chunks(chunks)
        if not provider.strip() or not model.strip():
            raise ValueError("Index phải ghi provider và model")
        if requested_dimensions is not None and (type(requested_dimensions) is not int or requested_dimensions <= 0):
            raise ValueError("requested_dimensions phải là số nguyên dương hoặc None")
        self._chunks = deepcopy(chunks)
        self._vectors = validate_vectors(vectors, count=len(chunks), dimensions=requested_dimensions)
        self._unit_vectors = []
        for vector in self._vectors:
            norm = math.hypot(*vector)
            self._unit_vectors.append([value / norm for value in vector])
        self.provider, self.model = provider, model
        self.dimension = len(self._vectors[0])
        self.requested_dimensions = requested_dimensions
        self.fingerprint = knowledge_fingerprint(self._chunks)
        self.built_at = datetime.now(timezone.utc)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def check_compatibility(self, chunks: list[FAQChunk], *, provider: str, model: str,
                            dimensions: int | None) -> None:
        """Bắt stale sources và cả thay đổi policy dimensions, kể cả None vs số cụ thể."""
        if provider != self.provider or model != self.model or dimensions != self.requested_dimensions:
            raise IndexError("Index khác provider/model/dimensions; cần rebuild")
        if knowledge_fingerprint(chunks) != self.fingerprint:
            raise IndexError("Stale knowledge fingerprint; cần rebuild index")

    def search(self, query_vector: list[float], top_k: int = 5,
               sku_ids: tuple[str, ...] | None = None) -> list[RetrievalHit]:
        """Cosine giảm dần, đồng điểm theo chunk_id; filter ALL giống BM25."""
        if type(top_k) is not int or top_k <= 0:
            raise ValueError("top_k phải là số nguyên dương")
        if sku_ids is not None and (not isinstance(sku_ids, tuple) or not sku_ids
                or any(not isinstance(sku, str) or not sku.strip() for sku in sku_ids)):
            raise ValueError("sku_ids phải là tuple SKU không rỗng")
        query = validate_vectors([query_vector], count=1, dimensions=self.dimension)[0]
        norm = math.hypot(*query)
        unit = [value / norm for value in query]
        candidates = []
        for chunk, vector in zip(self._chunks, self._unit_vectors):
            if sku_ids and not set(sku_ids).issubset(chunk.metadata["sku_ids"]):
                continue
            similarity = max(-1.0, min(1.0, math.fsum(a * b for a, b in zip(unit, vector))))
            candidates.append((similarity, chunk))
        candidates.sort(key=lambda pair: (-pair[0], pair[1].chunk_id))
        return [RetrievalHit(chunk.chunk_id, chunk.source_ref, score, rank, deepcopy(chunk.metadata),
                             chunk.retrieval_text, "semantic", {"semantic": score}, {"semantic": rank})
                for rank, (score, chunk) in enumerate(candidates[:top_k], start=1)]

    # ========================================================
    # 3. PERSISTENCE — MỘT FILE, GHI TẠM RỒI ATOMIC REPLACE
    # ========================================================

    def save(self, path: str | Path) -> None:
        """Chỉ lưu tên index.json; cấm ghi vào cây shared_data/inputs."""
        path = Path(path).resolve()
        if path.name != "index.json" or any(p.name == "inputs" and p.parent.name == "shared_data" for p in path.parents):
            raise IndexError("Chỉ lưu index.json ngoài shared_data/inputs")
        payload = {"chunks": [asdict(chunk) for chunk in self._chunks], "vectors": self._vectors}
        manifest = IndexManifest(provider=self.provider, model=self.model, dimension=self.dimension,
            requested_dimensions=self.requested_dimensions, source_fingerprint=self.fingerprint,
            payload_sha256=_digest(payload), chunk_count=self.chunk_count,
            configuration=INDEX_CONFIGURATION, built_at=self.built_at)
        document = {"manifest": manifest.model_dump(mode="json"), **payload}
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as stream:
                temp_path = Path(stream.name)
                json.dump(document, stream, ensure_ascii=False, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    @classmethod
    def load(cls, path: str | Path, chunks: list[FAQChunk], *, provider: str, model: str,
             dimensions: int | None) -> "VectorIndex":
        """Validate toàn bộ file trước khi attach; không tự sửa index lỗi."""
        try:
            document = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(document, dict) or set(document) != {"manifest", "chunks", "vectors"}:
                raise ValueError("Index thiếu manifest/chunks/vectors")
            manifest = IndexManifest.model_validate_json(json.dumps(document["manifest"]))
            if manifest.configuration != INDEX_CONFIGURATION:
                raise ValueError("Index configuration không tương thích")
            payload = {"chunks": document["chunks"], "vectors": document["vectors"]}
            if _digest(payload) != manifest.payload_sha256:
                raise ValueError("Index payload checksum không khớp")
            loaded_chunks = []
            for raw in document["chunks"]:
                chunk = FAQChunk(**raw)
                # JSON biến tuple thành list; phục hồi kiểu metadata như snapshot chuẩn bị.
                for key in ("sku_ids", "evidence_refs", "evidence_notes"):
                    if isinstance(chunk.metadata.get(key), list):
                        chunk.metadata[key] = tuple(chunk.metadata[key])
                loaded_chunks.append(chunk)
            index = cls(loaded_chunks, document["vectors"], provider=manifest.provider,
                        model=manifest.model, requested_dimensions=manifest.requested_dimensions)
            if (index.dimension != manifest.dimension or index.chunk_count != manifest.chunk_count
                    or index.fingerprint != manifest.source_fingerprint):
                raise ValueError("Index manifest không khớp nội dung")
            index.check_compatibility(chunks, provider=provider, model=model, dimensions=dimensions)
            index.built_at = manifest.built_at
            return index
        except IndexError:
            raise
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            raise IndexError("Index thiếu/hỏng/metadata không hợp lệ; cần build hoặc --rebuild") from None
