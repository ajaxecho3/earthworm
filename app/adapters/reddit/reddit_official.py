# Reddit Official API Adapter
# This module implements a Reddit adapter for interacting with the official Reddit API using PRAW (Python Reddit API Wrapper).
# This adapter uses the official PRAW library to interact with Reddit's API.

import os
import praw
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
import logging
from functools import wraps
from .base import RedditAdapterProtocol
from .exceptions import AuthenticationError, APIError, RateLimitError

logger = logging.getLogger(__name__)

def handle_rate_limit(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator to handle rate limiting with exponential backoff and jitter for anti-bot detection."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except praw.exceptions.RedditAPIException as e:
                    # Check if any of the errors are rate limit related
                    for error in e.items:
                        if error.error_type in ('RATELIMIT', 'TOO_MANY_REQUESTS'):
                            if attempt == max_retries:
                                logger.error(f"Reddit API rate limit exceeded after {max_retries} retries in {func.__name__}")
                                raise RateLimitError(f"Reddit API rate limit exceeded: {error.message}")
                            
                            base_wait = base_delay * (2 ** attempt)
                            jitter = random.uniform(0.5, 1.5)
                            delay = base_wait * jitter
                            logger.warning(f"Reddit API rate limit in {func.__name__}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            break
                    else:
                        # Not a rate limit error, re-raise
                        raise APIError(f"Reddit API error: {e}")
                except Exception as e:
                    # Catch other potential bot detection errors
                    error_str = str(e).lower()
                    if "429" in error_str or "too many requests" in error_str or "rate limit" in error_str:
                        if attempt == max_retries:
                            logger.error(f"Rate limit detected after {max_retries} retries in {func.__name__}")
                            raise RateLimitError(f"Rate limit detected: {e}")
                        
                        # Longer delay for potential bot detection
                        base_wait = base_delay * (3 ** attempt)  # More aggressive backoff
                        jitter = random.uniform(1.0, 2.0)  # Higher jitter
                        delay = base_wait * jitter
                        logger.warning(f"Potential bot detection in {func.__name__}, backing off for {delay:.1f}s")
                        time.sleep(delay)
                    else:
                        raise
                        
        return wrapper
    return decorator

class RedditOfficial(RedditAdapterProtocol):
    """Official Reddit API adapter using PRAW (Python Reddit API Wrapper)."""
    
    def __init__(self, client_id: str = "", client_secret: str = "", user_agent: str = ""):
        # Use environment variables if not provided
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID', '')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET', '')
        self.user_agent = user_agent or os.getenv('REDDIT_USER_AGENT', 'Earthworm Reddit Adapter 1.0')
        self.reddit: Optional[praw.Reddit] = None
        
        # Optional username/password for more authenticated access
        self.username = os.getenv('REDDIT_USERNAME', '')
        self.password = os.getenv('REDDIT_PASSWORD', '')


   
        
        # Rate limiting configuration with anti-bot detection measures
        self.max_retries = int(os.getenv('REDDIT_MAX_RETRIES', '3'))
        self.base_delay = float(os.getenv('REDDIT_BASE_DELAY', '2.0'))  # Increased default delay
        self.request_delay = float(os.getenv('REDDIT_REQUEST_DELAY', '0.5'))  # Increased minimum delay
        self._last_request_time = 0.0
        
        # Anti-bot detection features
        self.use_random_delays = bool(os.getenv('REDDIT_RANDOM_DELAYS', 'True').lower() == 'true')
        self.min_jitter = float(os.getenv('REDDIT_MIN_JITTER', '0.3'))
        self.max_jitter = float(os.getenv('REDDIT_MAX_JITTER', '1.2'))
        self.burst_protection = bool(os.getenv('REDDIT_BURST_PROTECTION', 'True').lower() == 'true')
        self.max_requests_per_minute = int(os.getenv('REDDIT_MAX_REQUESTS_PER_MINUTE', '30'))
        self._request_times = []  # Track request times for burst protection
        
        # Authentication preference - default to read-only for better reliability and anti-bot protection
        self.prefer_authenticated = bool(os.getenv('REDDIT_PREFER_AUTHENTICATED', 'false').lower() == 'true')

    def _enforce_rate_limit(self):
        """Enforce minimum delay between requests with human-like patterns to prevent bot detection."""
        current_time = time.time()
        
        # Clean old request times (older than 1 minute)
        if self.burst_protection:
            self._request_times = [t for t in self._request_times if current_time - t < 60]
            
            # Check if we're approaching burst limits
            if len(self._request_times) >= self.max_requests_per_minute:
                wait_time = 60 - (current_time - self._request_times[0]) + random.uniform(1, 5)
                logger.info(f"Burst protection: waiting {wait_time:.1f}s to avoid detection")
                time.sleep(wait_time)
                self._request_times = []  # Reset after waiting
        
        # Calculate delay since last request
        time_since_last = current_time - self._last_request_time
        base_delay = self.request_delay
        
        # Add random jitter to appear more human-like
        if self.use_random_delays:
            jitter = random.uniform(self.min_jitter, self.max_jitter)
            delay_with_jitter = base_delay * jitter
        else:
            delay_with_jitter = base_delay
        
        if time_since_last < delay_with_jitter:
            sleep_time = delay_with_jitter - time_since_last
            logger.debug(f"Enforcing human-like delay: sleeping for {sleep_time:.3f}s")
            time.sleep(sleep_time)
        
        current_time = time.time()
        self._last_request_time = current_time
        
        # Track this request for burst protection
        if self.burst_protection:
            self._request_times.append(current_time)

    def authenticate(self) -> bool:
        """Initialize PRAW Reddit instance with environment credentials and anti-bot measures."""

        
        try:
            if not self.client_id or not self.client_secret:
                raise AuthenticationError("Reddit API credentials not found. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
            
            # Make user agent more realistic if default is being used
            if self.user_agent == 'Earthworm Reddit Adapter 1.0':
                # Use more human-like user agents
                user_agents = [
                    'Mozilla/5.0 (compatible; DataCollector/1.0; +http://example.com/bot)',
                    'Research Bot 1.0 (compatible; PRAW)',
                    'Academic Research Tool v1.0',
                    'Social Media Analytics Bot 1.0'
                ]
                self.user_agent = random.choice(user_agents)
                logger.debug(f"Using randomized user agent for better compatibility")
            
            # Add small random delay before authentication to appear more human
            if self.use_random_delays:
                auth_delay = random.uniform(0.5, 2.0)
                logger.debug(f"Pre-auth delay: {auth_delay:.1f}s")
                time.sleep(auth_delay)
            
            # Default to read-only mode for better reliability and anti-bot protection
            # Only try authenticated access if explicitly preferred and credentials provided
            auth_failed = False
            if self.prefer_authenticated and self.username and self.password:
                logger.info("Attempting authenticated Reddit API access (explicit preference)...")
                try:
                    self.reddit = praw.Reddit(
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        user_agent=self.user_agent,
                        username=self.username,
                        password=self.password,
                        check_for_async=False  # Disable async checking for better compatibility
                    )
                    # Test authentication immediately
                    self.reddit.user.me()
                    logger.info("✅ Successfully authenticated with username/password")
                except Exception as auth_error:
                    logger.warning(f"⚠️ Authentication failed ({auth_error}), falling back to read-only mode")
                    auth_failed = True
            
            # Use read-only mode by default or if authentication failed
            if not self.prefer_authenticated or not self.username or not self.password or auth_failed:
                if not self.prefer_authenticated:
                    logger.info("Using read-only Reddit API access (default for better reliability)...")
                else:
                    logger.info("Using read-only Reddit API access...")
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent,
                    check_for_async=False
                )
            
            # Test the connection by accessing a simple endpoint with delay
            try:
                # Add delay before test to avoid rapid requests
                time.sleep(random.uniform(1.0, 2.0))
                test_sub = self.reddit.subreddit("test")
                _ = test_sub.display_name  # Simple property access to test
                logger.info("✅ Successfully connected to Reddit Official API")
                return True
            except Exception as test_error:
                logger.warning(f"Authentication test failed: {test_error}")
                # Still return True if the reddit instance was created
                return self.reddit is not None
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e}")

    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user information using PRAW."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        self._enforce_rate_limit()
        
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

    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def get_subreddit_posts(self, subreddit: str, sort: str = "hot", limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get posts from a subreddit using PRAW with enhanced error handling."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        self._enforce_rate_limit()
        
        try:
            sub = self.reddit.subreddit(subreddit)
            
            # Get posts based on sort parameter
            if sort == "hot":
                posts = sub.hot(limit=limit)
            elif sort == "new":
                posts = sub.new(limit=limit)
            elif sort == "top":
                posts = sub.top(limit=limit, time_filter="all")
            elif sort == "rising":
                posts = sub.rising(limit=limit)
            else:
                posts = sub.hot(limit=limit)
            
            result = []
            for post in posts:
                try:
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'author': str(post.author) if post.author else '[deleted]',
                        'score': post.score,
                        'upvote_ratio': getattr(post, 'upvote_ratio', 0),
                        'url': post.url,
                        'created_utc': post.created_utc,
                        'num_comments': post.num_comments,
                        'selftext': getattr(post, 'selftext', ''),
                        'subreddit': post.subreddit.display_name,
                        'permalink': f"https://reddit.com{post.permalink}",
                        'is_self': post.is_self,
                        'over_18': post.over_18,
                        'spoiler': getattr(post, 'spoiler', False),
                        'locked': getattr(post, 'locked', False),
                        'archived': getattr(post, 'archived', False),
                        'distinguished': getattr(post, 'distinguished', None),
                        'stickied': getattr(post, 'stickied', False),
                    }
                    result.append(post_data)
                except Exception as post_error:
                    logger.warning(f"Error processing post {getattr(post, 'id', 'unknown')}: {post_error}")
                    continue
            
            # Return in Reddit JSON API format for compatibility
            return {
                'data': {
                    'children': [{'data': post} for post in result],
                    'after': None,
                    'before': None,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get posts from r/{subreddit}: {e}")
            raise APIError(f"Failed to get posts: {e}")

    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def get_comments(self, post_id: str, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get comments for a specific post using PRAW."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        self._enforce_rate_limit()
        
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove "more comments" objects
            
            comments = []
            for comment in submission.comments.list()[:limit]:
                try:
                    if hasattr(comment, 'body') and comment.body not in ['[deleted]', '[removed]']:
                        comment_data = {
                            'id': comment.id,
                            'author': str(comment.author) if comment.author else '[deleted]',
                            'body': comment.body,
                            'score': comment.score,
                            'created_utc': comment.created_utc,
                            'parent_id': comment.parent_id,
                            'link_id': comment.link_id,
                            'subreddit': comment.subreddit.display_name,
                            'permalink': f"https://reddit.com{comment.permalink}",
                            'distinguished': getattr(comment, 'distinguished', None),
                            'stickied': getattr(comment, 'stickied', False),
                            'is_submitter': getattr(comment, 'is_submitter', False),
                            'controversiality': getattr(comment, 'controversiality', 0),
                            'depth': getattr(comment, 'depth', 0),
                        }
                        comments.append(comment_data)
                except Exception as comment_error:
                    logger.warning(f"Error processing comment: {comment_error}")
                    continue
            
            logger.info(f"Successfully extracted {len(comments)} comments from post {post_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Failed to get comments for post {post_id}: {e}")
            raise APIError(f"Failed to get comments: {e}")

    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def search_posts(self, query: str, subreddit: Optional[str] = None, 
                    sort: str = "relevance", time_filter: str = "all", 
                    limit: int = 25) -> Optional[Dict[str, Any]]:
        """Search for posts using PRAW."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        self._enforce_rate_limit()
        
        try:
            if subreddit:
                sub = self.reddit.subreddit(subreddit)
                search_results = sub.search(query, sort=sort, time_filter=time_filter, limit=limit)
            else:
                search_results = self.reddit.subreddit("all").search(query, sort=sort, time_filter=time_filter, limit=limit)
            
            result = []
            for post in search_results:
                try:
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'author': str(post.author) if post.author else '[deleted]',
                        'score': post.score,
                        'url': post.url,
                        'created_utc': post.created_utc,
                        'num_comments': post.num_comments,
                        'selftext': getattr(post, 'selftext', ''),
                        'subreddit': post.subreddit.display_name,
                        'permalink': f"https://reddit.com{post.permalink}",
                    }
                    result.append(post_data)
                except Exception as post_error:
                    logger.warning(f"Error processing search result: {post_error}")
                    continue
            
            return {
                'data': {
                    'children': [{'data': post} for post in result],
                    'after': None,
                    'before': None,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to search for '{query}': {e}")
            raise APIError(f"Failed to search: {e}")

    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def get_user_posts(self, username: str, sort: str = "new", 
                      limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get posts submitted by a specific user using PRAW."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        self._enforce_rate_limit()
        
        try:
            user = self.reddit.redditor(username)
            
            if sort == "new":
                posts = user.submissions.new(limit=limit)
            elif sort == "top":
                posts = user.submissions.top(limit=limit)
            elif sort == "hot":
                posts = user.submissions.hot(limit=limit)
            else:
                posts = user.submissions.new(limit=limit)
            
            result = []
            for post in posts:
                try:
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'author': str(post.author) if post.author else '[deleted]',
                        'score': post.score,
                        'url': post.url,
                        'created_utc': post.created_utc,
                        'num_comments': post.num_comments,
                        'selftext': getattr(post, 'selftext', ''),
                        'subreddit': post.subreddit.display_name,
                    }
                    result.append(post_data)
                except Exception as post_error:
                    logger.warning(f"Error processing user post: {post_error}")
                    continue
            
            return {
                'data': {
                    'children': [{'data': post} for post in result],
                    'after': None,
                    'before': None,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get posts for user {username}: {e}")
            raise APIError(f"Failed to get user posts: {e}")

    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def get_user_comments(self, username: str, sort: str = "new", 
                         limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get comments made by a specific user using PRAW."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        self._enforce_rate_limit()
        
        try:
            user = self.reddit.redditor(username)
            
            if sort == "new":
                comments = user.comments.new(limit=limit)
            elif sort == "top":
                comments = user.comments.top(limit=limit)
            else:
                comments = user.comments.new(limit=limit)
            
            result = []
            for comment in comments:
                try:
                    if hasattr(comment, 'body') and comment.body not in ['[deleted]', '[removed]']:
                        comment_data = {
                            'id': comment.id,
                            'author': str(comment.author) if comment.author else '[deleted]',
                            'body': comment.body,
                            'score': comment.score,
                            'created_utc': comment.created_utc,
                            'subreddit': comment.subreddit.display_name,
                            'link_id': comment.link_id,
                        }
                        result.append(comment_data)
                except Exception as comment_error:
                    logger.warning(f"Error processing user comment: {comment_error}")
                    continue
            
            return {
                'data': {
                    'children': [{'data': comment} for comment in result],
                    'after': None,
                    'before': None,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get comments for user {username}: {e}")
            raise APIError(f"Failed to get user comments: {e}")

    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def get_subreddit_info(self, subreddit: str) -> Optional[Dict[str, Any]]:
        """Get subreddit information and metadata using PRAW."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        self._enforce_rate_limit()
        
        try:
            sub = self.reddit.subreddit(subreddit)
            
            # Get subreddit info
            return {
                'display_name': sub.display_name,
                'title': getattr(sub, 'title', ''),
                'description': getattr(sub, 'description', ''),
                'subscribers': getattr(sub, 'subscribers', 0),
                'active_user_count': getattr(sub, 'active_user_count', 0),
                'created_utc': getattr(sub, 'created_utc', 0),
                'over18': getattr(sub, 'over18', False),
                'public_description': getattr(sub, 'public_description', ''),
                'url': f"https://reddit.com/r/{sub.display_name}",
                'icon_img': getattr(sub, 'icon_img', ''),
                'header_img': getattr(sub, 'header_img', ''),
                'lang': getattr(sub, 'lang', 'en'),
                'subreddit_type': getattr(sub, 'subreddit_type', 'public'),
            }
            
        except Exception as e:
            logger.error(f"Failed to get subreddit info for r/{subreddit}: {e}")
            raise APIError(f"Failed to get subreddit info: {e}")

    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def get_post_details(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific post using PRAW."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
            
        self._enforce_rate_limit()
        
        try:
            submission = self.reddit.submission(id=post_id)
            
            # Get detailed post information
            post_data = {
                'id': submission.id,
                'title': submission.title,
                'author': str(submission.author) if submission.author else '[deleted]',
                'score': submission.score,
                'upvote_ratio': getattr(submission, 'upvote_ratio', 0),
                'url': submission.url,
                'created_utc': submission.created_utc,
                'num_comments': submission.num_comments,
                'selftext': getattr(submission, 'selftext', ''),
                'subreddit': submission.subreddit.display_name,
                'permalink': f"https://reddit.com{submission.permalink}",
                'is_self': submission.is_self,
                'over_18': submission.over_18,
                'spoiler': getattr(submission, 'spoiler', False),
                'locked': getattr(submission, 'locked', False),
                'archived': getattr(submission, 'archived', False),
                'distinguished': getattr(submission, 'distinguished', None),
                'stickied': getattr(submission, 'stickied', False),
                'gilded': getattr(submission, 'gilded', 0),
                'total_awards_received': getattr(submission, 'total_awards_received', 0),
                'edited': getattr(submission, 'edited', False),
                'domain': getattr(submission, 'domain', ''),
                'thumbnail': getattr(submission, 'thumbnail', ''),
                'preview': getattr(submission, 'preview', {}),
            }
            
            # Return in Reddit JSON API format for compatibility
            return {
                'data': {
                    'children': [{'data': post_data}],
                    'after': None,
                    'before': None,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get post details for {post_id}: {e}")
            raise APIError(f"Failed to get post details: {e}")

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status information."""
        if not self.reddit:
            return {'error': 'Not authenticated'}
        
        try:
            # Get rate limit info from PRAW if available
            rate_limit_info = {
                'remaining_requests': getattr(self.reddit._core, 'remaining', None),
                'reset_timestamp': getattr(self.reddit._core, 'reset_timestamp', None),
                'used_requests': getattr(self.reddit._core, 'used', None),
                'last_request_time': self._last_request_time,
                'request_delay': self.request_delay,
                'max_retries': self.max_retries,
                'base_delay': self.base_delay
            }
            return rate_limit_info
        except Exception as e:
            logger.warning(f"Could not get rate limit status: {e}")
            return {
                'last_request_time': self._last_request_time,
                'request_delay': self.request_delay,
                'max_retries': self.max_retries,
                'base_delay': self.base_delay
            }

    def set_rate_limit_config(self, max_retries: int = None, base_delay: float = None, 
                             request_delay: float = None) -> None:
        """Update rate limiting configuration."""
        if max_retries is not None:
            self.max_retries = max_retries
            logger.info(f"Updated max_retries to {max_retries}")
        
        if base_delay is not None:
            self.base_delay = base_delay
            logger.info(f"Updated base_delay to {base_delay}s")
            
        if request_delay is not None:
            self.request_delay = request_delay
            logger.info(f"Updated request_delay to {request_delay}s")

    def wait_for_rate_limit_reset(self) -> bool:
        """Wait for rate limit to reset if we know when it resets."""
        if not self.reddit:
            return False
            
        try:
            reset_timestamp = getattr(self.reddit._core, 'reset_timestamp', None)
            if reset_timestamp:
                current_time = time.time()
                wait_time = reset_timestamp - current_time
                
                if wait_time > 0:
                    # Add random jitter to reset wait time
                    jitter = random.uniform(0.8, 1.3)
                    actual_wait = (wait_time + 1) * jitter
                    logger.info(f"Waiting {actual_wait:.1f}s for rate limit reset...")
                    time.sleep(actual_wait)
                    return True
            return False
        except Exception as e:
            logger.warning(f"Could not wait for rate limit reset: {e}")
            return False

    def enable_stealth_mode(self):
        """Enable enhanced anti-bot detection measures."""
        self.use_random_delays = True
        self.burst_protection = True
        self.request_delay = max(self.request_delay, 1.0)  # Minimum 1 second between requests
        self.max_requests_per_minute = min(self.max_requests_per_minute, 20)  # Max 20 requests per minute
        self.min_jitter = 0.5
        self.max_jitter = 2.0
        logger.info("🥷 Stealth mode enabled - using enhanced anti-bot measures")

    def disable_stealth_mode(self):
        """Disable anti-bot detection measures for faster operation."""
        self.use_random_delays = False
        self.burst_protection = False
        self.request_delay = 0.1
        self.max_requests_per_minute = 60
        self.min_jitter = 0.3
        self.max_jitter = 1.2
        logger.info("🚀 Stealth mode disabled - using faster operation mode")

    def get_anti_bot_status(self) -> Dict[str, Any]:
        """Get current anti-bot detection configuration."""
        return {
            'stealth_mode': self.use_random_delays and self.burst_protection,
            'random_delays_enabled': self.use_random_delays,
            'burst_protection_enabled': self.burst_protection,
            'request_delay': self.request_delay,
            'max_requests_per_minute': self.max_requests_per_minute,
            'jitter_range': f"{self.min_jitter}-{self.max_jitter}",
            'recent_requests': len(self._request_times),
            'user_agent': self.user_agent
        }

    def simulate_human_behavior(self):
        """Add a realistic pause to simulate human browsing behavior."""
        if self.use_random_delays:
            # Simulate reading time between 2-8 seconds
            reading_time = random.uniform(2.0, 8.0)
            logger.debug(f"Simulating human reading time: {reading_time:.1f}s")
            time.sleep(reading_time)
    
    # ===============================
    # ADVANCED RESEARCH METHODS
    # ===============================
    
    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def search_posts_by_timeframe(self, query: str, subreddit: Optional[str] = None,
                                 start_date: Optional[datetime] = None, 
                                 end_date: Optional[datetime] = None,
                                 limit: int = 100) -> Optional[Dict[str, Any]]:
        """Search for posts within a specific timeframe for temporal analysis."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
        
        self._enforce_rate_limit()
        
        try:
            # Default to last 30 days if no dates provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Convert to Unix timestamps
            start_timestamp = start_date.timestamp()
            end_timestamp = end_date.timestamp()
            
            # Search for posts
            if subreddit:
                sub = self.reddit.subreddit(subreddit)
                search_results = sub.search(query, sort="new", limit=limit)
            else:
                search_results = self.reddit.subreddit("all").search(query, sort="new", limit=limit)
            
            result = []
            for post in search_results:
                try:
                    # Filter by timestamp
                    if start_timestamp <= post.created_utc <= end_timestamp:
                        post_data = {
                            'id': post.id,
                            'title': post.title,
                            'author': str(post.author) if post.author else '[deleted]',
                            'score': post.score,
                            'upvote_ratio': getattr(post, 'upvote_ratio', 0),
                            'url': post.url,
                            'created_utc': post.created_utc,
                            'created_date': datetime.fromtimestamp(post.created_utc).isoformat(),
                            'num_comments': post.num_comments,
                            'selftext': getattr(post, 'selftext', ''),
                            'subreddit': post.subreddit.display_name,
                            'permalink': f"https://reddit.com{post.permalink}",
                            'is_self': post.is_self,
                            'over_18': post.over_18,
                            'domain': getattr(post, 'domain', ''),
                        }
                        result.append(post_data)
                except Exception as post_error:
                    logger.warning(f"Error processing temporal search result: {post_error}")
                    continue
            
            logger.info(f"Found {len(result)} posts between {start_date.date()} and {end_date.date()}")
            
            return {
                'data': {
                    'children': [{'data': post} for post in result],
                    'timeframe': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat(),
                        'total_days': (end_date - start_date).days
                    },
                    'query': query,
                    'subreddit': subreddit
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to search posts by timeframe: {e}")
            raise APIError(f"Failed to search by timeframe: {e}")
    
    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def collect_from_multiple_subreddits(self, subreddits: List[str], 
                                        sort: str = "hot", limit_per_sub: int = 25) -> Dict[str, Any]:
        """Collect posts from multiple subreddits for comparative analysis."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return {}
        
        all_results = {}
        total_posts = 0
        
        logger.info(f"Collecting from {len(subreddits)} subreddits: {subreddits}")
        
        for i, subreddit in enumerate(subreddits):
            try:
                logger.info(f"Collecting from r/{subreddit} ({i+1}/{len(subreddits)})")
                
                # Get posts from this subreddit
                posts_data = self.get_subreddit_posts(subreddit, sort=sort, limit=limit_per_sub)
                
                if posts_data and posts_data.get('data', {}).get('children'):
                    posts = posts_data['data']['children']
                    all_results[subreddit] = {
                        'posts': posts,
                        'count': len(posts),
                        'collected_at': datetime.now().isoformat()
                    }
                    total_posts += len(posts)
                    logger.info(f"  ✅ Collected {len(posts)} posts from r/{subreddit}")
                else:
                    all_results[subreddit] = {'posts': [], 'count': 0, 'error': 'No posts found'}
                    logger.warning(f"  ⚠️ No posts found in r/{subreddit}")
                
                # Human-like delay between subreddits
                if i < len(subreddits) - 1:  # Don't wait after last subreddit
                    self.simulate_human_behavior()
                    
            except Exception as e:
                logger.error(f"Error collecting from r/{subreddit}: {e}")
                all_results[subreddit] = {'posts': [], 'count': 0, 'error': str(e)}
                continue
        
        logger.info(f"Multi-subreddit collection complete: {total_posts} total posts from {len(subreddits)} subreddits")
        
        return {
            'results': all_results,
            'summary': {
                'total_subreddits': len(subreddits),
                'successful_collections': len([r for r in all_results.values() if r['count'] > 0]),
                'total_posts': total_posts,
                'collection_date': datetime.now().isoformat()
            }
        }
    
    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def get_comment_thread(self, comment_id: str, max_depth: int = 5) -> Optional[Dict[str, Any]]:
        """Get a complete comment thread for conversation analysis."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
        
        self._enforce_rate_limit()
        
        try:
            comment = self.reddit.comment(id=comment_id)
            comment.refresh()  # Load all replies
            
            def extract_comment_tree(comment_obj, current_depth=0):
                """Recursively extract comment tree."""
                if current_depth > max_depth:
                    return None
                
                try:
                    if not hasattr(comment_obj, 'body') or comment_obj.body in ['[deleted]', '[removed]']:
                        return None
                    
                    comment_data = {
                        'id': comment_obj.id,
                        'author': str(comment_obj.author) if comment_obj.author else '[deleted]',
                        'body': comment_obj.body,
                        'score': comment_obj.score,
                        'created_utc': comment_obj.created_utc,
                        'created_date': datetime.fromtimestamp(comment_obj.created_utc).isoformat(),
                        'depth': current_depth,
                        'parent_id': comment_obj.parent_id,
                        'permalink': f"https://reddit.com{comment_obj.permalink}",
                        'is_submitter': getattr(comment_obj, 'is_submitter', False),
                        'distinguished': getattr(comment_obj, 'distinguished', None),
                        'gilded': getattr(comment_obj, 'gilded', 0),
                        'controversiality': getattr(comment_obj, 'controversiality', 0),
                        'replies': []
                    }
                    
                    # Get replies recursively
                    if hasattr(comment_obj, 'replies') and comment_obj.replies:
                        for reply in comment_obj.replies:
                            if hasattr(reply, 'body'):  # Skip MoreComments objects
                                reply_data = extract_comment_tree(reply, current_depth + 1)
                                if reply_data:
                                    comment_data['replies'].append(reply_data)
                    
                    return comment_data
                    
                except Exception as e:
                    logger.warning(f"Error processing comment in thread: {e}")
                    return None
            
            thread_data = extract_comment_tree(comment)
            
            if thread_data:
                logger.info(f"Successfully extracted comment thread starting from {comment_id}")
                return {
                    'thread_root': thread_data,
                    'max_depth': max_depth,
                    'extracted_at': datetime.now().isoformat()
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get comment thread for {comment_id}: {e}")
            raise APIError(f"Failed to get comment thread: {e}")
    
    @handle_rate_limit(max_retries=3, base_delay=1.0)
    def get_trending_topics(self, subreddit: str = "all", time_filter: str = "day") -> Optional[Dict[str, Any]]:
        """Get trending topics and popular keywords for trend analysis."""
        if not self.reddit:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
        
        self._enforce_rate_limit()
        
        try:
            sub = self.reddit.subreddit(subreddit)
            
            # Get top posts from the specified time period
            if time_filter == "hour":
                posts = sub.top(time_filter="hour", limit=50)
            elif time_filter == "day":
                posts = sub.top(time_filter="day", limit=50)
            elif time_filter == "week":
                posts = sub.top(time_filter="week", limit=100)
            else:
                posts = sub.hot(limit=50)
            
            trending_data = {
                'posts': [],
                'keywords': {},
                'subreddits': {},
                'authors': {},
                'domains': {}
            }
            
            for post in posts:
                try:
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'created_utc': post.created_utc,
                        'subreddit': post.subreddit.display_name,
                        'author': str(post.author) if post.author else '[deleted]',
                        'url': post.url,
                        'domain': getattr(post, 'domain', ''),
                        'upvote_ratio': getattr(post, 'upvote_ratio', 0)
                    }
                    trending_data['posts'].append(post_data)
                    
                    # Count trending elements
                    subreddit_name = post.subreddit.display_name
                    trending_data['subreddits'][subreddit_name] = trending_data['subreddits'].get(subreddit_name, 0) + 1
                    
                    author_name = str(post.author) if post.author else '[deleted]'
                    if author_name != '[deleted]':
                        trending_data['authors'][author_name] = trending_data['authors'].get(author_name, 0) + 1
                    
                    domain = getattr(post, 'domain', '')
                    if domain:
                        trending_data['domains'][domain] = trending_data['domains'].get(domain, 0) + 1
                    
                    # Simple keyword extraction from titles
                    title_words = post.title.lower().split()
                    for word in title_words:
                        # Filter out common words and short words
                        if len(word) > 3 and word not in ['this', 'that', 'with', 'from', 'they', 'have', 'been', 'were', 'said', 'what', 'when', 'where', 'will', 'there', 'their']:
                            trending_data['keywords'][word] = trending_data['keywords'].get(word, 0) + 1
                    
                except Exception as post_error:
                    logger.warning(f"Error processing trending post: {post_error}")
                    continue
            
            # Sort trending data by frequency
            trending_data['top_keywords'] = dict(sorted(trending_data['keywords'].items(), key=lambda x: x[1], reverse=True)[:20])
            trending_data['top_subreddits'] = dict(sorted(trending_data['subreddits'].items(), key=lambda x: x[1], reverse=True)[:10])
            trending_data['top_authors'] = dict(sorted(trending_data['authors'].items(), key=lambda x: x[1], reverse=True)[:10])
            trending_data['top_domains'] = dict(sorted(trending_data['domains'].items(), key=lambda x: x[1], reverse=True)[:10])
            
            logger.info(f"Analyzed {len(trending_data['posts'])} trending posts from r/{subreddit}")
            
            return {
                'data': trending_data,
                'analysis_period': time_filter,
                'subreddit': subreddit,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get trending topics: {e}")
            raise APIError(f"Failed to get trending topics: {e}")
    
    def get_research_metadata(self) -> Dict[str, Any]:
        """Get comprehensive metadata about the current session for research documentation."""
        return {
            'session_info': {
                'reddit_adapter': 'Official PRAW',
                'authentication_mode': 'authenticated' if (self.prefer_authenticated and self.username) else 'read-only',
                'anti_bot_protection': self.get_anti_bot_status(),
                'rate_limiting': self.get_rate_limit_status(),
                'session_start': datetime.now().isoformat(),
                'user_agent': self.user_agent
            },
            'capabilities': {
                'subreddit_collection': True,
                'search_functionality': True,
                'comment_extraction': True,
                'user_analysis': True,
                'temporal_filtering': True,
                'multi_subreddit_collection': True,
                'comment_thread_analysis': True,
                'trending_analysis': True,
                'export_formats': ['json', 'csv', 'excel'],
                'statistical_analysis': True
            },
            'limitations': {
                'rate_limits': 'Reddit API standard limits apply',
                'historical_data': 'Limited to Reddit API availability',
                'deleted_content': 'Cannot retrieve deleted/removed content',
                'private_subreddits': 'Requires appropriate permissions',
                'real_time': 'Not real-time, subject to API delays'
            }
        }
