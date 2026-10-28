"""Facade nạp tri thức và tìm FAQ bằng lexical retrieval, không gọi AI."""

from copy import deepcopy
from pathlib import Path
from typing import Any

from .knowledge.catalog_repository import CatalogRepository
from .knowledge.chunking import chunk_faqs
from .knowledge.faq_parser import parse_faq
from .knowledge.lexical_retriever import LexicalRetriever
from .knowledge.models import FAQChunk, FAQRecord, LexicalSearchHit


class KnowledgeEngine:
    """Snapshot tri thức được chuẩn bị từ hai file nguồn cho một lần chạy."""

    def __init__(self, catalog_path: str | Path, faq_path: str | Path, *, source_id: str | None = None):
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


def load_knowledge(catalog_path: str | Path, faq_path: str | Path, *, source_id: str | None = None) -> KnowledgeEngine:
    """Nạp tri thức từ hai đường dẫn được cung cấp, không đọc .env hoặc mạng."""
    return KnowledgeEngine(catalog_path, faq_path, source_id=source_id)
