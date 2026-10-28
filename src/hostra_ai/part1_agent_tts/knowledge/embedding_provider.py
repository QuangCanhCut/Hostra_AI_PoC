"""Adapter Embeddings chính thức; SDK được nạp khi tạo provider có chủ đích."""

import math
import os
from time import perf_counter
from typing import Any, Protocol

from .models import EmbeddingConfig


# ============================================================
# 1. INTERFACE VÀ KIỂM TRA VECTOR DÙNG CHUNG
# ============================================================

class EmbeddingError(RuntimeError):
    """Lỗi đã lọc thông tin nhạy cảm; code cho CLI/M03 quyết định bước xử lý."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


class EmbeddingProvider(Protocol):
    """Cho phép unit test inject provider riêng mà không dùng API key."""

    provider_name: str
    model: str
    dimensions: int | None

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


def validate_vectors(vectors: Any, *, count: int, dimensions: int | None = None) -> list[list[float]]:
    """Từ chối vector rỗng, sai số lượng/chiều, bool, NaN/Inf hoặc zero norm."""
    if not isinstance(vectors, list) or len(vectors) != count or count <= 0:
        raise ValueError("Vector count không khớp input hoặc input rỗng")
    validated = []
    expected = dimensions
    for vector in vectors:
        if not isinstance(vector, (list, tuple)) or not vector:
            raise ValueError("Vector phải là danh sách không rỗng")
        if expected is None:
            expected = len(vector)
        if len(vector) != expected:
            raise ValueError("Vector dimension không nhất quán")
        if any(type(value) not in (int, float) or not math.isfinite(value) for value in vector):
            raise ValueError("Vector chứa giá trị không hữu hạn hoặc không phải số")
        values = [float(value) for value in vector]
        norm = math.hypot(*values)
        if not math.isfinite(norm) or norm == 0:
            raise ValueError("Vector có norm bằng zero hoặc không hữu hạn")
        validated.append(values)
    return validated


# ============================================================
# 2. OPENAI PROVIDER — BATCHING, TIMEOUT VÀ LỖI CÓ THỂ XỬ LÝ
# ============================================================

class OpenAIEmbeddingProvider:
    """Không có retry ngoài SDK; không log exception gốc chứa request/credentials."""

    provider_name = "openai"

    def __init__(self, config: EmbeddingConfig, *, client: Any = None):
        self.config = config
        self.model = config.model
        self.dimensions = config.dimensions
        self.total_tokens = 0
        self.request_count = 0
        self.api_seconds = 0.0
        self._observed_dimension: int | None = config.dimensions
        if client is None:
            if not os.environ.get("OPENAI_API_KEY"):
                raise EmbeddingError("MISSING_API_KEY", "Cần OPENAI_API_KEY khi gọi embeddings API")
            from openai import OpenAI
            # Chỉ gửi credentials đến endpoint chính thức. SDK tự đọc environment.
            client = OpenAI(base_url="https://api.openai.com/v1", timeout=config.timeout_seconds,
                            max_retries=config.max_retries)
        self._client = client

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Mỗi batch một request; response.index xác định thứ tự thay vì vị trí trả về."""
        if not isinstance(texts, list) or not texts or any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError("Embedding input phải là danh sách chuỗi không rỗng")
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.config.batch_size):
            batch = texts[start:start + self.config.batch_size]
            options = {"model": self.model, "input": batch, "encoding_format": "float"}
            if self.dimensions is not None:
                options["dimensions"] = self.dimensions
            response = self._request(options)
            try:
                if response.model != self.model or len(response.data) != len(batch):
                    raise ValueError("Model hoặc response count không khớp")
                indices = [item.index for item in response.data]
                if any(type(index) is not int for index in indices) or sorted(indices) != list(range(len(batch))):
                    raise ValueError("Response indices không đầy đủ hoặc bị trùng")
                ordered = [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
                validated = validate_vectors(ordered, count=len(batch), dimensions=self._observed_dimension)
                self._observed_dimension = len(validated[0])
                vectors.extend(validated)
                usage = getattr(response, "usage", None)
                tokens = getattr(usage, "total_tokens", 0)
                if type(tokens) is int and tokens >= 0:
                    self.total_tokens += tokens
            except (ValueError, TypeError, AttributeError, OverflowError):
                raise EmbeddingError("INVALID_RESPONSE", "Embedding response sai model/count/indices/vector") from None
        return vectors

    def embed_query(self, text: str) -> list[float]:
        """Dùng cùng model và chính sách dimensions như document embeddings."""
        return self.embed_documents([text])[0]

    def _request(self, options: dict[str, Any]) -> Any:
        import openai
        self.request_count += 1
        started = perf_counter()
        try:
            return self._client.embeddings.create(**options)
        except openai.AuthenticationError:
            raise EmbeddingError("AUTHENTICATION", "API từ chối xác thực; kiểm tra key ở máy local") from None
        except openai.RateLimitError:
            raise EmbeddingError("RATE_LIMIT_OR_QUOTA", "API báo giới hạn hoặc quota/billing; dừng và kiểm tra tài khoản") from None
        except openai.APITimeoutError:
            raise EmbeddingError("TIMEOUT", "Embeddings API quá thời gian chờ") from None
        except openai.APIConnectionError:
            raise EmbeddingError("NETWORK", "Không kết nối được Embeddings API") from None
        except openai.APIError:
            raise EmbeddingError("API_ERROR", "Embeddings API không xử lý được request; kiểm tra model/config") from None
        finally:
            self.api_seconds += perf_counter() - started
