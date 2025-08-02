class RedditAdapterError(Exception):
    """Base exception for Reddit adapter errors."""
    pass

class AuthenticationError(RedditAdapterError):
    """Raised when authentication fails."""
    pass

class APIError(RedditAdapterError):
    """Raised when API requests fail."""
    pass

class RateLimitError(RedditAdapterError):
    """Raised when rate limit is exceeded."""
    pass
