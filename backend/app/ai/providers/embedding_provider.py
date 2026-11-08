'''Embedding provider concrete implementation using OpenAI-compatible API.'''

import os
import json
import logging
from typing import List, Dict, Any

import httpx
from pydantic import BaseModel, ValidationError

from .base import EmbeddingProvider
from .exceptions import ProviderError, AuthenticationError, RateLimitError, TimeoutError

logger = logging.getLogger("brandcanon")

class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """Embedding provider that talks to an OpenAI‑compatible endpoint.

    Environment variables:
        EMBEDDING_API_BASE (default: https://api.openai.com/v1)
        EMBEDDING_API_KEY (required)
        EMBEDDING_MODEL   (default: text-embedding-3-large)
        EMBEDDING_DIMENSION (optional, int) – if set, validates the returned vector size.
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("EMBEDDING_API_BASE", "https://api.openai.com/v1")
        self.api_key = os.getenv("EMBEDDING_API_KEY")
        if not self.api_key:
            raise AuthenticationError("EMBEDDING_API_KEY not configured")
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        dim = os.getenv("EMBEDDING_DIMENSION")
        self.expected_dim: int | None = int(dim) if dim else None
        self.client = httpx.Client(timeout=30.0)

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = self.client.post(url, headers=headers, json=payload)
        except httpx.RequestError as exc:
            logger.error("Embedding request error: %s", exc)
            raise TimeoutError(str(exc)) from exc
        if response.status_code == 401:
            raise AuthenticationError("Invalid embedding credentials")
        if response.status_code == 429:
            raise RateLimitError("Embedding rate limit exceeded")
        if response.status_code >= 500:
            raise ProviderError(f"Embedding service error {response.status_code}: {response.text}")
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise ProviderError("Unable to decode embedding response as JSON") from exc

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            raise ValueError("texts list must not be empty")
        payload = {
            "model": self.model,
            "input": texts,
        }
        resp = self._post("embeddings", payload)
        try:
            data = [item["embedding"] for item in resp["data"]]
        except (KeyError, TypeError) as exc:
            raise ProviderError("Unexpected embedding response structure") from exc
        # Validate dimensions if configured
        if self.expected_dim is not None:
            for vec in data:
                if len(vec) != self.expected_dim:
                    raise ProviderError(
                        f"Embedding dimension mismatch: expected {self.expected_dim}, got {len(vec)}"
                    )
        return data

