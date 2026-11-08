'''Embedding service that uses the configured EmbeddingProvider.

Provides:
- embed_text(text: str) -> List[float]
- embed_texts(texts: List[str]) -> List[List[float]]

Handles batching, empty input validation, dimension checking, retries,
and logs provider interactions.
'''

import logging
import os
import time
from typing import List

from app.ai.providers import ProviderFactory, ProviderError, AuthenticationError, RateLimitError, TimeoutError

logger = logging.getLogger("brandcanon")

# Simple exponential backoff retry decorator
def retry_on_exception(
    exceptions: tuple,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = base_delay
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error("Embedding provider failed after %s attempts: %s", attempt, exc)
                        raise
                    logger.warning(
                        "Transient embedding provider error (%s), retry %s/%s after %.2fs",
                        exc,
                        attempt,
                        max_attempts,
                        delay,
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
        return wrapper
    return decorator


class EmbeddingService:
    """Service that coordinates embedding generation via the configured provider.

    Configuration via environment variables:
        EMBEDDING_BATCH_SIZE – how many texts to embed per provider call (default 10)
        EMBEDDING_MODEL – passed to provider via its environment config, not used directly here.
    """

    def __init__(self) -> None:
        provider, is_mock = ProviderFactory.get_embedding_provider()
        self.provider = provider
        self.is_mock = is_mock
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "10"))
        self.expected_dim = getattr(self.provider, "expected_dim", None)
        logger.info(
            "EmbeddingService initialized (mock=%s, batch_size=%s, expected_dim=%s)",
            self.is_mock,
            self.batch_size,
            self.expected_dim,
        )

    @retry_on_exception((ProviderError, RateLimitError, TimeoutError))
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            raise ValueError("texts batch must not be empty")
        embeddings = self.provider.embed(texts)
        if self.expected_dim is not None:
            for vec in embeddings:
                if len(vec) != self.expected_dim:
                    raise ProviderError(
                        f"Embedding dimension mismatch: expected {self.expected_dim}, got {len(vec)}"
                    )
        return embeddings

    def embed_text(self, text: str) -> List[float]:
        if not text:
            raise ValueError("text must not be empty")
        return self._embed_batch([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            raise ValueError("texts list must not be empty")
        results: List[List[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_embeddings = self._embed_batch(batch)
            results.extend(batch_embeddings)
        return results
