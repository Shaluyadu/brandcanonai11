"""Domain‑specific exceptions for the Suggestion Generation Engine.

These are used to provide clear error messages to the API layer and the worker
without exposing internal stack traces.
"""

class SuggestionGenerationError(Exception):
    """Base class for all suggestion‑generation errors."""
    pass

class FindingNotFoundError(SuggestionGenerationError):
    """Raised when a requested finding does not exist or does not belong to the organisation."""
    pass

class EvidenceValidationError(SuggestionGenerationError):
    """Raised when referenced evidence fails validation (missing, not approved, outdated, etc.)."""
    pass

class ProviderError(SuggestionGenerationError):
    """Raised when the LLM provider returns an error or malformed response."""
    pass

class GenerationPolicyError(SuggestionGenerationError):
    """Raised when the policy for a particular verification status disallows generation."""
    pass

