"""Kiểm thử đọc dữ liệu catalog và truy xuất trường có nguồn."""

import json
from pathlib import Path

import pytest

from hostra_ai.part1_agent_tts.knowledge.catalog_repository import CatalogRepository

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "shared_data/inputs/catalog_skus.json"


def test_real_catalog_and_null():
    repo = CatalogRepository(CATALOG)
    assert len(repo.sku_ids) == 2 and repo.data_type == "mock"
    asus, lenovo = "LAPTOP-ASUS-001", "LAPTOP-LENOVO-002"
    assert repo.get_evidence(asus, "price_vnd").value == 26500000
    assert repo.get_evidence(lenovo, "price_vnd").value == 25690000
    assert repo.get_evidence(asus, "specifications.ram.upgradable").value is False
    evidence = repo.get_evidence(asus, "specifications.storage.upgradable")
    assert evidence.value is None and evidence.source_ref == f"catalog:{asus}"
    assert evidence.data_type == "mock"
    assert repo.get_evidence(lenovo, "specifications.ram.upgradable").value is True
    assert repo.get_evidence(lenovo, "specifications.storage.upgradable").value is True
    with pytest.raises(KeyError, match="SKU"):
        repo.get_product("UNKNOWN")
    with pytest.raises(KeyError, match="trường"):
        repo.get_evidence(asus, "specifications.unknown")


def test_lookup_is_copy_and_input_unchanged():
    original = CATALOG.read_bytes()
    repo = CatalogRepository(CATALOG)
    product = repo.get_product(repo.sku_ids[0])
    product["specifications"]["ram"]["upgradable"] = "changed"
    assert repo.get_evidence(repo.sku_ids[0], "specifications.ram.upgradable").value is False
    assert CATALOG.read_bytes() == original


@pytest.mark.parametrize("data", [[], {}, {"data_type": "mock", "products": []},
    {"data_type": "mock", "products": [42]},
    {"data_type": "mock", "products": [{"sku_id": ""}]},
    {"data_type": "mock", "products": [{"sku_id": "A"}, {"sku_id": "A"}]}])
def test_invalid_catalog(tmp_path, data):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        CatalogRepository(path)


def test_bad_json(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON"):
        CatalogRepository(path)


@pytest.mark.parametrize("field,bad", [
    ("price_vnd", "giá chữ"), ("price_vnd", "26500000"), ("price_vnd", -1),
    ("price_vnd", True), ("price_vnd", 1.0), ("price_vnd", None),
    ("stock_quantity", "10"), ("stock_quantity", -1), ("stock_quantity", False),
    ("stock_quantity", 1.5), ("stock_quantity", None),
])
def test_rejects_invalid_numeric_values(tmp_path, field, bad):
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    data["products"][0][field] = bad
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match=field):
        CatalogRepository(path)


@pytest.mark.parametrize("component,bad", [("ram", "true"), ("ram", 1),
    ("storage", "false"), ("storage", 0)])
def test_rejects_invalid_upgrade_flags(tmp_path, component, bad):
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    data["products"][0]["specifications"][component]["upgradable"] = bad
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="upgradable"):
        CatalogRepository(path)


@pytest.mark.parametrize("change", ["missing_specs", "bad_specs", "missing_ram", "bad_storage", "missing_flag"])
def test_rejects_missing_structure(tmp_path, change):
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    product = data["products"][0]
    if change == "missing_specs":
        del product["specifications"]
    elif change == "bad_specs":
        product["specifications"] = []
    elif change == "missing_ram":
        del product["specifications"]["ram"]
    elif change == "bad_storage":
        product["specifications"]["storage"] = None
    else:
        del product["specifications"]["ram"]["upgradable"]
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="specifications"):
        CatalogRepository(path)


def test_zero_and_nullable_flags_are_valid(tmp_path):
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    product = data["products"][0]
    product["price_vnd"] = product["stock_quantity"] = 0
    product["specifications"]["ram"]["upgradable"] = None
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    repo = CatalogRepository(path)
    assert repo.get_evidence(product["sku_id"], "specifications.ram.upgradable").value is None
    assert repo.get_product(product["sku_id"])["price_vnd"] == 0


def test_duplicate_valid_products_rejected(tmp_path):
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    data["products"][1]["sku_id"] = data["products"][0]["sku_id"]
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="SKU trùng"):
        CatalogRepository(path)
