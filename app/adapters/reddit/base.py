from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class RedditAdapterProtocol(ABC):
    """Protocol/Interface for Reddit adapters."""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the Reddit API."""
        pass
    
    @abstractmethod
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        pass
    
    @abstractmethod
    def get_subreddit_posts(self, subreddit: str, sort: str = "hot", limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get posts from a subreddit."""
        pass
    
    @abstractmethod
    def get_subreddit_info(self, subreddit: str) -> Optional[Dict[str, Any]]:
        """Get subreddit information and metadata."""
        pass
    
    @abstractmethod
    def get_post_details(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific post."""
        pass
    
    @abstractmethod
    def get_comments(self, post_id: str, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get comments for a specific post."""
        pass
    
    @abstractmethod
    def search_posts(self, query: str, subreddit: Optional[str] = None, 
                    sort: str = "relevance", time_filter: str = "all", 
                    limit: int = 25) -> Optional[Dict[str, Any]]:
        """Search for posts across Reddit or within a specific subreddit."""
        pass
    
    @abstractmethod
    def get_user_posts(self, username: str, sort: str = "new", 
                      limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get posts submitted by a specific user."""
        pass
    
    @abstractmethod
    def get_user_comments(self, username: str, sort: str = "new", 
                         limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get comments made by a specific user."""
        pass
