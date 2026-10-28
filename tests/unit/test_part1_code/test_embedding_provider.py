"""Test adapter bằng SDK mock; không gửi request mạng hoặc dùng key thật."""

from types import SimpleNamespace as NS
from unittest.mock import Mock

import httpx
import openai
import pytest

from hostra_ai.part1_agent_tts.knowledge.embedding_provider import EmbeddingError, OpenAIEmbeddingProvider
from hostra_ai.part1_agent_tts.knowledge.models import EmbeddingConfig


def response(vectors, indices=None, model="test-model"):
    indices = list(range(len(vectors))) if indices is None else indices
    return NS(model=model, data=[NS(index=i, embedding=v) for i, v in zip(indices, vectors)], usage=NS(total_tokens=4))


def provider(client):
    return OpenAIEmbeddingProvider(EmbeddingConfig(model="test-model", dimensions=2, batch_size=2), client=client)


def test_batches_and_response_order(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = Mock()
    client.embeddings.create.side_effect = [response([[0., 1.], [1., 0.]], [1, 0]), response([[1., 1.]])]
    adapter = provider(client)
    assert adapter.embed_documents(["một", "hai", "ba"]) == [[1., 0.], [0., 1.], [1., 1.]]
    assert [call.kwargs["input"] for call in client.embeddings.create.call_args_list] == [["một", "hai"], ["ba"]]
    assert adapter.request_count == 2 and adapter.total_tokens == 8


@pytest.mark.parametrize("value", [[], [""], ["  "], [None], "text"])
def test_empty_input(value):
    client = Mock()
    with pytest.raises(ValueError):
        provider(client).embed_documents(value)
    client.embeddings.create.assert_not_called()


@pytest.mark.parametrize("reply", [response([]), response([[1.]]), response([[0., 0.]]),
    response([[float("nan"), 1.]]), response([[float("inf"), 1.]]),
    response([[True, 1.]]), response([[1., 1.]], [1]), response([[1., 1.]], model="wrong")])
def test_invalid_response(reply):
    client = Mock()
    client.embeddings.create.return_value = reply
    with pytest.raises(EmbeddingError, match="INVALID_RESPONSE"):
        provider(client).embed_query("ram")


def test_dimension_consistency_without_explicit_dimensions():
    client = Mock()
    client.embeddings.create.side_effect = [response([[1., 0.]]), response([[1., 0., 1.]])]
    adapter = OpenAIEmbeddingProvider(EmbeddingConfig(model="test-model"), client=client)
    adapter.embed_query("ram")
    with pytest.raises(EmbeddingError, match="INVALID_RESPONSE"):
        adapter.embed_query("ssd")


@pytest.mark.parametrize("kind,code", [("auth", "AUTHENTICATION"), ("rate", "RATE_LIMIT_OR_QUOTA"),
    ("timeout", "TIMEOUT"), ("network", "NETWORK"), ("bad", "API_ERROR")])
def test_sdk_errors_sanitized(kind, code):
    request = httpx.Request("POST", "https://api.openai.com/v1/embeddings")
    reply = httpx.Response(401, request=request)
    errors = {
        "auth": openai.AuthenticationError("SECRET-MUST-NOT-LEAK", response=reply, body=None),
        "rate": openai.RateLimitError("SECRET-MUST-NOT-LEAK", response=reply, body=None),
        "timeout": openai.APITimeoutError(request=request),
        "network": openai.APIConnectionError(request=request),
        "bad": openai.BadRequestError("SECRET-MUST-NOT-LEAK", response=reply, body=None),
    }
    client = Mock()
    client.embeddings.create.side_effect = errors[kind]
    with pytest.raises(EmbeddingError, match=code) as error:
        provider(client).embed_query("ram")
    assert "SECRET" not in str(error.value)
    assert client.embeddings.create.call_count == 1  # Adapter không retry chồng SDK.


def test_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(EmbeddingError, match="MISSING_API_KEY"):
        OpenAIEmbeddingProvider(EmbeddingConfig())


def test_sdk_configuration_without_request(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-key")
    factory = Mock()
    monkeypatch.setattr(openai, "OpenAI", factory)
    OpenAIEmbeddingProvider(EmbeddingConfig(timeout_seconds=12.0, max_retries=0))
    assert factory.call_args.kwargs["timeout"] == 12.0
    assert factory.call_args.kwargs["max_retries"] == 0
    assert "api_key" not in factory.call_args.kwargs
    assert "test-only-key" not in capsys.readouterr().out
