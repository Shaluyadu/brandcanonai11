'''Tests for AI provider layer.'''

import os
import json
import pytest
from unittest import mock

from app.ai.providers import (
    ProviderFactory,
    MockLLMProvider,
    MockEmbeddingProvider,
    OpenAICompatibleLLMProvider,
    OpenAICompatibleEmbeddingProvider,
    ProviderError,
    AuthenticationError,
)

# Helper to clear env vars
def clear_env(monkeypatch):
    for var in ["LLM_PROVIDER", "LLM_API_KEY", "EMBEDDING_PROVIDER", "EMBEDDING_API_KEY"]:
        monkeypatch.delenv(var, raising=False)

def test_factory_returns_mock_when_no_configuration(monkeypatch):
    clear_env(monkeypatch)
    llm, llm_is_mock = ProviderFactory.get_llm_provider()
    embed, embed_is_mock = ProviderFactory.get_embedding_provider()
    assert isinstance(llm, MockLLMProvider)
    assert isinstance(embed, MockEmbeddingProvider)
    assert llm_is_mock is True
    assert embed_is_mock is True

def test_factory_raises_error_for_missing_key_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ProviderError) as exc:
        ProviderFactory.get_llm_provider()
    assert "LLM_API_KEY not configured" in str(exc.value)

    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    with pytest.raises(ProviderError) as exc2:
        ProviderFactory.get_embedding_provider()
    assert "EMBEDDING_API_KEY not configured" in str(exc2.value)

def test_mock_llm_generate_and_structured(monkeypatch):
    provider = MockLLMProvider()
    response = provider.generate("Hello world")
    assert "Mock response" in response

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "count": {"type": "integer"},
            "flag": {"type": "boolean"},
        },
        "required": ["title", "count", "flag"],
    }
    structured = provider.generate_structured("Give me data", schema)
    assert structured["title"] == "example_title"
    assert structured["count"] == 0
    assert structured["flag"] is False

def test_mock_embedding_dimensions(monkeypatch):
    # Default dimension (8)
    provider = MockEmbeddingProvider()
    vectors = provider.embed(["a", "b"])
    assert len(vectors) == 2
    assert all(len(v) == 8 for v in vectors)

    # Custom dimension via env var
    monkeypatch.setenv("EMBEDDING_DIMENSION", "5")
    provider2 = MockEmbeddingProvider()
    vectors2 = provider2.embed(["x"])
    assert len(vectors2) == 1
    assert len(vectors2[0]) == 5

def test_openai_llm_provider_missing_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(AuthenticationError):
        OpenAICompatibleLLMProvider()

def test_openai_embedding_provider_missing_key(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    with pytest.raises(AuthenticationError):
        OpenAICompatibleEmbeddingProvider()

# Mock httpx.Client to avoid real network calls for OpenAI provider when key is present
@mock.patch("httpx.Client.post")
def test_openai_llm_generate_mock_response(mock_post, monkeypatch):
    # Provide dummy API key
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    # Mock response JSON structure
    mock_resp = mock.Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Generated text"}}]
    }
    mock_post.return_value = mock_resp

    provider = OpenAICompatibleLLMProvider()
    result = provider.generate("test prompt")
    assert result == "Generated text"

@mock.patch("httpx.Client.post")
def test_openai_embedding_embed_mock_response(mock_post, monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("EMBEDDING_API_KEY", "embed-key")
    mock_resp = mock.Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"embedding": [0.1, 0.2, 0.3]},
            {"embedding": [0.4, 0.5, 0.6]},
        ]
    }
    mock_post.return_value = mock_resp
    provider = OpenAICompatibleEmbeddingProvider()
    vectors = provider.embed(["a", "b"])
    assert vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

