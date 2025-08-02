# Reddit Official API Adapter
# This module implements a Reddit adapter for interacting with the official Reddit API using PRAW (Python Reddit API Wrapper).
# This adapter uses the official PRAW library to interact with Reddit's API.


import praw
from typing import Dict, Any, Optional, List
import logging
from .base import RedditAdapterProtocol
from .exceptions import AuthenticationError, APIError

logger = logging.getLogger(__name__)

class RedditOfficial(RedditAdapterProtocol):
    """Official Reddit API adapter using PRAW (Python Reddit API Wrapper)."""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.reddit: Optional[praw.Reddit] = None

    def authenticate(self) -> bool:
        """Initialize PRAW Reddit instance."""
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            
            # Test authentication by accessing read-only data
            _ = self.reddit.user.me()
            logger.info("Successfully authenticated with Reddit Official API")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e}")

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user information using PRAW."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        try:
            user = self.reddit.redditor(username)
            return {
                'name': user.name,
                'id': user.id,
                'created_utc': user.created_utc,
                'comment_karma': user.comment_karma,
                'link_karma': user.link_karma,
                'is_verified': getattr(user, 'verified', None),
                'has_verified_email': getattr(user, 'has_verified_email', None)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user info for {username}: {e}")
            raise APIError(f"Failed to get user info: {e}")

    def get_subreddit_posts(self, subreddit: str, sort: str = "hot", limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get posts from a subreddit using PRAW."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        try:
            sub = self.reddit.subreddit(subreddit)
            
            if sort == "hot":
                posts = sub.hot(limit=limit)
            elif sort == "new":
                posts = sub.new(limit=limit)
            elif sort == "top":
                posts = sub.top(limit=limit)
            else:
                posts = sub.hot(limit=limit)
            
            result = []
            for post in posts:
                result.append({
                    'id': post.id,
                    'title': post.title,
                    'author': str(post.author) if post.author else None,
                    'score': post.score,
                    'url': post.url,
                    'created_utc': post.created_utc,
                    'num_comments': post.num_comments,
                    'selftext': post.selftext if hasattr(post, 'selftext') else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get posts from r/{subreddit}: {e}")
            raise APIError(f"Failed to get posts: {e}")
