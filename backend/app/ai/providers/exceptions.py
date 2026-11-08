'''Provider specific exception hierarchy.'''

class ProviderError(Exception):
    """Base class for all provider‑related errors."""

class AuthenticationError(ProviderError):
    """Raised when credentials are missing or invalid."""

class RateLimitError(ProviderError):
    """Raised when the provider returns a rate‑limit response."""

class TimeoutError(ProviderError):
    """Raised when a request times out or the provider is unreachable."""

