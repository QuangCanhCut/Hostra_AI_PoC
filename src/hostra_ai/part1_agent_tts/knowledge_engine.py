"""Facade nạp tri thức và tìm FAQ bằng lexical retrieval, không gọi AI."""

from copy import deepcopy
from pathlib import Path
from typing import Any

from .knowledge.catalog_repository import CatalogRepository
from .knowledge.chunking import chunk_faqs
from .knowledge.faq_parser import parse_faq
from .knowledge.lexical_retriever import LexicalRetriever
from .knowledge.models import FAQChunk, FAQRecord, LexicalSearchHit
from .knowledge.models import CatalogEvidence, EvidencePackage, RagConfig, RetrievalHit
from .knowledge.embedding_provider import EmbeddingProvider
from .knowledge.retriever import KnowledgeRetriever
from .knowledge.vector_index import VectorIndex


class KnowledgeEngine:
    """Snapshot tri thức được chuẩn bị từ hai file nguồn cho một lần chạy."""

    def __init__(self, catalog_path: str | Path, faq_path: str | Path, *, source_id: str | None = None,
                 config: RagConfig | None = None, embedding_provider: EmbeddingProvider | None = None,
                 vector_index: VectorIndex | None = None):
        self.catalog = CatalogRepository(catalog_path)
        if source_id is None:
            # File trong repository dùng đường dẫn tương đối POSIX, độc lập máy chạy.
            root = Path(__file__).resolve().parents[3]
            try:
                source_id = Path(faq_path).resolve().relative_to(root).as_posix()
            except ValueError:
                # Với nguồn ngoài repo, bên gọi nên cấp source_id ổn định khi lập index.
                source_id = str(faq_path)
        records = parse_faq(faq_path, self.catalog, source_id=source_id)
        if not records:
            raise ValueError(f"Nguồn FAQ không chứa mục FAQ nào: {faq_path}")
        self._faqs = {record.faq_id: record for record in records}
        self._chunks = chunk_faqs(records)
        self._lexical = LexicalRetriever(self._chunks)
        self.config = config or RagConfig()
        self._retriever = KnowledgeRetriever(self._chunks, self.catalog, self._lexical, self.config)
        if vector_index is not None:
            if embedding_provider is None:
                raise ValueError("Inject vector index cần provider để kiểm tra model/dimensions")
            self.use_vector_index(vector_index, embedding_provider)
        elif embedding_provider is not None:
            self._retriever.provider = embedding_provider

    def get_product(self, sku_id: str) -> dict[str, Any]:
        """Tra sản phẩm theo SKU."""
        return self.catalog.get_product(sku_id)

    def get_faq(self, faq_id: str) -> FAQRecord:
        """Tra FAQ theo ID; báo lỗi rõ khi không tồn tại."""
        try:
            return self._faqs[faq_id]
        except KeyError as exc:
            raise KeyError(f"Không tìm thấy FAQ: {faq_id}") from exc

    def list_faq_chunks(self) -> list[FAQChunk]:
        """Trả bản sao chunks để bên gọi không làm thay đổi snapshot."""
        return deepcopy(self._chunks)

    def search_faq(self, query: str, top_k: int = 5,
                   sku_ids: tuple[str, ...] | None = None) -> list[LexicalSearchHit]:
        """Tìm FAQ; SKU là bộ lọc tùy chọn, không tự áp dụng active SKU."""
        return self._lexical.search(query, top_k=top_k, sku_ids=sku_ids)

    # ========================================================
    # M02.3–M02.5 — FACADE, KHÔNG CHỨA THUẬT TOÁN RETRIEVAL
    # ========================================================

    def use_vector_index(self, index: VectorIndex, provider: EmbeddingProvider) -> None:
        """Attach snapshot tương thích và bỏ cache query của provider trước đó."""
        index.check_compatibility(self._chunks, provider=provider.provider_name,
                                  model=provider.model, dimensions=provider.dimensions)
        self._retriever = KnowledgeRetriever(self._chunks, self.catalog, self._lexical, self.config,
                                             provider=provider, index=index)

    def build_vector_index(self, provider: EmbeddingProvider) -> VectorIndex:
        """Build có chủ đích qua provider được truyền vào; CLI kiểm soát --allow-api."""
        vectors = provider.embed_documents([chunk.retrieval_text for chunk in self._chunks])
        index = VectorIndex(self._chunks, vectors, provider=provider.provider_name,
                            model=provider.model, requested_dimensions=provider.dimensions)
        self.use_vector_index(index, provider)
        return index

    def load_vector_index(self, path: str | Path, provider: EmbeddingProvider) -> None:
        """Chỉ đọc index; không build hoặc embed tài liệu khi load/search."""
        index = VectorIndex.load(path, self._chunks, provider=provider.provider_name,
                                  model=provider.model, dimensions=provider.dimensions)
        self.use_vector_index(index, provider)

    def index_status(self) -> dict[str, Any]:
        """Thông tin local; lexical startup không cần SDK/key hoặc index file."""
        index = self._retriever.index
        if index is None:
            return {"ready": False}
        return {"ready": True, "provider": index.provider, "model": index.model,
                "dimension": index.dimension, "chunk_count": index.chunk_count,
                "source_fingerprint": index.fingerprint}

    def search(self, query: str, mode: str | None = None, top_k: int | None = None,
               sku_ids: tuple[str, ...] | None = None) -> list[RetrievalHit]:
        """Ứng viên FAQ thô; search_faq cũ tiếp tục giữ behavior BM25 nguyên bản."""
        return self._retriever.search(query, mode=mode or self.config.retrieval.default_mode,
            top_k=self.config.retrieval.top_k if top_k is None else top_k, sku_ids=sku_ids)

    def retrieve(self, query: str, mode: str | None = None, top_k: int | None = None,
                 sku_ids: tuple[str, ...] | None = None) -> EvidencePackage:
        """Entry point bàn giao M03, có guard OOD/ambiguity và Catalog facts."""
        return self._retriever.retrieve(query, mode=mode or self.config.retrieval.default_mode,
            top_k=self.config.retrieval.top_k if top_k is None else top_k, sku_ids=sku_ids)

    def get_catalog_evidence(self, sku_id: str, field_path: str | None = None) -> CatalogEvidence:
        """Đọc authoritative facts trực tiếp; không lấy giá từ nội dung FAQ."""
        return self.catalog.get_evidence(sku_id, field_path)


def load_knowledge(catalog_path: str | Path, faq_path: str | Path, *, source_id: str | None = None,
                   config: RagConfig | None = None, embedding_provider: EmbeddingProvider | None = None,
                   vector_index: VectorIndex | None = None) -> KnowledgeEngine:
    """Nạp tri thức từ hai đường dẫn được cung cấp, không đọc .env hoặc mạng."""
    return KnowledgeEngine(catalog_path, faq_path, source_id=source_id, config=config,
                           embedding_provider=embedding_provider, vector_index=vector_index)
