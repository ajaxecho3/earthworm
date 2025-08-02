#!/usr/bin/env python3
"""
Earthworm - Multi-Platform Social Media Data Collection Tool
Main application supporting Reddit, Twitter, and other social media platforms.
"""

import os
import sys
import logging
import argparse
import json
import csv
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
import pandas as pd
from enum import Enum

# Add current directory to Python path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters.reddit.reddit_official import RedditOfficial
from adapters.reddit.factory import RedditAdapterFactory
from adapters.reddit.config import RedditConfig
from adapters.reddit.exceptions import AuthenticationError, APIError, RateLimitError

class Platform(Enum):
    """Supported social media platforms."""
    REDDIT = "reddit"
    TWITTER = "twitter"
    # Future platforms can be added here
    # INSTAGRAM = "instagram"
    # TIKTOK = "tiktok"
    # LINKEDIN = "linkedin"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('earthworm.log')
    ]
)
logger = logging.getLogger(__name__)

class EarthwormApp:
    """
    Main application class for Earthworm multi-platform social media data collection.
    
    Supports multiple social media platforms with a unified interface for:
    - Data collection and export
    - Research-grade analytics
    - Cross-platform comparative analysis
    - Academic and professional research workflows
    """
    
    def __init__(self):
        """Initialize the Earthworm application with platform support."""
        self.adapters: Dict[Platform, Any] = {}
        self.active_platform: Optional[Platform] = None
        self.config = self._load_config()
        
        # Initialize available platforms
        self.available_platforms = self._detect_available_platforms()
        logger.info(f"🌍 Earthworm initialized with support for: {[p.value for p in self.available_platforms]}")
    
    def _detect_available_platforms(self) -> List[Platform]:
        """Detect which platforms are available based on configuration."""
        available = []
        
        # Check Reddit availability
        if self.config.client_id and self.config.client_secret:
            available.append(Platform.REDDIT)
        elif self.config.client_id:  # Read-only mode
            available.append(Platform.REDDIT)
        
        # Check Twitter availability (placeholder for future implementation)
        twitter_key = os.getenv('TWITTER_API_KEY')
        if twitter_key:
            available.append(Platform.TWITTER)
        
        return available
    
    def _load_config(self) -> RedditConfig:
        """Load configuration from environment variables."""
        return RedditConfig(
            client_id=os.getenv('REDDIT_CLIENT_ID', ''),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET', ''),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'Earthworm Multi-Platform Data Collector 2.0'),
            timeout=int(os.getenv('REDDIT_TIMEOUT', '30')),
            max_retries=int(os.getenv('REDDIT_MAX_RETRIES', '3')),
            rate_limit_delay=float(os.getenv('REDDIT_BASE_DELAY', '2.0'))
        )
    
    def initialize_platform(self, platform: Union[str, Platform], **kwargs) -> bool:
        """
        Initialize a specific platform adapter.
        
        Args:
            platform: Platform to initialize (reddit, twitter, etc.)
            **kwargs: Platform-specific initialization parameters
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if isinstance(platform, str):
            try:
                platform = Platform(platform.lower())
            except ValueError:
                logger.error(f"❌ Unsupported platform: {platform}")
                return False
        
        if platform not in self.available_platforms:
            logger.error(f"❌ Platform {platform.value} not available. Check configuration.")
            return False
        
        if platform == Platform.REDDIT:
            return self._initialize_reddit(**kwargs)
        elif platform == Platform.TWITTER:
            return self._initialize_twitter(**kwargs)
        else:
            logger.error(f"❌ Platform {platform.value} initialization not implemented yet")
            return False
    
    def _initialize_reddit(self, stealth_mode: bool = False) -> bool:
        """Initialize Reddit adapter with optional stealth mode."""
        try:
            logger.info("🚀 Initializing Reddit adapter...")
            
            # Create Reddit adapter using factory
            reddit_adapter = RedditAdapterFactory.create_adapter(
                adapter_type="official",
                config=self.config
            )
            
            # Enable stealth mode if requested
            if stealth_mode:
                logger.info("🥷 Enabling stealth mode for enhanced anti-bot protection")
                reddit_adapter.enable_stealth_mode()
            
            # Authenticate
            if reddit_adapter.authenticate():
                self.adapters[Platform.REDDIT] = reddit_adapter
                self.active_platform = Platform.REDDIT
                logger.info("✅ Reddit adapter initialized successfully")
                
                # Show configuration status
                anti_bot_status = reddit_adapter.get_anti_bot_status()
                logger.info(f"Anti-bot configuration: {anti_bot_status}")
                
                return True
            else:
                logger.error("❌ Failed to authenticate with Reddit")
                return False
                
        except AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Reddit initialization: {e}")
            return False
    
    def _initialize_twitter(self, **kwargs) -> bool:
        """Initialize Twitter adapter (placeholder for future implementation)."""
        logger.warning("🐦 Twitter adapter not yet implemented")
        # TODO: Implement Twitter adapter initialization
        return False
    
    def get_active_adapter(self):
        """Get the currently active platform adapter."""
        if not self.active_platform or self.active_platform not in self.adapters:
            raise RuntimeError("No platform initialized. Call initialize_platform() first.")
        return self.adapters[self.active_platform]
    
    @property
    def reddit_adapter(self) -> Optional[RedditOfficial]:
        """Get Reddit adapter for backward compatibility."""
        return self.adapters.get(Platform.REDDIT)
    
    def switch_platform(self, platform: Union[str, Platform]) -> bool:
        """Switch to a different initialized platform."""
        if isinstance(platform, str):
            try:
                platform = Platform(platform.lower())
            except ValueError:
                logger.error(f"❌ Unknown platform: {platform}")
                return False
        
        if platform not in self.adapters:
            logger.error(f"❌ Platform {platform.value} not initialized")
            return False
        
        self.active_platform = platform
        logger.info(f"🔄 Switched to {platform.value} platform")
        return True
    
    # ===============================
    # PLATFORM-AGNOSTIC DATA COLLECTION
    # ===============================
    
    def collect_data(self, **kwargs) -> Dict[str, Any]:
        """
        Universal data collection method that works across platforms.
        
        Args:
            **kwargs: Platform-specific parameters
        
        Returns:
            Dict containing collected data with platform context
        """
        if not self.active_platform:
            raise RuntimeError("No platform initialized. Call initialize_platform() first.")
        
        adapter = self.get_active_adapter()
        
        if self.active_platform == Platform.REDDIT:
            return self._collect_reddit_data(adapter, **kwargs)
        elif self.active_platform == Platform.TWITTER:
            return self._collect_twitter_data(adapter, **kwargs)
        else:
            raise RuntimeError(f"Data collection not implemented for {self.active_platform.value}")
    
    def search_across_platform(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Universal search method that works across platforms.
        
        Args:
            query: Search term
            **kwargs: Platform-specific parameters
        
        Returns:
            Dict containing search results with platform context
        """
        if not self.active_platform:
            raise RuntimeError("No platform initialized. Call initialize_platform() first.")
        
        adapter = self.get_active_adapter()
        
        if self.active_platform == Platform.REDDIT:
            return self._search_reddit(adapter, query, **kwargs)
        elif self.active_platform == Platform.TWITTER:
            return self._search_twitter(adapter, query, **kwargs)
        else:
            raise RuntimeError(f"Search not implemented for {self.active_platform.value}")
    
    # ===============================
    # REDDIT-SPECIFIC METHODS
    # ===============================
    
    def _collect_reddit_data(self, adapter: RedditOfficial, subreddit: str = None, 
                           sort: str = "hot", limit: int = 25, 
                           include_comments: bool = False, **kwargs) -> Dict[str, Any]:
        """Collect data from Reddit."""
        if subreddit:
            return self.collect_subreddit_data(subreddit, sort, limit, include_comments)
        else:
            raise ValueError("Reddit data collection requires 'subreddit' parameter")
    
    def _search_reddit(self, adapter: RedditOfficial, query: str, 
                      subreddit: str = None, limit: int = 25, 
                      include_comments: bool = False, **kwargs) -> Dict[str, Any]:
        """Search Reddit."""
        return self.search_reddit_posts(query, subreddit, limit, include_comments)
    
    def collect_subreddit_data(self, subreddit: str, sort: str = "hot", 
                              limit: int = 25, include_comments: bool = False) -> dict:
        """Collect data from a specific subreddit."""
        adapter = self.reddit_adapter
        if not adapter:
            adapter = self.reddit_adapter
        if not adapter:
            raise RuntimeError("Reddit adapter not initialized. Call initialize_platform('reddit') first.")
        
        logger.info(f"📊 Collecting data from r/{subreddit} (sort: {sort}, limit: {limit})")
        
        try:
            # Get posts
            posts_data = adapter.get_subreddit_posts(
                subreddit=subreddit,
                sort=sort,
                limit=limit
            )
            
            if not posts_data:
                logger.warning(f"No posts found for r/{subreddit}")
                return {"posts": [], "comments": [], "platform": "reddit"}
            
            posts = posts_data['data']['children']
            logger.info(f"✅ Retrieved {len(posts)} posts from r/{subreddit}")
            
            all_comments = []
            
            # Collect comments if requested
            if include_comments:
                logger.info("💬 Collecting comments for posts...")
                for i, post in enumerate(posts[:5]):  # Limit to first 5 posts for comments
                    post_id = post['data']['id']
                    logger.info(f"Getting comments for post {i+1}/5: {post_id}")
                    
                    try:
                        comments = adapter.get_comments(post_id, limit=50)
                        if comments:
                            all_comments.extend(comments)
                            logger.info(f"  ✅ Got {len(comments)} comments")
                        
                        # Simulate human behavior between requests
                        if i < 4:  # Don't wait after last post
                            adapter.simulate_human_behavior()
                            
                    except (APIError, RateLimitError) as e:
                        logger.warning(f"  ⚠️  Error getting comments for {post_id}: {e}")
                        continue
                
                logger.info(f"📝 Total comments collected: {len(all_comments)}")
            
            return {
                "platform": "reddit",
                "subreddit": subreddit,
                "posts": posts,
                "comments": all_comments,
                "total_posts": len(posts),
                "total_comments": len(all_comments),
                "collection_metadata": {
                    "sort": sort,
                    "limit": limit,
                    "include_comments": include_comments,
                    "collected_at": datetime.now().isoformat()
                }
            }
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except APIError as e:
            logger.error(f"API error: {e}")
            raise
    
    def search_reddit_posts(self, query: str, subreddit: str = None, 
                           limit: int = 25, include_comments: bool = False) -> dict:
        """Search for Reddit posts using a query."""
        adapter = self.reddit_adapter
        if not adapter:
            raise RuntimeError("Reddit adapter not initialized. Call initialize_platform('reddit') first.")
        
        logger.info(f"🔍 Searching for '{query}' on Reddit{f' in r/{subreddit}' if subreddit else ' across all subreddits'}")
        
        try:
            # Search for posts
            search_results = adapter.search_posts(query, subreddit=subreddit, limit=limit)
            
            if search_results and search_results['data']['children']:
                posts = search_results['data']['children']
                logger.info(f"✅ Found {len(posts)} posts for query '{query}'")
                
                all_comments = []
                
                # Collect comments if requested
                if include_comments:
                    logger.info("💬 Collecting comments for search results...")
                    for i, post in enumerate(posts[:3]):  # Limit to first 3 posts for comments
                        post_id = post['data']['id']
                        logger.info(f"Getting comments for post {i+1}/3: {post_id}")
                        
                        try:
                            comments = adapter.get_comments(post_id, limit=25)
                            if comments:
                                all_comments.extend(comments)
                                logger.info(f"  ✅ Got {len(comments)} comments")
                            
                            # Simulate human behavior between requests
                            if i < 2:  # Don't wait after last post
                                adapter.simulate_human_behavior()
                                
                        except (APIError, RateLimitError) as e:
                            logger.warning(f"  ⚠️  Error getting comments for {post_id}: {e}")
                            continue
                    
                    logger.info(f"📝 Total comments collected: {len(all_comments)}")
                
                return {
                    "platform": "reddit",
                    "query": query,
                    "subreddit": subreddit,
                    "posts": posts,
                    "comments": all_comments,
                    "total_results": len(posts),
                    "total_comments": len(all_comments),
                    "search_metadata": {
                        "limit": limit,
                        "include_comments": include_comments,
                        "searched_at": datetime.now().isoformat()
                    }
                }
            else:
                logger.info(f"No results found for '{query}'")
                return {
                    "platform": "reddit", 
                    "query": query, 
                    "subreddit": subreddit, 
                    "posts": [], 
                    "comments": [], 
                    "total_results": 0, 
                    "total_comments": 0
                }
                
        except (APIError, RateLimitError) as e:
            logger.error(f"Search error: {e}")
            raise
    
    # ===============================
    # TWITTER-SPECIFIC METHODS (PLACEHOLDER)
    # ===============================
    
    def _collect_twitter_data(self, adapter, **kwargs) -> Dict[str, Any]:
        """Collect data from Twitter (placeholder for future implementation)."""
        logger.warning("🐦 Twitter data collection not yet implemented")
        return {
            "platform": "twitter",
            "error": "Twitter adapter not yet implemented",
            "posts": [],
            "comments": [],
            "total_results": 0
        }
    
    def _search_twitter(self, adapter, query: str, **kwargs) -> Dict[str, Any]:
        """Search Twitter (placeholder for future implementation)."""
        logger.warning("🐦 Twitter search not yet implemented")
        return {
            "platform": "twitter",
            "query": query,
            "error": "Twitter adapter not yet implemented",
            "posts": [],
            "comments": [],
            "total_results": 0
        }
    
    # ===============================
    # ADVANCED RESEARCH METHODS
    # ===============================
    
    def collect_temporal_data(self, query: str, start_date: datetime = None, 
                             end_date: datetime = None, **kwargs) -> Dict[str, Any]:
        """Collect data within a specific timeframe across platforms."""
        if not self.active_platform:
            raise RuntimeError("No platform initialized.")
        
        if self.active_platform == Platform.REDDIT:
            adapter = self.reddit_adapter
            if not adapter:
                raise RuntimeError("Reddit adapter not initialized.")
            
            return adapter.search_posts_by_timeframe(
                query=query,
                start_date=start_date,
                end_date=end_date,
                **kwargs
            )
        else:
            raise RuntimeError(f"Temporal data collection not implemented for {self.active_platform.value}")
    
    def collect_from_multiple_sources(self, sources: List[str], **kwargs) -> Dict[str, Any]:
        """Collect data from multiple sources (subreddits, hashtags, etc.)."""
        if not self.active_platform:
            raise RuntimeError("No platform initialized.")
        
        if self.active_platform == Platform.REDDIT:
            adapter = self.reddit_adapter
            if not adapter:
                raise RuntimeError("Reddit adapter not initialized.")
            
            return adapter.collect_from_multiple_subreddits(
                subreddits=sources,
                **kwargs
            )
        else:
            raise RuntimeError(f"Multi-source collection not implemented for {self.active_platform.value}")
    
    def analyze_trending_topics(self, **kwargs) -> Dict[str, Any]:
        """Analyze trending topics on the current platform."""
        if not self.active_platform:
            raise RuntimeError("No platform initialized.")
        
        if self.active_platform == Platform.REDDIT:
            adapter = self.reddit_adapter
            if not adapter:
                raise RuntimeError("Reddit adapter not initialized.")
            
            return adapter.get_trending_topics(**kwargs)
        else:
            raise RuntimeError(f"Trending analysis not implemented for {self.active_platform.value}")
    
    # ===============================
    # LEGACY REDDIT METHODS (MAINTAINED FOR BACKWARD COMPATIBILITY)
    # ===============================
    
    def initialize_reddit(self, stealth_mode: bool = False) -> bool:
        """Legacy method for backward compatibility."""
        return self.initialize_platform(Platform.REDDIT, stealth_mode=stealth_mode)
    
    def search_reddit(self, query: str, subreddit: Optional[str] = None, 
                     limit: int = 25, include_comments: bool = False) -> dict:
        """Legacy search method for backward compatibility."""
        return self.search_reddit_posts(query, subreddit, limit, include_comments)
    
    def get_user_activity(self, username: str, include_posts: bool = True, 
                         include_comments: bool = True) -> dict:
        """Get a user's activity (posts and comments)."""
        if not self.reddit_adapter:
            raise RuntimeError("Reddit adapter not initialized. Call initialize_reddit() first.")
        
        logger.info(f"👤 Collecting activity for user u/{username}")
        
        try:
            # Get user info
            user_info = self.reddit_adapter.get_user_info(username)
            if not user_info:
                logger.warning(f"User u/{username} not found or private")
                return {"user": None, "posts": [], "comments": []}
            
            logger.info(f"✅ Found user u/{username} (karma: {user_info.get('comment_karma', 0) + user_info.get('link_karma', 0)})")
            
            user_posts = []
            user_comments = []
            
            # Get user posts if requested
            if include_posts:
                logger.info("📄 Getting user posts...")
                posts_data = self.reddit_adapter.get_user_posts(username, limit=25)
                if posts_data and posts_data['data']['children']:
                    user_posts = posts_data['data']['children']
                    logger.info(f"  ✅ Retrieved {len(user_posts)} posts")
                
                # Add delay between requests
                self.reddit_adapter.simulate_human_behavior()
            
            # Get user comments if requested
            if include_comments:
                logger.info("💬 Getting user comments...")
                comments_data = self.reddit_adapter.get_user_comments(username, limit=25)
                if comments_data and comments_data['data']['children']:
                    user_comments = comments_data['data']['children']
                    logger.info(f"  ✅ Retrieved {len(user_comments)} comments")
            
            return {
                "user": user_info,
                "posts": user_posts,
                "comments": user_comments,
                "total_posts": len(user_posts),
                "total_comments": len(user_comments)
            }
            
        except (APIError, RateLimitError) as e:
            logger.error(f"Error getting user activity: {e}")
            raise
    
    def export_data(self, data: dict, format: str = "json", filename: Optional[str] = None) -> str:
        """Export collected data in analysis-ready formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not filename:
            if 'query' in data:
                base_name = f"search_{data['query'][:20]}_{timestamp}"
            elif 'subreddit' in data:
                base_name = f"subreddit_{data['subreddit']}_{timestamp}"
            elif 'user' in data and data['user']:
                base_name = f"user_{data['user']['name']}_{timestamp}"
            else:
                base_name = f"reddit_data_{timestamp}"
            
            # Clean filename
            base_name = "".join(c for c in base_name if c.isalnum() or c in "_-").rstrip()
        else:
            base_name = filename.rsplit('.', 1)[0]  # Remove extension if provided
        
        if format.lower() == "json":
            filename = f"{base_name}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        elif format.lower() == "csv":
            filename = f"{base_name}.csv"
            self._export_to_csv(data, filename)
        
        elif format.lower() == "excel":
            filename = f"{base_name}.xlsx"
            self._export_to_excel(data, filename)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return filename
    
    def _export_to_csv(self, data: dict, filename: str):
        """Export data to CSV format for analysis."""
        posts_df = self._create_posts_dataframe(data.get('posts', []))
        comments_df = self._create_comments_dataframe(data.get('comments', []))
        
        # Save posts
        posts_file = filename.replace('.csv', '_posts.csv')
        posts_df.to_csv(posts_file, index=False, encoding='utf-8')
        
        # Save comments if available
        if not comments_df.empty:
            comments_file = filename.replace('.csv', '_comments.csv')
            comments_df.to_csv(comments_file, index=False, encoding='utf-8')
    
    def _export_to_excel(self, data: dict, filename: str):
        """Export data to Excel format with multiple sheets."""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Posts sheet
            posts_df = self._create_posts_dataframe(data.get('posts', []))
            posts_df.to_excel(writer, sheet_name='Posts', index=False)
            
            # Comments sheet
            comments_df = self._create_comments_dataframe(data.get('comments', []))
            if not comments_df.empty:
                comments_df.to_excel(writer, sheet_name='Comments', index=False)
            
            # Summary sheet
            summary_df = self._create_summary_dataframe(data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    def _create_posts_dataframe(self, posts: list) -> pd.DataFrame:
        """Create a structured DataFrame from posts data."""
        if not posts:
            return pd.DataFrame()
        
        processed_posts = []
        for post in posts:
            # Handle nested data structure
            post_data = post.get('data', post) if 'data' in post else post
            
            processed_post = {
                'id': post_data.get('id', ''),
                'title': post_data.get('title', ''),
                'author': post_data.get('author', ''),
                'subreddit': post_data.get('subreddit', ''),
                'score': post_data.get('score', 0),
                'upvote_ratio': post_data.get('upvote_ratio', 0),
                'num_comments': post_data.get('num_comments', 0),
                'created_utc': post_data.get('created_utc', 0),
                'created_date': datetime.fromtimestamp(post_data.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S') if post_data.get('created_utc') else '',
                'selftext': post_data.get('selftext', ''),
                'url': post_data.get('url', ''),
                'permalink': post_data.get('permalink', ''),
                'is_self': post_data.get('is_self', False),
                'post_hint': post_data.get('post_hint', ''),
                'domain': post_data.get('domain', ''),
                'gilded': post_data.get('gilded', 0),
                'over_18': post_data.get('over_18', False),
                'spoiler': post_data.get('spoiler', False),
                'locked': post_data.get('locked', False),
                'stickied': post_data.get('stickied', False),
                'distinguished': post_data.get('distinguished', ''),
                'total_awards_received': post_data.get('total_awards_received', 0),
                'text_length': len(post_data.get('selftext', '')),
                'title_length': len(post_data.get('title', ''))
            }
            processed_posts.append(processed_post)
        
        return pd.DataFrame(processed_posts)
    
    def _create_comments_dataframe(self, comments: list) -> pd.DataFrame:
        """Create a structured DataFrame from comments data."""
        if not comments:
            return pd.DataFrame()
        
        processed_comments = []
        for comment in comments:
            processed_comment = {
                'id': comment.get('id', ''),
                'author': comment.get('author', ''),
                'body': comment.get('body', ''),
                'score': comment.get('score', 0),
                'created_utc': comment.get('created_utc', 0),
                'created_date': datetime.fromtimestamp(comment.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S') if comment.get('created_utc') else '',
                'parent_id': comment.get('parent_id', ''),
                'post_id': comment.get('link_id', '').replace('t3_', '') if comment.get('link_id') else '',
                'subreddit': comment.get('subreddit', ''),
                'depth': comment.get('depth', 0),
                'is_submitter': comment.get('is_submitter', False),
                'gilded': comment.get('gilded', 0),
                'distinguished': comment.get('distinguished', ''),
                'stickied': comment.get('stickied', False),
                'total_awards_received': comment.get('total_awards_received', 0),
                'comment_length': len(comment.get('body', ''))
            }
            processed_comments.append(processed_comment)
        
        return pd.DataFrame(processed_comments)
    
    def _create_summary_dataframe(self, data: dict) -> pd.DataFrame:
        """Create a summary DataFrame with key statistics."""
        posts = data.get('posts', [])
        comments = data.get('comments', [])
        
        summary_data = {
            'Metric': [
                'Collection Date',
                'Query/Subreddit',
                'Total Posts',
                'Total Comments',
                'Average Post Score',
                'Average Comments per Post',
                'Top Author (by posts)',
                'Most Active Subreddit',
                'Average Text Length',
                'Posts with Images/Videos',
                'NSFW Posts',
                'Gilded Posts'
            ],
            'Value': []
        }
        
        # Calculate statistics
        posts_df = self._create_posts_dataframe(posts)
        
        summary_data['Value'].append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        summary_data['Value'].append(data.get('query') or data.get('subreddit', 'N/A'))
        summary_data['Value'].append(len(posts))
        summary_data['Value'].append(len(comments))
        
        if not posts_df.empty:
            summary_data['Value'].append(f"{posts_df['score'].mean():.2f}")
            summary_data['Value'].append(f"{posts_df['num_comments'].mean():.2f}")
            summary_data['Value'].append(posts_df['author'].value_counts().index[0] if not posts_df['author'].value_counts().empty else 'N/A')
            summary_data['Value'].append(posts_df['subreddit'].value_counts().index[0] if not posts_df['subreddit'].value_counts().empty else 'N/A')
            summary_data['Value'].append(f"{posts_df['text_length'].mean():.2f}")
            summary_data['Value'].append(posts_df[posts_df['post_hint'].isin(['image', 'rich:video'])].shape[0])
            summary_data['Value'].append(posts_df['over_18'].sum())
            summary_data['Value'].append(posts_df['gilded'].sum())
        else:
            summary_data['Value'].extend(['0', '0', 'N/A', 'N/A', '0', '0', '0', '0'])
        
        return pd.DataFrame(summary_data)
    
    def analyze_data(self, data: dict) -> dict:
        """Perform statistical analysis on collected data."""
        posts_df = self._create_posts_dataframe(data.get('posts', []))
        comments_df = self._create_comments_dataframe(data.get('comments', []))
        
        analysis = {
            'collection_info': {
                'timestamp': datetime.now().isoformat(),
                'query': data.get('query'),
                'subreddit': data.get('subreddit'),
                'total_posts': len(data.get('posts', [])),
                'total_comments': len(data.get('comments', []))
            },
            'post_analysis': {},
            'comment_analysis': {},
            'temporal_analysis': {},
            'content_analysis': {}
        }
        
        if not posts_df.empty:
            analysis['post_analysis'] = {
                'score_stats': {
                    'mean': float(posts_df['score'].mean()),
                    'median': float(posts_df['score'].median()),
                    'std': float(posts_df['score'].std()),
                    'min': int(posts_df['score'].min()),
                    'max': int(posts_df['score'].max())
                },
                'engagement_stats': {
                    'avg_comments_per_post': float(posts_df['num_comments'].mean()),
                    'avg_upvote_ratio': float(posts_df['upvote_ratio'].mean()),
                    'total_engagement': int(posts_df['score'].sum() + posts_df['num_comments'].sum())
                },
                'content_distribution': {
                    'self_posts': int(posts_df['is_self'].sum()),
                    'link_posts': int((~posts_df['is_self']).sum()),
                    'nsfw_posts': int(posts_df['over_18'].sum()),
                    'gilded_posts': int(posts_df['gilded'].sum())
                },
                'top_authors': posts_df['author'].value_counts().head(5).to_dict(),
                'top_subreddits': posts_df['subreddit'].value_counts().head(5).to_dict() if 'subreddit' in posts_df.columns else {}
            }
            
            # Temporal analysis
            if 'created_utc' in posts_df.columns:
                posts_df['hour'] = pd.to_datetime(posts_df['created_utc'], unit='s').dt.hour
                posts_df['day_of_week'] = pd.to_datetime(posts_df['created_utc'], unit='s').dt.day_name()
                
                analysis['temporal_analysis'] = {
                    'posts_by_hour': posts_df['hour'].value_counts().sort_index().to_dict(),
                    'posts_by_day': posts_df['day_of_week'].value_counts().to_dict(),
                    'posting_timespan': {
                        'earliest': posts_df['created_date'].min(),
                        'latest': posts_df['created_date'].max()
                    }
                }
            
            # Content analysis
            analysis['content_analysis'] = {
                'title_length_stats': {
                    'mean': float(posts_df['title_length'].mean()),
                    'median': float(posts_df['title_length'].median()),
                    'max': int(posts_df['title_length'].max())
                },
                'text_length_stats': {
                    'mean': float(posts_df['text_length'].mean()),
                    'median': float(posts_df['text_length'].median()),
                    'max': int(posts_df['text_length'].max())
                }
            }
        
        if not comments_df.empty:
            analysis['comment_analysis'] = {
                'score_stats': {
                    'mean': float(comments_df['score'].mean()),
                    'median': float(comments_df['score'].median()),
                    'std': float(comments_df['score'].std())
                },
                'length_stats': {
                    'mean': float(comments_df['comment_length'].mean()),
                    'median': float(comments_df['comment_length'].median()),
                    'max': int(comments_df['comment_length'].max())
                },
                'top_commenters': comments_df['author'].value_counts().head(5).to_dict(),
                'comment_depth_distribution': comments_df['depth'].value_counts().to_dict()
            }
        
        return analysis
    
    def show_rate_limit_status(self):
        """Display current rate limit status."""
        if not self.reddit_adapter:
            logger.warning("Reddit adapter not initialized")
            return
        
        rate_status = self.reddit_adapter.get_rate_limit_status()
        anti_bot_status = self.reddit_adapter.get_anti_bot_status()
        
        print("\n📊 Rate Limit & Anti-Bot Status:")
        print("=" * 50)
        
        print("\nRate Limiting:")
        for key, value in rate_status.items():
            if value is not None:
                print(f"  {key}: {value}")
        
        print("\nAnti-Bot Configuration:")
        for key, value in anti_bot_status.items():
            print(f"  {key}: {value}")
    
    def run_interactive_mode(self):
        """Run the application in interactive menu mode."""
        print("🌍 Welcome to Earthworm - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\n📋 Main Menu:")
            print("1. 🔍 Search Posts")
            print("2. 📊 Collect from Subreddit")
            print("3. 👤 Analyze User Activity")
            print("4. 🔄 Multi-Source Collection")
            print("5. 📈 Trending Analysis")
            print("6. 🕒 Temporal Analysis")
            print("7. ⚙️  Platform Settings")
            print("8. 💾 Export Options")
            print("9. 🎯 Demo Mode")
            print("0. ❌ Exit")
            
            choice = input("\nSelect an option (0-9): ").strip()
            
            if choice == "0":
                print("👋 Thanks for using Earthworm!")
                break
            elif choice == "1":
                self._interactive_search()
            elif choice == "2":
                self._interactive_subreddit_collection()
            elif choice == "3":
                self._interactive_user_analysis()
            elif choice == "4":
                self._interactive_multi_source()
            elif choice == "5":
                self._interactive_trending()
            elif choice == "6":
                self._interactive_temporal()
            elif choice == "7":
                self._interactive_platform_settings()
            elif choice == "8":
                self._interactive_export()
            elif choice == "9":
                self.run_demo()
            else:
                print("❌ Invalid option. Please try again.")
    
    def _interactive_search(self):
        """Interactive search interface."""
        print("\n🔍 Search Posts")
        print("-" * 30)
        
        query = input("Enter search term: ").strip()
        if not query:
            print("❌ Search term cannot be empty")
            return
        
        platform = self._select_platform()
        if not platform:
            return
        
        # Initialize platform if needed
        if not self.initialize_platform(platform):
            print(f"❌ Failed to initialize {platform}")
            return
        
        limit = self._get_number_input("Number of results (default 25): ", 25, 1, 500)
        include_comments = self._get_yes_no("Include comments? (y/n): ")
        
        if platform == 'reddit':
            subreddit = input("Specific subreddit (optional, press Enter for all): ").strip()
            subreddit = subreddit if subreddit else None
        
        print(f"\n🔍 Searching for '{query}'...")
        
        try:
            data = self.search_across_platform(
                query=query,
                subreddit=subreddit if platform == 'reddit' else None,
                limit=limit,
                include_comments=include_comments
            )
            
            self._display_search_results(data, query)
            self._offer_export_analysis(data)
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    def _interactive_subreddit_collection(self):
        """Interactive subreddit collection."""
        print("\n📊 Subreddit Collection")
        print("-" * 30)
        
        if not self.initialize_platform('reddit'):
            print("❌ Failed to initialize Reddit")
            return
        
        subreddit = input("Enter subreddit name (without r/): ").strip()
        if not subreddit:
            print("❌ Subreddit name cannot be empty")
            return
        
        print("\nSort options:")
        print("1. Hot (default)")
        print("2. New")
        print("3. Top")
        print("4. Rising")
        
        sort_choice = input("Select sort method (1-4): ").strip()
        sort_map = {"1": "hot", "2": "new", "3": "top", "4": "rising"}
        sort = sort_map.get(sort_choice, "hot")
        
        limit = self._get_number_input("Number of posts (default 25): ", 25, 1, 500)
        include_comments = self._get_yes_no("Include comments? (y/n): ")
        
        print(f"\n📊 Collecting from r/{subreddit}...")
        
        try:
            data = self.collect_subreddit_data(
                subreddit=subreddit,
                sort=sort,
                limit=limit,
                include_comments=include_comments
            )
            
            print(f"✅ Collected {data['total_posts']} posts")
            if include_comments:
                print(f"✅ Collected {data['total_comments']} comments")
            
            self._offer_export_analysis(data)
            
        except Exception as e:
            print(f"❌ Collection failed: {e}")
    
    def _interactive_multi_source(self):
        """Interactive multi-source collection."""
        print("\n🔄 Multi-Source Collection")
        print("-" * 30)
        
        if not self.initialize_platform('reddit'):
            print("❌ Failed to initialize Reddit")
            return
        
        print("Enter subreddit names (one per line, empty line to finish):")
        subreddits = []
        while True:
            sub = input(f"Subreddit {len(subreddits) + 1}: ").strip()
            if not sub:
                break
            subreddits.append(sub)
        
        if not subreddits:
            print("❌ No subreddits provided")
            return
        
        limit_per_sub = self._get_number_input("Posts per subreddit (default 10): ", 10, 1, 100)
        
        print(f"\n🔄 Collecting from {len(subreddits)} subreddits...")
        
        try:
            data = self.collect_from_multiple_sources(
                sources=subreddits,
                limit_per_sub=limit_per_sub
            )
            
            if data and data.get('results'):
                total_posts = data['summary']['total_posts']
                successful = data['summary']['successful_collections']
                print(f"✅ Collected {total_posts} posts from {successful}/{len(subreddits)} sources")
                
                self._offer_export_analysis(data)
            
        except Exception as e:
            print(f"❌ Multi-source collection failed: {e}")
    
    def _interactive_trending(self):
        """Interactive trending analysis."""
        print("\n📈 Trending Analysis")
        print("-" * 30)
        
        if not self.initialize_platform('reddit'):
            print("❌ Failed to initialize Reddit")
            return
        
        subreddit = input("Subreddit for analysis (default: all): ").strip()
        subreddit = subreddit if subreddit else "all"
        
        print("\nTime filter:")
        print("1. Hour")
        print("2. Day (default)")
        print("3. Week")
        
        time_choice = input("Select time filter (1-3): ").strip()
        time_map = {"1": "hour", "2": "day", "3": "week"}
        time_filter = time_map.get(time_choice, "day")
        
        print(f"\n📈 Analyzing trends in r/{subreddit} ({time_filter})...")
        
        try:
            data = self.analyze_trending_topics(
                subreddit=subreddit,
                time_filter=time_filter
            )
            
            if data and data.get('data'):
                trending_data = data['data']
                print(f"📊 Analyzed {len(trending_data['posts'])} trending posts")
                
                if trending_data.get('top_keywords'):
                    print("\n🔥 Top trending keywords:")
                    for i, (keyword, count) in enumerate(list(trending_data['top_keywords'].items())[:10], 1):
                        print(f"  {i}. {keyword}: {count} mentions")
                
                self._offer_export_analysis(data)
            
        except Exception as e:
            print(f"❌ Trending analysis failed: {e}")
    
    def _select_platform(self):
        """Interactive platform selection."""
        if len(self.available_platforms) == 1:
            return self.available_platforms[0].value
        
        print("\nAvailable platforms:")
        for i, platform in enumerate(self.available_platforms, 1):
            print(f"{i}. {platform.value.capitalize()}")
        
        while True:
            choice = input(f"Select platform (1-{len(self.available_platforms)}): ").strip()
            try:
                index = int(choice) - 1
                if 0 <= index < len(self.available_platforms):
                    return self.available_platforms[index].value
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Please enter a number")
    
    def _get_number_input(self, prompt: str, default: int, min_val: int = 1, max_val: int = 1000):
        """Get validated number input."""
        while True:
            response = input(prompt).strip()
            if not response:
                return default
            try:
                value = int(response)
                if min_val <= value <= max_val:
                    return value
                else:
                    print(f"❌ Please enter a number between {min_val} and {max_val}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def _get_yes_no(self, prompt: str) -> bool:
        """Get yes/no input."""
        while True:
            response = input(prompt).strip().lower()
            if response in ['y', 'yes', '1', 'true']:
                return True
            elif response in ['n', 'no', '0', 'false', '']:
                return False
            else:
                print("❌ Please enter y/n")
    
    def _display_search_results(self, data: dict, query: str):
        """Display search results in a formatted way."""
        posts = data.get('posts', [])
        if not posts:
            print(f"❌ No results found for '{query}'")
            return
        
        print(f"\n✅ Found {len(posts)} results for '{query}'")
        print("=" * 60)
        
        for i, post in enumerate(posts[:5], 1):  # Show first 5
            post_data = post.get('data', post)
            print(f"{i}. {post_data.get('title', 'N/A')[:70]}...")
            print(f"   👤 u/{post_data.get('author', 'unknown')}")
            print(f"   📊 Score: {post_data.get('score', 0)} | 💬 Comments: {post_data.get('num_comments', 0)}")
            if data.get('platform') == 'reddit':
                print(f"   📍 r/{post_data.get('subreddit', 'unknown')}")
            print("-" * 60)
        
        if len(posts) > 5:
            print(f"... and {len(posts) - 5} more results")
    
    def _offer_export_analysis(self, data: dict):
        """Offer export and analysis options."""
        if not data or not data.get('posts'):
            return
        
        print("\n📋 What would you like to do with this data?")
        print("1. 📊 Analyze data")
        print("2. 💾 Export data")
        print("3. 🔬 Analyze and export")
        print("4. ⏭️  Continue (do nothing)")
        
        choice = input("Select option (1-4): ").strip()
        
        if choice in ["1", "3"]:
            print("\n🔬 Performing analysis...")
            analysis = self.analyze_data(data)
            self.display_analysis_summary(analysis)
        
        if choice in ["2", "3"]:
            print("\nExport formats:")
            print("1. JSON")
            print("2. CSV")
            print("3. Excel")
            
            format_choice = input("Select format (1-3): ").strip()
            format_map = {"1": "json", "2": "csv", "3": "excel"}
            export_format = format_map.get(format_choice, "json")
            
            filename = input("Custom filename (optional): ").strip()
            filename = filename if filename else None
            
            try:
                exported_file = self.export_data(data, format=export_format, filename=filename)
                print(f"✅ Data exported to: {exported_file}")
            except Exception as e:
                print(f"❌ Export failed: {e}")

    def display_analysis_summary(self, analysis: dict):
        """Display a formatted analysis summary."""
        print("\n📈 Data Analysis Summary")
        print("=" * 60)
        
        # Collection info
        info = analysis['collection_info']
        print(f"Collection Date: {info['timestamp'][:19]}")
        print(f"Target: {info['query'] or info['subreddit'] or 'N/A'}")
        print(f"Posts Collected: {info['total_posts']}")
        print(f"Comments Collected: {info['total_comments']}")
        
        # Post analysis
        if analysis['post_analysis']:
            post_stats = analysis['post_analysis']
            print(f"\n📊 Post Statistics:")
            print(f"  Average Score: {post_stats['score_stats']['mean']:.1f}")
            print(f"  Average Comments per Post: {post_stats['engagement_stats']['avg_comments_per_post']:.1f}")
            print(f"  Average Upvote Ratio: {post_stats['engagement_stats']['avg_upvote_ratio']:.3f}")
            print(f"  Self Posts: {post_stats['content_distribution']['self_posts']}")
            print(f"  NSFW Posts: {post_stats['content_distribution']['nsfw_posts']}")
            
            if post_stats['top_authors']:
                top_author = list(post_stats['top_authors'].keys())[0]
                post_count = list(post_stats['top_authors'].values())[0]
                print(f"  Most Active Author: u/{top_author} ({post_count} posts)")
        
        # Comment analysis
        if analysis['comment_analysis']:
            comment_stats = analysis['comment_analysis']
            print(f"\n💬 Comment Statistics:")
            print(f"  Average Comment Score: {comment_stats['score_stats']['mean']:.1f}")
            print(f"  Average Comment Length: {comment_stats['length_stats']['mean']:.0f} characters")
            
            if comment_stats['top_commenters']:
                top_commenter = list(comment_stats['top_commenters'].keys())[0]
                comment_count = list(comment_stats['top_commenters'].values())[0]
                print(f"  Most Active Commenter: u/{top_commenter} ({comment_count} comments)")
        
        # Temporal analysis
        if analysis['temporal_analysis']:
            temporal = analysis['temporal_analysis']
            if 'posting_timespan' in temporal:
                print(f"\n⏰ Temporal Analysis:")
                print(f"  Time Range: {temporal['posting_timespan']['earliest']} to {temporal['posting_timespan']['latest']}")
                
                if temporal['posts_by_hour']:
                    peak_hour = max(temporal['posts_by_hour'], key=temporal['posts_by_hour'].get)
                    print(f"  Peak Posting Hour: {peak_hour}:00 ({temporal['posts_by_hour'][peak_hour]} posts)")
        
        print(f"\n✅ Analysis complete. Data ready for research!")
    
    
    def run_demo(self, stealth_mode: bool = False):
        """Run a demonstration of the application features."""
        print("🌍 Welcome to Earthworm - Social Media Data Collector")
        print("=" * 60)
        
        # Initialize Reddit adapter
        if not self.initialize_reddit(stealth_mode=stealth_mode):
            logger.error("Failed to initialize Reddit adapter")
            return
        
        try:
            # Demo 1: Collect subreddit data
            print("\n🔥 Demo 1: Collecting hot posts from r/python")
            python_data = self.collect_subreddit_data("python", sort="hot", limit=5)
            print(f"Collected {python_data['total_posts']} posts from r/python")
            
            # Show sample post
            if python_data['posts']:
                sample_post = python_data['posts'][0]['data']
                print(f"\nSample post: '{sample_post['title'][:60]}...'")
                print(f"Score: {sample_post['score']}, Comments: {sample_post['num_comments']}")
            
            # Demo 2: Search functionality
            print("\n🔍 Demo 2: Searching for 'machine learning' posts")
            search_results = self.search_reddit("machine learning", limit=3)
            print(f"Found {search_results['total_results']} results")
            
            # Demo 3: Search with comments
            print("\n💬 Demo 3: Search with comments collection")
            search_with_comments = self.search_reddit("python", limit=2, include_comments=True)
            print(f"Found {search_with_comments['total_results']} posts with {search_with_comments['total_comments']} comments")
            
            # Demo 4: Rate limit status
            print("\n📊 Demo 4: Rate Limit Status")
            self.show_rate_limit_status()
            
            print("\n✅ Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"Demo error: {e}")
        
        finally:
            # Reset to normal mode if stealth was enabled
            if stealth_mode and self.reddit_adapter:
                self.reddit_adapter.disable_stealth_mode()
                logger.info("🔄 Reset to normal mode")

def main():
    """Main entry point supporting both interactive and command-line modes."""
    parser = argparse.ArgumentParser(description='Earthworm - Multi-Platform Social Media Data Collector')
    
    # Mode selection
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive menu mode (recommended for beginners)')
    parser.add_argument('--config', action='store_true',
                       help='Run configuration wizard')
    
    # Quick actions (simplified)
    parser.add_argument('--quick-search', type=str,
                       help='Quick search (e.g., --quick-search "python programming")')
    parser.add_argument('--quick-subreddit', type=str,
                       help='Quick subreddit collection (e.g., --quick-subreddit python)')
    
    # Platform selection
    parser.add_argument('--platform', type=str, choices=['reddit', 'twitter'], default='reddit',
                       help='Social media platform to use (default: reddit)')
    
    # General options
    parser.add_argument('--stealth', action='store_true', 
                       help='Enable stealth mode for enhanced anti-bot protection')
    parser.add_argument('--demo', action='store_true', 
                       help='Run demonstration of platform features')
    parser.add_argument('--list-platforms', action='store_true',
                       help='List available platforms and their status')
    
    # Advanced options (for power users)
    parser.add_argument('--advanced', action='store_true',
                       help='Show advanced command-line options')
    
    args, unknown_args = parser.parse_known_args()
    
    # Initialize Earthworm app
    app = EarthwormApp()
    
    # Handle special modes first
    if args.list_platforms:
        print("🌍 Earthworm - Available Platforms:")
        for platform in app.available_platforms:
            status = "✅ Ready" if platform in app.available_platforms else "❌ Not configured"
            print(f"  {platform.value.capitalize()}: {status}")
        
        print(f"\nConfigured platforms: {len(app.available_platforms)}")
        
        if Platform.REDDIT in app.available_platforms:
            print("  📊 Reddit: Full research capabilities available")
        if Platform.TWITTER in app.available_platforms:
            print("  🐦 Twitter: Coming soon")
        
        return
    
    if args.config:
        run_configuration_wizard()
        return
    
    if args.advanced:
        show_advanced_help()
        return
    
    # Validate platform-specific credentials
    if args.platform == 'reddit':
        if not os.getenv('REDDIT_CLIENT_ID'):
            print("❌ Error: Reddit API credentials not found!")
            print("Run with --config to set up credentials")
            sys.exit(1)
    elif args.platform == 'twitter':
        print("❌ Twitter integration coming soon. Use --platform reddit for now.")
        sys.exit(1)
    
    # Handle interactive mode
    if args.interactive:
        if app.initialize_platform(args.platform, stealth_mode=args.stealth):
            app.run_interactive_mode()
        else:
            print("❌ Failed to initialize platform")
        return
    
    # Handle quick actions
    if args.quick_search:
        if app.initialize_platform(args.platform, stealth_mode=args.stealth):
            try:
                data = app.search_across_platform(query=args.quick_search, limit=10)
                app._display_search_results(data, args.quick_search)
                app._offer_export_analysis(data)
            except Exception as e:
                print(f"❌ Search failed: {e}")
        return
    
    if args.quick_subreddit:
        if app.initialize_platform('reddit', stealth_mode=args.stealth):
            try:
                data = app.collect_subreddit_data(args.quick_subreddit, limit=10)
                print(f"✅ Collected {data['total_posts']} posts from r/{args.quick_subreddit}")
                app._offer_export_analysis(data)
            except Exception as e:
                print(f"❌ Collection failed: {e}")
        return
    
    # Handle demo
    if args.demo:
        if app.initialize_platform(args.platform, stealth_mode=args.stealth):
            app.run_demo(stealth_mode=args.stealth)
        return
    
    # If no specific action, show user-friendly help
    if not unknown_args:
        show_getting_started()
    else:
        # Fall back to advanced CLI parsing for power users
        parse_advanced_arguments(unknown_args, app, args)

def show_getting_started():
    """Show user-friendly getting started guide."""
    print("🌍 Welcome to Earthworm - Social Media Data Collector")
    print("=" * 60)
    print("\n� Getting Started:")
    print("  --interactive     Launch interactive menu (recommended)")
    print("  --config          Set up API credentials")
    print("  --demo            See what Earthworm can do")
    print("\n⚡ Quick Actions:")
    print('  --quick-search "AI research"    Quick search')
    print("  --quick-subreddit python        Quick subreddit collection")
    print("\n🔧 Options:")
    print("  --list-platforms  Show available platforms")
    print("  --advanced        Show all command-line options")
    print("\n💡 Examples:")
    print("  earthworm --interactive")
    print('  earthworm --quick-search "machine learning"')
    print("  earthworm --quick-subreddit datascience")
    print("  earthworm --demo --stealth")

def run_configuration_wizard():
    """Interactive configuration wizard."""
    print("🔧 Earthworm Configuration Wizard")
    print("=" * 40)
    
    print("\n� Reddit Configuration:")
    print("Visit https://www.reddit.com/prefs/apps to create an app")
    
    client_id = input("Reddit Client ID: ").strip()
    client_secret = input("Reddit Client Secret (optional for read-only): ").strip()
    user_agent = input("User Agent (optional): ").strip()
    
    if not user_agent:
        user_agent = "Earthworm Data Collector 2.0"
    
    # Create .env file
    env_content = f"""# Earthworm Configuration
REDDIT_CLIENT_ID={client_id}
REDDIT_CLIENT_SECRET={client_secret}
REDDIT_USER_AGENT={user_agent}
REDDIT_PREFER_AUTHENTICATED=false
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Configuration saved to .env file")
        print("🎯 Ready to use Earthworm! Try: earthworm --interactive")
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")

def show_advanced_help():
    """Show advanced command-line options."""
    print("🔧 Advanced Command-Line Options")
    print("=" * 40)
    print("\nFor power users and automation:")
    print("\n📊 Data Collection:")
    print("  --subreddit NAME          Collect from specific subreddit")
    print("  --search QUERY            Search posts")
    print("  --user USERNAME           Get user activity")
    print("  --limit N                 Limit results (default: 25)")
    print("  --comments                Include comments")
    print("\n🔬 Research Features:")
    print("  --temporal                Enable temporal analysis")
    print("  --start-date YYYY-MM-DD   Start date for temporal analysis")
    print("  --end-date YYYY-MM-DD     End date for temporal analysis")
    print("  --multi-source A B C      Collect from multiple sources")
    print("  --trending                Analyze trending topics")
    print("\n💾 Export & Analysis:")
    print("  --export FORMAT           Export (json/csv/excel)")
    print("  --analyze                 Perform statistical analysis")
    print("  --filename NAME           Custom filename")
    print("\n⚙️ Platform Options:")
    print("  --platform NAME           Select platform (reddit/twitter)")
    print("  --stealth                 Enable anti-bot protection")

def parse_advanced_arguments(unknown_args, app, base_args):
    """Parse advanced command-line arguments for power users."""
    # Create a new parser for advanced options
    advanced_parser = argparse.ArgumentParser(add_help=False)
    
    # Data collection options
    advanced_parser.add_argument('--subreddit', type=str)
    advanced_parser.add_argument('--search', type=str)
    advanced_parser.add_argument('--user', type=str)
    advanced_parser.add_argument('--limit', type=int, default=25)
    advanced_parser.add_argument('--comments', action='store_true')
    
    # Advanced research options
    advanced_parser.add_argument('--temporal', action='store_true')
    advanced_parser.add_argument('--start-date', type=str)
    advanced_parser.add_argument('--end-date', type=str)
    advanced_parser.add_argument('--multi-source', type=str, nargs='+')
    advanced_parser.add_argument('--trending', action='store_true')
    
    # Export and analysis options
    advanced_parser.add_argument('--export', type=str, choices=['json', 'csv', 'excel'])
    advanced_parser.add_argument('--analyze', action='store_true')
    advanced_parser.add_argument('--filename', type=str)
    
    try:
        args = advanced_parser.parse_args(unknown_args)
        execute_advanced_commands(app, args, base_args)
    except SystemExit:
        print("❌ Invalid advanced options. Use --advanced to see all options.")

def execute_advanced_commands(app, args, base_args):
    """Execute advanced command-line operations."""
    # Initialize the selected platform
    print(f"🚀 Initializing {base_args.platform.capitalize()} platform...")
    if not app.initialize_platform(base_args.platform, stealth_mode=base_args.stealth):
        logger.error(f"Failed to initialize {base_args.platform}. Exiting.")
        sys.exit(1)
    
    try:
        data = None
        
        # Handle advanced research operations
        if args.temporal and args.search:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else None
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else None
            
            print(f"🕒 Performing temporal analysis for '{args.search}'")
            data = app.collect_temporal_data(
                query=args.search,
                start_date=start_date,
                end_date=end_date,
                limit=args.limit
            )
        
        elif args.multi_source:
            print(f"🔄 Collecting from multiple sources: {args.multi_source}")
            data = app.collect_from_multiple_sources(
                sources=args.multi_source,
                limit_per_sub=args.limit
            )
        
        elif args.trending:
            print(f"� Analyzing trending topics on {base_args.platform}")
            data = app.analyze_trending_topics()
        
        elif args.subreddit:
            data = app.collect_subreddit_data(
                args.subreddit, 
                limit=args.limit, 
                include_comments=args.comments
            )
            print(f"Collected {data['total_posts']} posts from r/{args.subreddit}")
        
        elif args.search:
            data = app.search_across_platform(
                query=args.search,
                limit=args.limit,
                include_comments=args.comments
            )
            print(f"Found {data.get('total_results', 0)} results for '{args.search}'")
        
        elif args.user:
            data = app.get_user_activity(args.user)
            print(f"User u/{args.user}: {data['total_posts']} posts, {data['total_comments']} comments")
        
        # Perform analysis if requested
        if data and args.analyze:
            print("\n� Performing statistical analysis...")
            analysis = app.analyze_data(data)
            app.display_analysis_summary(analysis)
        
        # Export data if requested
        if data and args.export:
            filename = app.export_data(data, format=args.export, filename=args.filename)
            print(f"\n💾 Data exported to: {filename}")
    
    except Exception as e:
        logger.error(f"Advanced operation failed: {e}")
        sys.exit(1)

def app():
    """Legacy function to execute the script."""
    print("🌍 Earthworm - Enhanced Social Media Data Collector")
    print("Use 'python main.py --help' for available options")
    print("Quick start: python main.py --demo")

if __name__ == "__main__":
    main()
