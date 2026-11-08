'''Provider base classes for LLM and Embedding services.'''

import abc
from typing import List, Dict, Any


class LLMProvider(abc.ABC):
    """Abstract LLM provider interface.

    Implementations must provide a method to generate a response given a prompt and optional
    structured output schema. The method should raise a ``RuntimeError`` on failure.
    """

    @abc.abstractmethod
    def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 1024, **kwargs) -> str:
        """Generate a text completion.

        Args:
            prompt: The user‑visible prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.
            **kwargs: Provider‑specific parameters.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Any:
        """Generate a response adhering to a JSON schema.

        Returns the parsed JSON object.
        """
        raise NotImplementedError


class EmbeddingProvider(abc.ABC):
    """Abstract embedding provider interface.

    Implementations should return a list of floats representing the vector.
    """

    @abc.abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for each input text.

        Args:
            texts: List of strings.
        Returns:
            List of embedding vectors (same order as ``texts``).
        """
        raise NotImplementedError

