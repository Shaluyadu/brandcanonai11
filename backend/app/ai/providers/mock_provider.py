'''Mock provider implementations for deterministic testing.'''

import json
import logging
from typing import Any, Dict, List

from .base import LLMProvider, EmbeddingProvider
from .exceptions import ProviderError

logger = logging.getLogger("brandcanon")

class MockLLMProvider(LLMProvider):
    """A deterministic mock LLM used in unit tests.

    - ``generate`` echoes the prompt with a fixed suffix.
    - ``generate_structured`` returns a JSON object that matches the supplied schema
      using simple placeholder values based on the property type.
    """

    def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 1024, **kwargs) -> str:
        logger.debug("MockLLMProvider generate called with prompt: %s", prompt)
        return f"Mock response to: {prompt[:30]}"

    def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Any:
        logger.debug("MockLLMProvider generate_structured called with prompt: %s and schema: %s", prompt, schema)
        # Very simple placeholder generation: for each property, return a dummy value based on type.
        properties = schema.get("properties", {})
        result: Dict[str, Any] = {}
        for name, prop in properties.items():
            typ = prop.get("type", "string")
            if typ == "string":
                result[name] = f"example_{name}"
            elif typ == "integer":
                result[name] = 0
            elif typ == "number":
                result[name] = 0.0
            elif typ == "boolean":
                result[name] = False
            elif typ == "array":
                result[name] = []
            elif typ == "object":
                result[name] = {}
            else:
                result[name] = None
        return result

class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic mock embedding provider.

    Returns a fixed‑size vector of zeros for each input text, preserving order.
    The dimension can be configured via the ``EMBEDDING_DIMENSION`` env var; defaults to 8.
    """

    def __init__(self) -> None:
        import os
        dim = os.getenv("EMBEDDING_DIMENSION")
        self.dim = int(dim) if dim else 8

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            raise ValueError("texts list must not be empty")
        # Return zero vectors of the configured dimension.
        return [[0.0] * self.dim for _ in texts]

