"""Thiết lập test offline, thư mục tạm Windows và provider giả cho kiểm thử luồng."""

import hashlib
import os
from pathlib import Path
import shutil
import socket
from uuid import uuid4
import warnings

import pytest


# ============================================================
# 1. THƯ MỤC TẠM RIÊNG CHO MỖI PHIÊN PYTEST TRÊN WINDOWS
# ============================================================

_SESSION_TEMP = pytest.StashKey[Path]()


def pytest_configure(config):
    """Tránh thư mục Temp/pytest-of-... cũ bị lỗi quyền giữa các tài khoản.

    Không sửa TEMP/TMP toàn máy. --basetemp do người dùng cấp vẫn được ưu tiên.
    Mỗi phiên dùng UUID riêng để pytest không phải xóa/dùng lại thư mục phiên khác.
    """
    if os.name != "nt" or config.option.basetemp is not None:
        return
    workspace = Path(__file__).resolve().parents[1]
    temp_root = (workspace / ".pytest-temp").resolve()
    if not temp_root.is_relative_to(workspace):
        raise pytest.UsageError(".pytest-temp phải nằm trong workspace; kiểm tra symlink hoặc dùng --basetemp")
    temp_root.mkdir(exist_ok=True)
    session_temp = temp_root / f"run-{uuid4().hex}"
    config.option.basetemp = str(session_temp)
    config.stash[_SESSION_TEMP] = session_temp


def pytest_unconfigure(config):
    """Chỉ dọn thư mục của phiên này, không đụng các thư mục pytest cũ bị lỗi quyền."""
    session_temp = config.stash.get(_SESSION_TEMP, None)
    if session_temp is None or not session_temp.exists():
        return
    workspace = Path(__file__).resolve().parents[1]
    # Kiểm tra đường dẫn thật trước khi xóa đệ quy, kể cả khi có symlink bất thường.
    if session_temp.is_symlink() or not session_temp.resolve().is_relative_to(workspace / ".pytest-temp"):
        warnings.warn("Bỏ qua dọn thư mục test vì đường dẫn đã thay đổi", RuntimeWarning)
        return
    try:
        shutil.rmtree(session_temp)
    except OSError:
        warnings.warn(f"Test đã kết thúc nhưng chưa dọn được thư mục tạm: {session_temp}", RuntimeWarning)


# ============================================================
# 2. TEST OFFLINE KHÔNG ĐƯỢC MỞ KẾT NỐI MẠNG
# ============================================================


@pytest.fixture(autouse=True)
def block_network_in_offline_tests(monkeypatch):
    """Toàn bộ suite mặc định phải chạy offline, kể cả máy đang có API key."""
    def forbidden(*args, **kwargs):
        raise AssertionError("Test offline không được mở kết nối mạng")
    monkeypatch.setattr(socket.socket, "connect", forbidden)


# ============================================================
# 3. PROVIDER GIẢ — CHỈ KIỂM THỬ LUỒNG, KHÔNG ĐO CHẤT LƯỢNG
# ============================================================

class MockEmbeddingProvider:
    provider_name = "test"
    model = "mock-embedding-v1"
    dimensions = 8

    def __init__(self):
        self.document_calls = 0
        self.query_calls = 0

    @staticmethod
    def _vector(text):
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [float(value + 1) for value in digest[:8]]

    def embed_documents(self, texts):
        self.document_calls += 1
        return [self._vector(text) for text in texts]

    def embed_query(self, text):
        self.query_calls += 1
        return self._vector(text)


@pytest.fixture
def mock_embeddings():
    return MockEmbeddingProvider()
