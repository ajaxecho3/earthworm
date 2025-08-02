from typing import Union, Literal
from .base import RedditAdapterProtocol
from .reddit_community import RedditCommunity
from .reddit_official import RedditOfficial
from .config import RedditConfig
from .exceptions import RedditAdapterError

AdapterType = Literal["community", "official"]

class RedditAdapterFactory:
    """Factory for creating Reddit adapters."""
    
    @staticmethod
    def create_adapter(
        adapter_type: AdapterType,
        config: RedditConfig
    ) -> RedditAdapterProtocol:
        """Create a Reddit adapter instance."""
        
        if adapter_type == "community":
            return RedditCommunity(
                client_id=config.client_id,
                client_secret=config.client_secret,
                user_agent=config.user_agent
            )
        elif adapter_type == "official":
            return RedditOfficial(
                client_id=config.client_id,
                client_secret=config.client_secret,
                user_agent=config.user_agent
            )
        else:
            raise RedditAdapterError(f"Unknown adapter type: {adapter_type}")
