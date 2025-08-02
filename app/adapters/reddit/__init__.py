"""Reddit adapters package for earthworm application."""

from .base import RedditAdapterProtocol
from .reddit_community import RedditCommunity
from .reddit_official import RedditOfficial
from .config import RedditConfig
from .factory import RedditAdapterFactory
from .exceptions import (
    RedditAdapterError,
    AuthenticationError,
    APIError,
    RateLimitError
)

__version__ = "1.0.0"

__all__ = [
    "RedditAdapterProtocol",
    "RedditCommunity", 
    "RedditOfficial",
    "RedditConfig",
    "RedditAdapterFactory",
    "RedditAdapterError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
]