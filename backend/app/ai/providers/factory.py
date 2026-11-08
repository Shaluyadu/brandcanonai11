'''Factory for selecting AI providers based on environment configuration.'''

import os
import logging
from typing import Tuple

from .llm_provider import OpenAICompatibleLLMProvider
from .embedding_provider import OpenAICompatibleEmbeddingProvider
from .mock_provider import MockLLMProvider, MockEmbeddingProvider
from .exceptions import ProviderError, AuthenticationError

logger = logging.getLogger("brandcanon")

class ProviderFactory:
    """Factory that creates LLM and Embedding provider instances.

    Environment variables:
        LLM_PROVIDER          (e.g. "openai") – if omitted, a mock provider is used.
        LLM_API_KEY           – required for production providers.
        LLM_MODEL             – optional, defaults in provider.
        EMBEDDING_PROVIDER    – analogous for embeddings.
        EMBEDDING_API_KEY
        EMBEDDING_MODEL
        EMBEDDING_DIMENSION
    """

    @staticmethod
    def get_llm_provider() -> Tuple[object, bool]:
        """Return an LLM provider instance and a flag indicating if it is a mock.

        Raises ProviderError if a production provider is requested but configuration is
        incomplete.
        """
        provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
        if provider_name == "openai":
            try:
                return OpenAICompatibleLLMProvider(), False
            except AuthenticationError as exc:
                raise ProviderError(str(exc))
        # Default to mock implementation
        logger.info("Using MockLLMProvider (no production LLM configuration found)")
        return MockLLMProvider(), True

    @staticmethod
    def get_embedding_provider() -> Tuple[object, bool]:
        """Return an embedding provider instance and a flag indicating if it is a mock.
        """
        provider_name = os.getenv("EMBEDDING_PROVIDER", "mock").lower()
        if provider_name == "openai":
            try:
                return OpenAICompatibleEmbeddingProvider(), False
            except AuthenticationError as exc:
                raise ProviderError(str(exc))
        logger.info("Using MockEmbeddingProvider (no production embedding configuration found)")
        return MockEmbeddingProvider(), True

