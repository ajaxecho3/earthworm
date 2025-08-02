from dataclasses import dataclass
from typing import Optional

@dataclass
class RedditConfig:
    """Configuration for Reddit adapters."""
    client_id: str
    client_secret: str
    user_agent: str
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
