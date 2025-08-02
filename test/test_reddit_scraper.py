#!/usr/bin/env python3
"""
Test script for Reddit Community scraper
This script tests all the methods of the RedditCommunity class.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.adapters.reddit.reddit_community import RedditCommunity
import json
import time

def print_separator(title: str):
    """Print a nice separator for test sections."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_result(result, max_items=3):
    """Print test results in a readable format."""
    if result is None:
        print("❌ Result: None")
        return
    
    if isinstance(result, dict):
        if 'data' in result and 'children' in result['data']:
            # This is a Reddit listing
            children = result['data']['children']
            print(f"✅ Found {len(children)} items")
            for i, child in enumerate(children[:max_items]):
                if 'data' in child:
                    title = child['data'].get('title', child['data'].get('body', 'No title'))[:80]
                    print(f"   {i+1}. {title}...")
            if len(children) > max_items:
                print(f"   ... and {len(children) - max_items} more items")
        else:
            # Single item result
            print("✅ Single item result:")
            for key, value in list(result.items())[:5]:
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"   {key}: {value}")
    elif isinstance(result, list):
        print(f"✅ Found {len(result)} items")
        for i, item in enumerate(result[:max_items]):
            if isinstance(item, dict):
                title = item.get('body', item.get('title', str(item)))[:80]
                print(f"   {i+1}. {title}...")
    else:
        print(f"✅ Result: {result}")

def main():
    """Test the Reddit scraper functionality."""
    print_separator("🕷️  REDDIT COMMUNITY SCRAPER TEST")
    
    # Initialize the scraper
    print("Initializing Reddit scraper...")
    scraper = RedditCommunity()
    
    # Set a reasonable delay for testing
    scraper.set_request_delay(0.5)  # 0.5 seconds between requests
    
    # Test 1: Authentication (should always work for scraping)
    print_separator("1. Testing Authentication")
    auth_result = scraper.authenticate()
    print(f"Authentication: {'✅ Success' if auth_result else '❌ Failed'}")
    
    # Test 2: Get subreddit posts
    print_separator("2. Testing Subreddit Posts")
    print("Getting posts from r/python...")
    posts = scraper.get_subreddit_posts("python", sort="hot", limit=5)
    print_result(posts)
    
    # Test 3: Get subreddit info
    print_separator("3. Testing Subreddit Info")
    print("Getting info for r/python...")
    subreddit_info = scraper.get_subreddit_info("python")
    print_result(subreddit_info)
    
    # Test 4: Search posts
    print_separator("4. Testing Search")
    print("Searching for 'machine learning' in r/python...")
    search_results = scraper.search_posts("machine learning", subreddit="python", limit=3)
    print_result(search_results)
    
    # Test 5: Get user info (using a well-known Reddit user)
    print_separator("5. Testing User Info")
    print("Getting user info for 'reddit'...")
    user_info = scraper.get_user_info("reddit")
    print_result(user_info)
    
    # Test 6: Get user posts
    print_separator("6. Testing User Posts")
    print("Getting posts from user 'reddit'...")
    user_posts = scraper.get_user_posts("reddit", limit=3)
    print_result(user_posts)
    
    # Test 7: Get a specific post (we'll use the first post from r/python if available)
    print_separator("7. Testing Post Details")
    if posts and 'data' in posts and 'children' in posts['data'] and len(posts['data']['children']) > 0:
        first_post = posts['data']['children'][0]['data']
        post_id = first_post.get('id')
        if post_id:
            print(f"Getting details for post ID: {post_id}")
            post_details = scraper.get_post_details(post_id)
            print_result(post_details)
            
            # Test 8: Get comments for that post
            print_separator("8. Testing Comments")
            print(f"Getting comments for post ID: {post_id}")
            comments = scraper.get_comments(post_id, limit=5)
            print_result(comments)
        else:
            print("❌ Could not get post ID from subreddit posts")
    else:
        print("❌ No posts available to test post details and comments")
    
    print_separator("🎉 TEST COMPLETED")
    print("All tests have been executed!")
    print("\nNote: Some tests might fail due to:")
    print("- Rate limiting from Reddit")
    print("- Network issues")
    print("- Reddit's anti-scraping measures")
    print("- Private/deleted content")

if __name__ == "__main__":
    main()
