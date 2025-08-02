#!/usr/bin/env python3
"""
Reddit Comment Extraction Test
Comprehensive test for extracting comments from Reddit posts and users.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.adapters.reddit.reddit_community import RedditCommunity
import json
import time
from datetime import datetime

class CommentExtractor:
    """Dedicated class for testing Reddit comment extraction."""
    
    def __init__(self):
        self.scraper = RedditCommunity()
        self.scraper.authenticate()
        self.scraper.set_request_delay(1.0)  # Be respectful
        
    def print_separator(self, title: str):
        """Print formatted separator."""
        print("\n" + "💬 " + "="*55)
        print(f"   {title}")
        print("="*60)
    
    def extract_post_comments(self, post_id: str = None, limit: int = 50):
        """Extract and analyze comments from a specific post."""
        if not post_id:
            print("Please provide a Reddit post ID (from the URL)")
            print("Example: if URL is reddit.com/r/python/comments/abc123/title/")
            print("Then post_id is: abc123")
            post_id = input("Enter post ID: ").strip()
        
        self.print_separator(f"Extracting Comments from Post: {post_id}")
        
        # First get post details
        print("📄 Getting post information...")
        post_details = self.scraper.get_post_details(post_id)
        
        if post_details and 'data' in post_details and 'children' in post_details['data']:
            post_data = post_details['data']['children'][0]['data']
            print("✅ Post Found:")
            print(f"   Title: {post_data.get('title', 'No title')}")
            print(f"   Author: u/{post_data.get('author', 'unknown')}")
            print(f"   Subreddit: r/{post_data.get('subreddit', 'unknown')}")
            print(f"   Score: {post_data.get('score', 0)}")
            print(f"   Total Comments: {post_data.get('num_comments', 0)}")
        else:
            print("❌ Could not find post. Check the post ID.")
            return
        
        # Extract comments
        print(f"\n💬 Extracting up to {limit} comments...")
        start_time = time.time()
        comments = self.scraper.get_comments(post_id, limit=limit)
        end_time = time.time()
        
        if not comments:
            print("❌ No comments found or post has no comments")
            return
        
        print(f"✅ Extracted {len(comments)} comments in {end_time - start_time:.2f}s")
        
        # Analyze comments
        self._analyze_comments(comments)
        
        return comments
    
    def extract_user_comments(self, username: str = None, limit: int = 25):
        """Extract and analyze comments from a specific user."""
        if not username:
            username = input("Enter username (without u/): ").strip()
        
        self.print_separator(f"Extracting Comments from User: u/{username}")
        
        # Get user info first
        print("👤 Getting user information...")
        user_info = self.scraper.get_user_info(username)
        
        if user_info:
            print("✅ User Found:")
            print(f"   Comment Karma: {user_info.get('comment_karma', 0):,}")
            print(f"   Link Karma: {user_info.get('link_karma', 0):,}")
            print(f"   Account Age: {user_info.get('created_utc', 'Unknown')}")
        else:
            print("⚠️  Could not get user info, but proceeding with comment extraction...")
        
        # Extract user comments
        print(f"\n💬 Extracting up to {limit} recent comments...")
        start_time = time.time()
        comments_data = self.scraper.get_user_comments(username, limit=limit)
        end_time = time.time()
        
        if not comments_data or 'data' not in comments_data or 'children' not in comments_data['data']:
            print("❌ No comments found or user comments are private")
            return
        
        comments = [child['data'] for child in comments_data['data']['children']]
        print(f"✅ Extracted {len(comments)} comments in {end_time - start_time:.2f}s")
        
        # Analyze user comments
        self._analyze_user_comments(comments, username)
        
        return comments
    
    def _analyze_comments(self, comments):
        """Analyze post comments for insights."""
        print("\n📊 Comment Analysis:")
        
        # Basic stats
        total_score = sum(c.get('score', 0) for c in comments)
        avg_score = total_score / len(comments) if comments else 0
        
        # Filter out deleted/removed comments
        valid_comments = [c for c in comments if c.get('body') and c['body'] not in ['[deleted]', '[removed]']]
        
        print(f"   📈 Total Comments: {len(comments)}")
        print(f"   ✅ Valid Comments: {len(valid_comments)}")
        print(f"   🗑️  Deleted/Removed: {len(comments) - len(valid_comments)}")
        print(f"   ⭐ Average Score: {avg_score:.1f}")
        print(f"   🔥 Highest Score: {max((c.get('score', 0) for c in comments), default=0)}")
        print(f"   ❄️  Lowest Score: {min((c.get('score', 0) for c in comments), default=0)}")
        
        # Top comments
        print(f"\n🏆 Top 5 Comments by Score:")
        sorted_comments = sorted(valid_comments, key=lambda x: x.get('score', 0), reverse=True)
        
        for i, comment in enumerate(sorted_comments[:5], 1):
            author = comment.get('author', 'unknown')
            score = comment.get('score', 0)
            body = comment.get('body', 'No content')[:100].replace('\n', ' ')
            print(f"   {i}. u/{author} (Score: {score})")
            print(f"      {body}{'...' if len(comment.get('body', '')) > 100 else ''}")
        
        # Author analysis
        authors = {}
        for comment in valid_comments:
            author = comment.get('author', 'unknown')
            if author not in authors:
                authors[author] = {'count': 0, 'total_score': 0}
            authors[author]['count'] += 1
            authors[author]['total_score'] += comment.get('score', 0)
        
        print(f"\n👥 Most Active Commenters:")
        top_authors = sorted(authors.items(), key=lambda x: x[1]['count'], reverse=True)
        for i, (author, stats) in enumerate(top_authors[:5], 1):
            avg_score = stats['total_score'] / stats['count'] if stats['count'] > 0 else 0
            print(f"   {i}. u/{author}: {stats['count']} comments, avg score: {avg_score:.1f}")
    
    def _analyze_user_comments(self, comments, username):
        """Analyze user's comment history for insights."""
        print(f"\n📊 Analysis for u/{username}:")
        
        # Basic stats
        total_score = sum(c.get('score', 0) for c in comments)
        avg_score = total_score / len(comments) if comments else 0
        
        # Filter valid comments
        valid_comments = [c for c in comments if c.get('body') and c['body'] not in ['[deleted]', '[removed]']]
        
        print(f"   📈 Recent Comments: {len(comments)}")
        print(f"   ✅ Valid Comments: {len(valid_comments)}")
        print(f"   ⭐ Average Score: {avg_score:.1f}")
        print(f"   🔥 Best Comment Score: {max((c.get('score', 0) for c in comments), default=0)}")
        
        # Subreddit activity
        subreddits = {}
        for comment in valid_comments:
            subreddit = comment.get('subreddit', 'unknown')
            subreddits[subreddit] = subreddits.get(subreddit, 0) + 1
        
        print(f"\n🏠 Most Active Subreddits:")
        top_subreddits = sorted(subreddits.items(), key=lambda x: x[1], reverse=True)
        for i, (subreddit, count) in enumerate(top_subreddits[:5], 1):
            percentage = (count / len(valid_comments)) * 100
            print(f"   {i}. r/{subreddit}: {count} comments ({percentage:.1f}%)")
        
        # Recent comments
        print(f"\n💬 Recent Comments:")
        for i, comment in enumerate(valid_comments[:5], 1):
            subreddit = comment.get('subreddit', 'unknown')
            score = comment.get('score', 0)
            body = comment.get('body', 'No content')[:80].replace('\n', ' ')
            print(f"   {i}. In r/{subreddit} (Score: {score})")
            print(f"      {body}{'...' if len(comment.get('body', '')) > 80 else ''}")
    
    def demo_comment_extraction(self):
        """Run a demonstration of comment extraction capabilities."""
        self.print_separator("Comment Extraction Demo")
        
        print("🎯 This demo will show you how to extract comments from:")
        print("   1. A specific popular post")
        print("   2. A well-known Reddit user")
        print("\nStarting demo...")
        
        # Demo 1: Extract comments from a popular post
        print("\n" + "="*60)
        print("DEMO 1: Extracting comments from r/python hot post")
        print("="*60)
        
        # Get a recent post from r/python
        print("📄 Finding a recent post from r/python...")
        posts = self.scraper.get_subreddit_posts("python", sort="hot", limit=5)
        
        if posts and 'data' in posts and 'children' in posts['data']:
            # Find a post with comments
            for post in posts['data']['children']:
                post_data = post['data']
                if post_data.get('num_comments', 0) > 5:  # Posts with some comments
                    post_id = post_data['id']
                    print(f"✅ Found post: {post_data.get('title', 'No title')[:60]}...")
                    print(f"   Post ID: {post_id}")
                    print(f"   Comments: {post_data.get('num_comments', 0)}")
                    
                    # Extract comments from this post
                    self.extract_post_comments(post_id, limit=20)
                    break
        else:
            print("❌ Could not find posts for demo")
        
        # Demo 2: Extract user comments
        print("\n" + "="*60)
        print("DEMO 2: Extracting user comments from 'reddit' account")
        print("="*60)
        
        self.extract_user_comments("reddit", limit=10)
        
        print(f"\n🎉 Demo completed! You can now use the comment extraction methods:")
        print(f"   • scraper.get_comments(post_id, limit=100)")
        print(f"   • scraper.get_user_comments(username, limit=25)")
    
    def interactive_comment_extractor(self):
        """Interactive menu for comment extraction."""
        while True:
            print("\n💬 Reddit Comment Extractor")
            print("="*40)
            print("1. Extract comments from a post")
            print("2. Extract user's comment history")
            print("3. Run extraction demo")
            print("4. Change request delay")
            print("0. Exit")
            
            choice = input("\nChoose an option (0-4): ").strip()
            
            try:
                if choice == "1":
                    self.extract_post_comments()
                elif choice == "2":
                    self.extract_user_comments()
                elif choice == "3":
                    self.demo_comment_extraction()
                elif choice == "4":
                    delay = float(input("Enter delay in seconds (0.1-10): ") or "1.0")
                    self.scraper.set_request_delay(delay)
                    print(f"✅ Request delay set to {delay}s")
                elif choice == "0":
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice")
                    
            except KeyboardInterrupt:
                print("\n⚠️  Interrupted by user")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            if choice != "0":
                input("\nPress Enter to continue...")

def main():
    """Main function."""
    try:
        extractor = CommentExtractor()
        extractor.interactive_comment_extractor()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")

if __name__ == "__main__":
    main()
