#!/usr/bin/env python3
"""
Earthworm - Social Media Data Collection Tool
Main application with enhanced Reddit API integration and anti-bot detection.
"""

import os
import sys
import logging
import argparse
import json
import csv
from datetime import datetime
from typing import Optional
import pandas as pd

# Add current directory to Python path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters.reddit.reddit_official import RedditOfficial
from adapters.reddit.factory import RedditAdapterFactory
from adapters.reddit.config import RedditConfig
from adapters.reddit.exceptions import AuthenticationError, APIError, RateLimitError

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
    """Main application class for Earthworm social media data collection."""
    
    def __init__(self):
        self.reddit_adapter: Optional[RedditOfficial] = None
        self.config = self._load_config()
    
    def _load_config(self) -> RedditConfig:
        """Load configuration from environment variables."""
        return RedditConfig(
            client_id=os.getenv('REDDIT_CLIENT_ID', ''),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET', ''),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'Earthworm Data Collector 1.0'),
            timeout=int(os.getenv('REDDIT_TIMEOUT', '30')),
            max_retries=int(os.getenv('REDDIT_MAX_RETRIES', '3')),
            rate_limit_delay=float(os.getenv('REDDIT_BASE_DELAY', '2.0'))
        )
    
    def initialize_reddit(self, stealth_mode: bool = False) -> bool:
        """Initialize Reddit adapter with optional stealth mode."""
        try:
            logger.info("🚀 Initializing Reddit adapter...")
            
            # Create Reddit adapter using factory
            self.reddit_adapter = RedditAdapterFactory.create_adapter(
                adapter_type="official",
                config=self.config
            )
            
            # Enable stealth mode if requested
            if stealth_mode:
                logger.info("🥷 Enabling stealth mode for enhanced anti-bot protection")
                self.reddit_adapter.enable_stealth_mode()
            
            # Authenticate
            if self.reddit_adapter.authenticate():
                logger.info("✅ Reddit adapter initialized successfully")
                
                # Show configuration status
                anti_bot_status = self.reddit_adapter.get_anti_bot_status()
                logger.info(f"Anti-bot configuration: {anti_bot_status}")
                
                return True
            else:
                logger.error("❌ Failed to authenticate with Reddit")
                return False
                
        except AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {e}")
            return False
    
    def collect_subreddit_data(self, subreddit: str, sort: str = "hot", 
                              limit: int = 25, include_comments: bool = False) -> dict:
        """Collect data from a specific subreddit."""
        if not self.reddit_adapter:
            raise RuntimeError("Reddit adapter not initialized. Call initialize_reddit() first.")
        
        logger.info(f"📊 Collecting data from r/{subreddit} (sort: {sort}, limit: {limit})")
        
        try:
            # Get posts
            posts_data = self.reddit_adapter.get_subreddit_posts(
                subreddit=subreddit,
                sort=sort,
                limit=limit
            )
            
            if not posts_data:
                logger.warning(f"No posts found for r/{subreddit}")
                return {"posts": [], "comments": []}
            
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
                        comments = self.reddit_adapter.get_comments(post_id, limit=50)
                        if comments:
                            all_comments.extend(comments)
                            logger.info(f"  ✅ Got {len(comments)} comments")
                        
                        # Simulate human behavior between requests
                        if i < 4:  # Don't wait after last post
                            self.reddit_adapter.simulate_human_behavior()
                            
                    except (APIError, RateLimitError) as e:
                        logger.warning(f"  ⚠️  Error getting comments for {post_id}: {e}")
                        continue
                
                logger.info(f"📝 Total comments collected: {len(all_comments)}")
            
            return {
                "subreddit": subreddit,
                "posts": posts,
                "comments": all_comments,
                "total_posts": len(posts),
                "total_comments": len(all_comments)
            }
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except APIError as e:
            logger.error(f"API error: {e}")
            raise
    
    def search_reddit(self, query: str, subreddit: Optional[str] = None, 
                     limit: int = 25, include_comments: bool = False) -> dict:
        """Search Reddit for posts matching a query."""
        if not self.reddit_adapter:
            raise RuntimeError("Reddit adapter not initialized. Call initialize_reddit() first.")
        
        search_location = f"r/{subreddit}" if subreddit else "all subreddits"
        logger.info(f"🔍 Searching '{query}' in {search_location} (limit: {limit})")
        
        try:
            results = self.reddit_adapter.search_posts(
                query=query,
                subreddit=subreddit,
                limit=limit
            )
            
            if results and results.get('data', {}).get('children'):
                posts = [child['data'] for child in results['data']['children']]
                logger.info(f"✅ Found {len(posts)} posts matching '{query}'")
                
                all_comments = []
                
                # Collect comments if requested
                if include_comments:
                    logger.info("💬 Collecting comments for search results...")
                    for i, post in enumerate(posts[:5]):  # Limit to first 5 posts for comments
                        post_id = post['id']
                        logger.info(f"Getting comments for post {i+1}/5: {post_id}")
                        
                        try:
                            comments = self.reddit_adapter.get_comments(post_id, limit=50)
                            if comments:
                                all_comments.extend(comments)
                                logger.info(f"  ✅ Got {len(comments)} comments")
                            
                            # Simulate human behavior between requests
                            if i < 4:  # Don't wait after last post
                                self.reddit_adapter.simulate_human_behavior()
                                
                        except (APIError, RateLimitError) as e:
                            logger.warning(f"  ⚠️  Error getting comments for {post_id}: {e}")
                            continue
                    
                    logger.info(f"📝 Total comments collected: {len(all_comments)}")
                
                return {
                    "query": query,
                    "subreddit": subreddit,
                    "posts": posts,
                    "comments": all_comments,
                    "total_results": len(posts),
                    "total_comments": len(all_comments)
                }
            else:
                logger.info(f"No results found for '{query}'")
                return {"query": query, "subreddit": subreddit, "posts": [], "comments": [], "total_results": 0, "total_comments": 0}
                
        except (APIError, RateLimitError) as e:
            logger.error(f"Search error: {e}")
            raise
    
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
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Earthworm - Social Media Data Collector')
    parser.add_argument('--stealth', action='store_true', 
                       help='Enable stealth mode for enhanced anti-bot protection')
    parser.add_argument('--demo', action='store_true', 
                       help='Run demonstration of features')
    parser.add_argument('--subreddit', type=str, 
                       help='Collect data from specific subreddit')
    parser.add_argument('--search', type=str, 
                       help='Search Reddit for posts')
    parser.add_argument('--user', type=str, 
                       help='Get user activity')
    parser.add_argument('--limit', type=int, default=25, 
                       help='Limit number of results (default: 25)')
    parser.add_argument('--comments', action='store_true', 
                       help='Include comments in data collection (for subreddit and search operations)')
    parser.add_argument('--export', type=str, choices=['json', 'csv', 'excel'], 
                       help='Export data in specified format for analysis')
    parser.add_argument('--analyze', action='store_true', 
                       help='Perform statistical analysis on collected data')
    parser.add_argument('--filename', type=str, 
                       help='Custom filename for exported data (without extension)')
    
    args = parser.parse_args()
    
    # Check for required environment variables
    if not os.getenv('REDDIT_CLIENT_ID') or not os.getenv('REDDIT_CLIENT_SECRET'):
        print("❌ Error: Reddit API credentials not found!")
        print("Please set the following environment variables:")
        print("  - REDDIT_CLIENT_ID")
        print("  - REDDIT_CLIENT_SECRET")
        print("  - REDDIT_USER_AGENT (optional)")
        sys.exit(1)
    
    app = EarthwormApp()
    
    # Run demo if requested
    if args.demo:
        app.run_demo(stealth_mode=args.stealth)
        return
    
    # Initialize Reddit adapter
    if not app.initialize_reddit(stealth_mode=args.stealth):
        logger.error("Failed to initialize. Exiting.")
        sys.exit(1)
    
    try:
        # Handle specific operations
        data = None
        
        if args.subreddit:
            data = app.collect_subreddit_data(args.subreddit, limit=args.limit, include_comments=args.comments)
            print(f"Collected {data['total_posts']} posts from r/{args.subreddit}")
            if args.comments:
                print(f"Collected {data['total_comments']} comments")
        
        elif args.search:
            data = app.search_reddit(args.search, limit=args.limit, include_comments=args.comments)
            print(f"Found {data['total_results']} results for '{args.search}'")
            if args.comments:
                print(f"Collected {data['total_comments']} comments")
            
            # Display results
            if not args.export and not args.analyze:  # Only show if not exporting/analyzing
                print("=" * 60)
                for i, post in enumerate(data['posts'][:5], 1):  # Show first 5
                    print(f"{i}. Title: {post['title'][:80]}...")
                    print(f"   Subreddit: r/{post['subreddit']}")
                    print(f"   Score: {post['score']} | Comments: {post['num_comments']}")
                    print(f"   Author: u/{post['author']}")
                    print(f"   URL: {post['url']}")
                    
                    # Show some comments if collected
                    if args.comments and data['comments']:
                        post_comments = [c for c in data['comments'] if c.get('parent_id') == f"t3_{post['id']}"][:3]
                        if post_comments:
                            print(f"   💬 Sample comments:")
                            for j, comment in enumerate(post_comments, 1):
                                comment_text = comment.get('body', '')[:100].replace('\n', ' ')
                                print(f"      {j}. {comment_text}...")
                    
                    print("-" * 60)
        
        elif args.user:
            data = app.get_user_activity(args.user)
            print(f"User u/{args.user}: {data['total_posts']} posts, {data['total_comments']} comments")
        
        else:
            print("No specific operation requested. Use --demo to see features.")
            app.show_rate_limit_status()
            return
        
        # Perform analysis if requested
        if data and args.analyze:
            print("\n🔬 Performing statistical analysis...")
            analysis = app.analyze_data(data)
            app.display_analysis_summary(analysis)
            
            # Export analysis
            if args.export:
                analysis_filename = app.export_data(analysis, format=args.export, 
                                                  filename=f"{args.filename}_analysis" if args.filename else None)
                print(f"\n📊 Analysis exported to: {analysis_filename}")
        
        # Export data if requested
        if data and args.export:
            filename = app.export_data(data, format=args.export, filename=args.filename)
            print(f"\n💾 Data exported to: {filename}")
            
            if args.export == 'csv':
                print(f"   📄 Posts: {filename.replace('.csv', '_posts.csv')}")
                if data.get('total_comments', 0) > 0:
                    print(f"   💬 Comments: {filename.replace('.csv', '_comments.csv')}")
            elif args.export == 'excel':
                print(f"   📊 Multi-sheet Excel file with Posts, Comments, and Summary tabs")
            
            print(f"\n🎯 Data is now ready for research analysis!")
            print(f"   • Use pandas: pd.read_csv() or pd.read_excel()")
            print(f"   • Structured format with normalized fields")
            print(f"   • Timestamps converted to readable dates")
            print(f"   • Statistical summaries included")
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

def app():
    """Legacy function to execute the script."""
    print("🌍 Earthworm - Enhanced Social Media Data Collector")
    print("Use 'python main.py --help' for available options")
    print("Quick start: python main.py --demo")

if __name__ == "__main__":
    main()
