"""Đọc catalog cấu trúc và truy xuất bằng SKU hoặc đường dẫn trường."""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .models import CatalogEvidence


class CatalogRepository:
    """Giữ snapshot riêng để bên gọi không thể sửa dữ liệu nguồn qua lookup."""

    def __init__(self, path: str | Path):
        self.source_file = str(path)
        try:
            with Path(path).open(encoding="utf-8") as stream:
                catalog = json.load(stream)
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise ValueError(f"Catalog JSON không hợp lệ: {path}: {exc}") from exc
        if not isinstance(catalog, dict):
            raise ValueError("Catalog phải là object")
        products = catalog.get("products")
        data_type = catalog.get("data_type")
        if not isinstance(products, list) or not products:
            raise ValueError("Catalog products phải là danh sách không rỗng")
        if not isinstance(data_type, str) or not data_type.strip():
            raise ValueError("Catalog thiếu data_type hợp lệ")
        self.data_type = data_type
        self._products: dict[str, dict[str, Any]] = {}
        for index, product in enumerate(products):
            if not isinstance(product, dict):
                raise ValueError(f"Product {index} phải là object")
            sku = product.get("sku_id")
            if not isinstance(sku, str) or not sku.strip() or sku != sku.strip():
                raise ValueError(f"Product {index} có sku_id không hợp lệ")
            if sku in self._products:
                raise ValueError(f"SKU trùng trong catalog: {sku}")
            # bool là subclass của int trong Python, nhưng không phải giá hoặc tồn kho.
            for field in ("price_vnd", "stock_quantity"):
                value = product.get(field)
                if type(value) is not int or value < 0:
                    raise ValueError(f"SKU {sku}: {field} phải là số nguyên không âm")
            specifications = product.get("specifications")
            if not isinstance(specifications, dict):
                raise ValueError(f"SKU {sku}: specifications phải là object")
            for component in ("ram", "storage"):
                details = specifications.get(component)
                if not isinstance(details, dict):
                    raise ValueError(f"SKU {sku}: specifications.{component} phải là object")
                if "upgradable" not in details or (details["upgradable"] is not None and type(details["upgradable"]) is not bool):
                    raise ValueError(f"SKU {sku}: specifications.{component}.upgradable phải là bool hoặc null")
            self._products[sku] = deepcopy(product)

    @property
    def sku_ids(self) -> tuple[str, ...]:
        """Các SKU theo thứ tự gốc trong catalog."""
        return tuple(self._products)

    def get_product(self, sku_id: str) -> dict[str, Any]:
        """Lấy bản sao sản phẩm; báo lỗi rõ nếu SKU không tồn tại."""
        if sku_id not in self._products:
            raise KeyError(f"Không tìm thấy SKU: {sku_id}")
        return deepcopy(self._products[sku_id])

    def get_evidence(self, sku_id: str, field_path: str | None = None) -> CatalogEvidence:
        """Đọc trường lồng nhau bằng đường dẫn dấu chấm, không suy diễn giá trị null.

        Ví dụ: specifications.storage.upgradable. None ở lá khác với trường thiếu.
        """
        value: Any = self.get_product(sku_id)
        if field_path is not None:
            parts = field_path.split(".")
            if not field_path or any(not part for part in parts):
                raise ValueError("field_path phải gồm các tên trường ngăn cách bởi dấu chấm")
            for part in parts:
                if not isinstance(value, dict) or part not in value:
                    raise KeyError(f"Không tìm thấy trường {field_path!r} trong SKU {sku_id}")
                value = value[part]
        return CatalogEvidence(sku_id, field_path, value, f"catalog:{sku_id}", self.data_type)
