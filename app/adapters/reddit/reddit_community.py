## Reddit Community Web Scraper
# This module implements a Reddit adapter for scraping Reddit data without using the official API.
# It scrapes public Reddit pages and JSON endpoints that don't require authentication.
# This file is part of the Earthworm application, which provides various adapters for different services.

import requests
from typing import Dict, Any, Optional, List, Callable
import logging
import time
import json
import random
from urllib.parse import urlencode, quote
from .base import RedditAdapterProtocol
from .exceptions import AuthenticationError, APIError, RateLimitError
from ...utils.agents import get_agent

logger = logging.getLogger(__name__)

class RedditCommunity(RedditAdapterProtocol):
    """Reddit Community web scraper for non-API Reddit data collection."""
    
    BASE_URL = "https://www.reddit.com"
    
    def __init__(self, client_id: str = "", client_secret: str = "", user_agent: str = ""):
        # These params are not needed for web scraping but kept for interface compatibility
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent or get_agent()
        self.session = requests.Session()
        self._setup_session()
        self.request_delay = 1.0  # Delay between requests to be respectful
        self.max_retries = 3  # Maximum number of retries for failed requests
        self.backoff_factor = 2.0  # Exponential backoff factor
        self.request_count = 0  # Track number of requests made
        self.start_time = time.time()  # Track session start time

    def _setup_session(self) -> None:
        """Setup the session with headers to mimic a real browser."""
        headers = {
            'User-Agent': get_agent(),  # Rotate user agent for each session
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(headers)
        
        # Add some cookies to appear more like a real browser
        self.session.cookies.update({
            'reddit_session': f'session_{int(time.time())}',
        })

    def _rotate_user_agent(self) -> None:
        """Rotate user agent to avoid detection."""
        self.session.headers.update({'User-Agent': get_agent()})

    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make a request with error handling, retry logic, and rate limiting."""
        for attempt in range(self.max_retries + 1):
            try:
                # Rotate user agent for each request
                self._rotate_user_agent()
                
                # Add delay to be respectful
                time.sleep(self.request_delay)
                
                # Track request count
                self.request_count += 1
                
                response = self.session.get(url, params=params, timeout=10)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue  # Retry the request
                
                # Handle other HTTP errors
                if response.status_code == 404:
                    logger.warning(f"Resource not found: {url}")
                    return None
                elif response.status_code == 403:
                    logger.warning(f"Access forbidden: {url} - Reddit may be blocking requests")
                    # Try with different approach for 403 errors
                    if attempt == 0:  # Only try once
                        alternate_response = self._try_alternate_request(url, params)
                        if alternate_response:
                            return alternate_response
                    return None
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code} for {url}")
                    if attempt < self.max_retries:
                        wait_time = self.backoff_factor ** attempt + random.uniform(0, 1)
                        logger.info(f"Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(wait_time)
                        continue
                
                response.raise_for_status()
                
                # Try to parse as JSON first (for .json endpoints)
                try:
                    data = response.json()
                    # Validate basic Reddit data structure
                    if self._validate_reddit_response(data):
                        return data
                    else:
                        logger.warning(f"Invalid Reddit response structure from {url}")
                        return None
                except json.JSONDecodeError:
                    # Return the text content for HTML parsing if needed
                    return {'html_content': response.text, 'status_code': response.status_code}
                    
            except requests.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt + random.uniform(0, 1)
                    logger.info(f"Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed for {url}")
                    raise APIError(f"Request failed after {self.max_retries + 1} attempts: {e}")
        
        return None

    def _try_alternate_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Try alternate request method when getting 403 errors."""
        try:
            # Try with a different user agent and additional headers
            alt_headers = {
                'User-Agent': get_agent(),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.reddit.com/',
                'Origin': 'https://www.reddit.com',
                'X-Requested-With': 'XMLHttpRequest',
            }
            
            # Update session headers temporarily
            original_headers = self.session.headers.copy()
            self.session.headers.update(alt_headers)
            
            # Add a longer delay for alternate requests
            time.sleep(self.request_delay * 2)
            
            response = self.session.get(url, params=params, timeout=15)
            
            # Restore original headers
            self.session.headers.clear()
            self.session.headers.update(original_headers)
            
            if response.status_code == 200:
                logger.info(f"Alternate request successful for {url}")
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {'html_content': response.text, 'status_code': response.status_code}
            else:
                logger.debug(f"Alternate request also failed with status {response.status_code}")
                return None
                
        except Exception as e:
            logger.debug(f"Alternate request failed: {e}")
            return None

    def _validate_reddit_response(self, data: Any) -> bool:
        """Validate that the response has the expected Reddit structure."""
        if not data:
            return False
        
        # Check for Reddit listing structure
        if isinstance(data, dict):
            if 'data' in data:
                return True
            if 'html_content' in data:  # HTML response
                return True
        
        # Check for Reddit post/comment array structure
        if isinstance(data, list):
            return len(data) > 0
        
        return False

    def _clean_text_content(self, text: str) -> str:
        """Clean and normalize text content for research use."""
        if not text or text in ['[deleted]', '[removed]', None]:
            return ""
        
        # Basic text cleaning
        text = text.strip()
        # Remove Reddit markdown formatting that might interfere with analysis
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        return text

    def _extract_clean_post_data(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and clean post data for research use."""
        return {
            'id': post_data.get('id', ''),
            'title': self._clean_text_content(post_data.get('title', '')),
            'author': post_data.get('author', ''),
            'subreddit': post_data.get('subreddit', ''),
            'score': post_data.get('score', 0),
            'upvote_ratio': post_data.get('upvote_ratio', 0),
            'num_comments': post_data.get('num_comments', 0),
            'created_utc': post_data.get('created_utc', 0),
            'selftext': self._clean_text_content(post_data.get('selftext', '')),
            'url': post_data.get('url', ''),
            'permalink': post_data.get('permalink', ''),
            'is_self': post_data.get('is_self', False),
            'over_18': post_data.get('over_18', False),
            'spoiler': post_data.get('spoiler', False),
            'locked': post_data.get('locked', False),
            'archived': post_data.get('archived', False),
            'distinguished': post_data.get('distinguished', None),
            'stickied': post_data.get('stickied', False),
        }

    def _extract_clean_comment_data(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and clean comment data for research use."""
        return {
            'id': comment_data.get('id', ''),
            'author': comment_data.get('author', ''),
            'body': self._clean_text_content(comment_data.get('body', '')),
            'score': comment_data.get('score', 0),
            'created_utc': comment_data.get('created_utc', 0),
            'parent_id': comment_data.get('parent_id', ''),
            'link_id': comment_data.get('link_id', ''),
            'subreddit': comment_data.get('subreddit', ''),
            'permalink': comment_data.get('permalink', ''),
            'distinguished': comment_data.get('distinguished', None),
            'stickied': comment_data.get('stickied', False),
            'is_submitter': comment_data.get('is_submitter', False),
            'controversiality': comment_data.get('controversiality', 0),
            'depth': comment_data.get('depth', 0),
        }

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about the current scraping session."""
        current_time = time.time()
        session_duration = current_time - self.start_time
        
        return {
            'session_duration_seconds': session_duration,
            'total_requests': self.request_count,
            'requests_per_minute': (self.request_count / session_duration * 60) if session_duration > 0 else 0,
            'average_delay': self.request_delay,
            'max_retries': self.max_retries,
            'start_time': self.start_time,
        }

    def authenticate(self) -> bool:
        """No authentication needed for web scraping public Reddit content."""
        logger.info("No authentication required for web scraping mode")
        return True

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user information from Reddit public page."""
        try:
            url = f"{self.BASE_URL}/user/{username}/about.json"
            data = self._make_request(url)
            
            if data and 'data' in data:
                return data['data']
            return None
            
        except APIError as e:
            logger.error(f"Failed to get user info for {username}: {e}")
            return None

    def get_subreddit_posts(self, subreddit: str, sort: str = "hot", limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get posts from a subreddit using public JSON endpoint."""
        try:
            url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
            params = {'limit': min(limit, 100)}  # Reddit limits to 100 per request
            
            data = self._make_request(url, params)
            return data
            
        except APIError as e:
            logger.error(f"Failed to get posts from r/{subreddit}: {e}")
            return None

    def get_subreddit_info(self, subreddit: str) -> Optional[Dict[str, Any]]:
        """Get subreddit information and metadata."""
        try:
            url = f"{self.BASE_URL}/r/{subreddit}/about.json"
            data = self._make_request(url)
            
            if data and 'data' in data:
                return data['data']
            return None
            
        except APIError as e:
            logger.error(f"Failed to get subreddit info for r/{subreddit}: {e}")
            return None

    def get_post_details(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific post."""
        try:
            # Reddit post URLs follow the pattern: /comments/post_id/
            url = f"{self.BASE_URL}/comments/{post_id}.json"
            data = self._make_request(url)
            
            if data and isinstance(data, list) and len(data) > 0:
                # First element contains the post data
                return data[0]
            return None
            
        except APIError as e:
            logger.error(f"Failed to get post details for {post_id}: {e}")
            return None

    def get_comments(self, post_id: str, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get comments for a specific post with improved data cleaning."""
        try:
            url = f"{self.BASE_URL}/comments/{post_id}.json"
            params = {'limit': limit}
            data = self._make_request(url, params)
            
            if data and isinstance(data, list) and len(data) > 1:
                # Second element contains the comments data
                comments_data = data[1]
                if 'data' in comments_data and 'children' in comments_data['data']:
                    # Extract and clean comment data
                    cleaned_comments = []
                    for child in comments_data['data']['children']:
                        if 'data' in child:
                            comment_data = child['data']
                            # Skip deleted/removed comments unless specifically requested
                            if comment_data.get('body') not in ['[deleted]', '[removed]', None, '']:
                                cleaned_comments.append(self._extract_clean_comment_data(comment_data))
                    
                    logger.info(f"Successfully extracted {len(cleaned_comments)} valid comments from post {post_id}")
                    return cleaned_comments
            
            logger.warning(f"No comments found for post {post_id}")
            return []
            
        except APIError as e:
            logger.error(f"Failed to get comments for post {post_id}: {e}")
            return None

    def search_posts(self, query: str, subreddit: Optional[str] = None, 
                    sort: str = "relevance", time_filter: str = "all", 
                    limit: int = 25) -> Optional[Dict[str, Any]]:
        """Search for posts across Reddit or within a specific subreddit."""
        try:
            if subreddit:
                url = f"{self.BASE_URL}/r/{subreddit}/search.json"
                params = {
                    'q': query,
                    'restrict_sr': 'on',  # Restrict search to subreddit
                    'sort': sort,
                    't': time_filter,
                    'limit': limit
                }
            else:
                url = f"{self.BASE_URL}/search.json"
                params = {
                    'q': query,
                    'sort': sort,
                    't': time_filter,
                    'limit': limit
                }
            
            data = self._make_request(url, params)
            return data
            
        except APIError as e:
            logger.error(f"Failed to search for '{query}': {e}")
            return None

    def get_user_posts(self, username: str, sort: str = "new", 
                      limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get posts submitted by a specific user."""
        try:
            url = f"{self.BASE_URL}/user/{username}/submitted.json"
            params = {
                'sort': sort,
                'limit': limit
            }
            
            data = self._make_request(url, params)
            return data
            
        except APIError as e:
            logger.error(f"Failed to get posts for user {username}: {e}")
            return None

    def get_user_comments(self, username: str, sort: str = "new", 
                         limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get comments made by a specific user."""
        try:
            url = f"{self.BASE_URL}/user/{username}/comments.json"
            params = {
                'sort': sort,
                'limit': limit
            }
            
            data = self._make_request(url, params)
            return data
            
        except APIError as e:
            logger.error(f"Failed to get comments for user {username}: {e}")
            return None

    def set_request_delay(self, delay: float) -> None:
        """Set the delay between requests (in seconds)."""
        self.request_delay = max(0.1, delay)  # Minimum 0.1 seconds
        logger.info(f"Request delay set to {self.request_delay} seconds")

    def batch_get_posts_with_comments(self, subreddit: str, sort: str = "hot", 
                                    post_limit: int = 25, comment_limit: int = 50,
                                    progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Dict[str, Any]]:
        """Batch extraction of posts with their comments for research purposes."""
        logger.info(f"Starting batch extraction from r/{subreddit}: {post_limit} posts, {comment_limit} comments each")
        
        # Get posts
        posts_data = self.get_subreddit_posts(subreddit, sort=sort, limit=post_limit)
        if not posts_data or 'data' not in posts_data or 'children' not in posts_data['data']:
            logger.error(f"Failed to get posts from r/{subreddit}")
            return []
        
        posts = posts_data['data']['children']
        logger.info(f"Retrieved {len(posts)} posts from r/{subreddit}")
        
        results = []
        for i, post in enumerate(posts):
            if 'data' not in post:
                continue
                
            post_data = post['data']
            post_id = post_data.get('id', '')
            
            # Clean and extract post data
            cleaned_post = self._extract_clean_post_data(post_data)
            
            # Get comments for this post
            if post_data.get('num_comments', 0) > 0 and post_id:
                logger.debug(f"Extracting comments for post {i+1}/{len(posts)}: {post_id}")
                comments = self.get_comments(post_id, limit=comment_limit)
                cleaned_post['comments'] = comments if comments else []
            else:
                cleaned_post['comments'] = []
            
            results.append(cleaned_post)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i + 1, len(posts))
        
        logger.info(f"Batch extraction completed: {len(results)} posts with comments")
        return results

    def search_and_extract(self, query: str, subreddit: Optional[str] = None,
                          sort: str = "relevance", time_filter: str = "all",
                          limit: int = 25, include_comments: bool = False,
                          comment_limit: int = 20) -> List[Dict[str, Any]]:
        """Search for posts and optionally extract comments."""
        logger.info(f"Searching for '{query}' in {'r/' + subreddit if subreddit else 'all Reddit'}")
        
        # Search for posts
        search_results = self.search_posts(query, subreddit=subreddit, sort=sort, 
                                         time_filter=time_filter, limit=limit)
        
        if not search_results or 'data' not in search_results or 'children' not in search_results['data']:
            logger.warning(f"No search results found for '{query}'")
            return []
        
        posts = search_results['data']['children']
        logger.info(f"Found {len(posts)} posts for query '{query}'")
        
        results = []
        for post in posts:
            if 'data' not in post:
                continue
                
            post_data = post['data']
            cleaned_post = self._extract_clean_post_data(post_data)
            
            # Extract comments if requested
            if include_comments and post_data.get('num_comments', 0) > 0:
                post_id = post_data.get('id', '')
                if post_id:
                    comments = self.get_comments(post_id, limit=comment_limit)
                    cleaned_post['comments'] = comments if comments else []
                else:
                    cleaned_post['comments'] = []
            else:
                cleaned_post['comments'] = []
            
            results.append(cleaned_post)
        
        return results

    def get_user_activity_summary(self, username: str, post_limit: int = 25, 
                                comment_limit: int = 25) -> Dict[str, Any]:
        """Get comprehensive user activity summary for research."""
        logger.info(f"Getting activity summary for user u/{username}")
        
        # Get user info
        user_info = self.get_user_info(username)
        if not user_info:
            logger.error(f"Could not retrieve info for user u/{username}")
            return {}
        
        # Get user posts
        user_posts_data = self.get_user_posts(username, limit=post_limit)
        user_posts = []
        if user_posts_data and 'data' in user_posts_data and 'children' in user_posts_data['data']:
            for post in user_posts_data['data']['children']:
                if 'data' in post:
                    user_posts.append(self._extract_clean_post_data(post['data']))
        
        # Get user comments
        user_comments_data = self.get_user_comments(username, limit=comment_limit)
        user_comments = []
        if user_comments_data and 'data' in user_comments_data and 'children' in user_comments_data['data']:
            for comment in user_comments_data['data']['children']:
                if 'data' in comment:
                    user_comments.append(self._extract_clean_comment_data(comment['data']))
        
        # Calculate summary statistics
        total_post_score = sum(post.get('score', 0) for post in user_posts)
        total_comment_score = sum(comment.get('score', 0) for comment in user_comments)
        
        # Get subreddit activity
        post_subreddits = {}
        comment_subreddits = {}
        
        for post in user_posts:
            subreddit = post.get('subreddit', 'unknown')
            post_subreddits[subreddit] = post_subreddits.get(subreddit, 0) + 1
        
        for comment in user_comments:
            subreddit = comment.get('subreddit', 'unknown')
            comment_subreddits[subreddit] = comment_subreddits.get(subreddit, 0) + 1
        
        summary = {
            'user_info': {
                'username': username,
                'comment_karma': user_info.get('comment_karma', 0),
                'link_karma': user_info.get('link_karma', 0),
                'created_utc': user_info.get('created_utc', 0),
                'verified': user_info.get('verified', False),
                'has_verified_email': user_info.get('has_verified_email', False),
            },
            'posts': {
                'count': len(user_posts),
                'data': user_posts,
                'total_score': total_post_score,
                'average_score': total_post_score / len(user_posts) if user_posts else 0,
                'subreddit_distribution': post_subreddits,
            },
            'comments': {
                'count': len(user_comments),
                'data': user_comments,
                'total_score': total_comment_score,
                'average_score': total_comment_score / len(user_comments) if user_comments else 0,
                'subreddit_distribution': comment_subreddits,
            },
            'extraction_metadata': {
                'extracted_at': time.time(),
                'post_limit': post_limit,
                'comment_limit': comment_limit,
            }
        }
        
        logger.info(f"User activity summary completed for u/{username}: {len(user_posts)} posts, {len(user_comments)} comments")
        return summary
