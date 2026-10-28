"""Điều phối lexical/semantic/hybrid và bàn giao evidence ứng viên cho M03."""

from copy import deepcopy
from pathlib import Path
import re

import yaml

from .catalog_repository import CatalogRepository
from .embedding_provider import EmbeddingProvider
from .lexical_retriever import LexicalRetriever, tokenize
from .models import EvidencePackage, FAQChunk, RagConfig, RetrievalHit
from .ranker import fuse_rrf
from .vector_index import VectorIndex


# ============================================================
# 1. CẤU HÌNH — MODEL CHỈ CÓ MỘT NGUỒN TẠI app.yaml
# ============================================================

def load_rag_config(app_path: str | Path, rag_path: str | Path) -> RagConfig:
    """Đọc YAML, validate trước khi tạo provider; không đọc .env ở tầng source."""
    try:
        app = yaml.safe_load(Path(app_path).read_text(encoding="utf-8"))
        rag = yaml.safe_load(Path(rag_path).read_text(encoding="utf-8"))
        if not isinstance(rag, dict) or set(rag) != {"embedding", "vector_index", "retrieval"}:
            raise ValueError("rag.yaml thiếu các section bắt buộc")
        required = {
            "embedding": {"provider", "dimensions", "batch_size", "timeout_seconds", "max_retries"},
            "vector_index": {"path", "metric"},
            "retrieval": {"default_mode", "top_k", "candidate_k", "rrf_k", "sku_boost", "no_hit_policy"},
        }
        for section, keys in required.items():
            if not isinstance(rag[section], dict) or not keys.issubset(rag[section]):
                raise ValueError(f"rag.yaml thiếu field bắt buộc trong {section}")
        if "model" in rag["embedding"]:
            raise ValueError("Tên embedding model chỉ cấu hình tại app.yaml: rag.embedding_model")
        rag["embedding"]["model"] = app["rag"]["embedding_model"]
        if isinstance(rag["retrieval"].get("domain_terms"), list):
            rag["retrieval"]["domain_terms"] = tuple(rag["retrieval"]["domain_terms"])
        return RagConfig.model_validate(rag)
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError):
        raise ValueError("Cấu hình RAG thiếu hoặc không hợp lệ; kiểm tra app.yaml và rag.yaml") from None


# ============================================================
# 2. RETRIEVAL — KHÔNG TẠO INDEX HOẶC PROVIDER NGẦM
# ============================================================

class KnowledgeRetriever:
    def __init__(self, chunks: list[FAQChunk], catalog: CatalogRepository,
                 lexical: LexicalRetriever, config: RagConfig, *,
                 provider: EmbeddingProvider | None = None, index: VectorIndex | None = None):
        self._chunks = deepcopy(chunks)
        self.catalog, self.lexical, self.config = catalog, lexical, config
        self.provider, self.index = provider, index
        self._query_cache: dict[str, list[float]] = {}

    def search(self, query: str, *, mode: str = "lexical", top_k: int = 5,
               sku_ids: tuple[str, ...] | None = None) -> list[RetrievalHit]:
        """API tìm ứng viên thô; OOD và ambiguity được xử lý bởi retrieve()."""
        if not isinstance(query, str):
            raise TypeError("query phải là chuỗi")
        if mode not in ("lexical", "semantic", "hybrid"):
            raise ValueError("mode phải là lexical, semantic hoặc hybrid")
        if type(top_k) is not int or top_k <= 0:
            raise ValueError("top_k phải là số nguyên dương")
        if sku_ids is not None and (not isinstance(sku_ids, tuple) or not sku_ids
                or any(not isinstance(sku, str) or sku not in self.catalog.sku_ids for sku in sku_ids)):
            raise ValueError("sku_ids phải là tuple SKU có trong Catalog")
        if not tokenize(query):
            return []
        candidate_k = max(top_k, self.config.retrieval.candidate_k) if mode == "hybrid" else top_k
        lexical = []
        if mode in ("lexical", "hybrid"):
            lexical = [RetrievalHit(hit.chunk_id, hit.source_ref, hit.score, hit.rank, hit.metadata,
                hit.retrieval_text, "lexical", {"lexical": hit.score}, {"lexical": hit.rank})
                for hit in self.lexical.search(query, top_k=candidate_k, sku_ids=sku_ids)]
        if mode == "lexical":
            return lexical
        if self.provider is None or self.index is None:
            raise RuntimeError("Semantic/hybrid cần embedding provider và vector index; build/load index trước")
        self.index.check_compatibility(self._chunks, provider=self.provider.provider_name,
                                      model=self.provider.model, dimensions=self.provider.dimensions)
        if query not in self._query_cache:
            vector = self.provider.embed_query(query)
            # Cache nhỏ theo engine; không ghi query người dùng ra file.
            if len(self._query_cache) >= 128:
                self._query_cache.pop(next(iter(self._query_cache)))
            self._query_cache[query] = list(vector)
        semantic = self.index.search(self._query_cache[query], top_k=candidate_k, sku_ids=sku_ids)
        if mode == "semantic":
            return semantic
        return fuse_rrf(lexical, semantic, top_k=top_k, rrf_k=self.config.retrieval.rrf_k,
                        sku_ids=sku_ids, sku_boost=self.config.retrieval.sku_boost)

    # ========================================================
    # 3. SKU VÀ CATALOG ROUTING — KHÔNG DÙNG ACTIVE SKU NGẦM
    # ========================================================

    def resolve_skus(self, query: str) -> tuple[str, ...]:
        """Chỉ nhận SKU/brand/model nêu tường minh, không phân giải 'máy đó'."""
        text = " ".join(tokenize(query))
        found = []
        for sku in self.catalog.sku_ids:
            product = self.catalog.get_product(sku)
            aliases = [sku, product.get("brand", ""), product.get("model", "")]
            if any(alias and f" {' '.join(tokenize(alias))} " in f" {text} " for alias in aliases):
                found.append(sku)
        return tuple(found)

    @staticmethod
    def _catalog_fields(query: str) -> tuple[str, ...]:
        text = " ".join(tokenize(query))
        paths = []
        if re.search(r"\bgiá\b|bao nhiêu tiền", text):
            paths.append("price_vnd")
        if any(term in text for term in ("tồn kho", "còn hàng", "có sẵn")):
            paths.append("stock_quantity")
        specifications = {
            "ram": "ram", "ssd": "storage", "ổ cứng": "storage", "cpu": "cpu", "chip": "cpu",
            "gpu": "gpu", "đồ họa": "gpu", "màn hình": "display", "oled": "display",
            "pin": "battery_wh", "cổng": "ports",
        }
        for term, field in specifications.items():
            if f" {term} " in f" {text} ":
                path = f"specifications.{field}"
                if path not in paths:
                    paths.append(path)
        if "thông số" in text or "cấu hình" in text:
            paths.append("specifications")
        return tuple(paths)

    def retrieve(self, query: str, *, mode: str = "lexical", top_k: int = 5,
                 sku_ids: tuple[str, ...] | None = None) -> EvidencePackage:
        """Gói evidence chưa xác minh: guard OOD bảo thủ + Catalog facts + FAQ hits."""
        # Validate tham số ngay cả khi guard trả sớm; lexical không có side effect mạng.
        if not isinstance(query, str) or type(top_k) is not int or top_k <= 0:
            raise ValueError("query phải là chuỗi và top_k là số nguyên dương")
        if mode not in ("lexical", "semantic", "hybrid"):
            raise ValueError("mode không hợp lệ")
        if sku_ids is not None and (not isinstance(sku_ids, tuple) or not sku_ids
                or any(sku not in self.catalog.sku_ids for sku in sku_ids)):
            raise ValueError("sku_ids không hợp lệ")
        mentioned = self.resolve_skus(query)
        resolved = sku_ids or mentioned
        text = " ".join(tokenize(query))
        def result(status, reason, hits=(), evidence=()):
            warnings = ("FAQ_NEEDS_REVIEW",) if any(h.metadata["needs_review"] for h in hits) else ()
            return EvidencePackage(query, mode, status, reason, tuple(resolved), tuple(hits), tuple(evidence), warnings)
        if sku_ids and mentioned and not set(mentioned).issubset(sku_ids):
            return result("insufficient_evidence", "SKU_SCOPE_CONFLICT")
        if not text:
            return result("no_hit", "EMPTY_QUERY")
        if not resolved and any(term in text for term in ("máy đó", "máy kia", "con kia", "con đó")):
            return result("insufficient_evidence", "AMBIGUOUS_SKU")
        domain_match = any(f" {' '.join(tokenize(term))} " in f" {text} "
                           for term in self.config.retrieval.domain_terms)
        if not domain_match and not resolved:
            return result("no_hit", "OUT_OF_DOMAIN")
        fields = self._catalog_fields(query)
        if fields and not resolved:
            return result("insufficient_evidence", "SKU_REQUIRED")
        # Khi SKU đã rõ nhưng chưa có field cụ thể, cung cấp bản ghi gốc thay vì
        # để câu hỏi so sánh hai máy chỉ có FAQ diễn giải mà thiếu Catalog đối chiếu.
        fact_paths = fields or (None,)
        facts = [self.catalog.get_evidence(sku, path) for sku in resolved for path in fact_paths]
        hits = self.search(query, mode=mode, top_k=top_k, sku_ids=tuple(resolved) or None)
        faq_ids = {chunk.metadata["faq_id"] for chunk in self._chunks}
        for hit in hits:
            if hit.source_ref != f"faq:{hit.metadata['faq_id']}" or hit.metadata["faq_id"] not in faq_ids:
                raise RuntimeError("FAQ result không có nguồn hợp lệ")
            for ref in hit.metadata["evidence_refs"]:
                if not ref.startswith("catalog:") or ref.removeprefix("catalog:") not in self.catalog.sku_ids:
                    raise RuntimeError("FAQ evidence ref không tồn tại trong Catalog")
        return result("ok" if hits or facts else "no_hit", None if hits or facts else "NO_MATCH", hits, facts)
