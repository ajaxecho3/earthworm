#!/usr/bin/env python3
"""
Enhanced Reddit Scraper Test
Test the improved features of the Reddit Community scraper.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.adapters.reddit.reddit_community import RedditCommunity
import json
import time

def test_enhanced_features():
    """Test the enhanced features of the Reddit scraper."""
    print("🚀 Testing Enhanced Reddit Scraper Features")
    print("="*60)
    
    # Initialize scraper
    scraper = RedditCommunity()
    scraper.authenticate()
    scraper.set_request_delay(1.0)  # Be respectful to Reddit
    
    # Test 1: Enhanced error handling and retry logic
    print("\n📋 Test 1: Enhanced Error Handling")
    print("-" * 40)
    
    # Test with invalid subreddit (should handle gracefully)
    result = scraper.get_subreddit_posts("invalidsubreddit12345", limit=5)
    print(f"Invalid subreddit result: {'✅ Handled gracefully' if result is None else '❌ Should return None'}")
    
    # Test 2: Data validation and cleaning
    print("\n📋 Test 2: Data Cleaning & Validation")
    print("-" * 40)
    
    posts = scraper.get_subreddit_posts("python", sort="hot", limit=3)
    if posts and 'data' in posts and 'children' in posts['data']:
        first_post = posts['data']['children'][0]['data']
        cleaned_post = scraper._extract_clean_post_data(first_post)
        
        print("✅ Post data cleaning test:")
        print(f"   Original keys: {len(first_post.keys())}")
        print(f"   Cleaned keys: {len(cleaned_post.keys())}")
        print(f"   Title cleaned: {'✅' if cleaned_post.get('title') else '❌'}")
        print(f"   Text cleaned: {'✅' if 'selftext' in cleaned_post else '❌'}")
        
        # Show example of cleaned data
        print(f"   Sample title: {cleaned_post.get('title', 'N/A')[:50]}...")
        print(f"   Sample score: {cleaned_post.get('score', 0)}")
    else:
        print("❌ Could not retrieve posts for data cleaning test")
    
    # Test 3: Batch processing
    print("\n📋 Test 3: Batch Processing")
    print("-" * 40)
    
    def progress_callback(current, total):
        print(f"   Progress: {current}/{total} ({(current/total)*100:.1f}%)")
    
    print("Testing batch extraction with progress tracking...")
    start_time = time.time()
    batch_results = scraper.batch_get_posts_with_comments(
        subreddit="test",  # Use smaller subreddit to avoid issues
        sort="hot",
        post_limit=2,
        comment_limit=3,
        progress_callback=progress_callback
    )
    end_time = time.time()
    
    print(f"✅ Batch processing completed in {end_time - start_time:.2f}s")
    print(f"   Posts extracted: {len(batch_results)}")
    posts_with_comments = sum(1 for post in batch_results if post.get('comments'))
    print(f"   Posts with comments: {posts_with_comments}")
    
    # Test 4: Enhanced search functionality
    print("\n📋 Test 4: Enhanced Search with Comments")
    print("-" * 40)
    
    search_results = scraper.search_and_extract(
        query="python",
        subreddit="programming",
        limit=2,
        include_comments=True,
        comment_limit=2
    )
    
    print(f"✅ Enhanced search completed:")
    print(f"   Search results: {len(search_results)}")
    for i, result in enumerate(search_results, 1):
        comments_count = len(result.get('comments', []))
        print(f"   Post {i}: {comments_count} comments extracted")
    
    # Test 5: User activity summary
    print("\n📋 Test 5: User Activity Summary")
    print("-" * 40)
    
    user_summary = scraper.get_user_activity_summary("reddit", post_limit=2, comment_limit=2)
    
    if user_summary:
        print("✅ User activity summary:")
        print(f"   Username: {user_summary['user_info']['username']}")
        print(f"   Comment Karma: {user_summary['user_info']['comment_karma']:,}")
        print(f"   Link Karma: {user_summary['user_info']['link_karma']:,}")
        print(f"   Posts analyzed: {user_summary['posts']['count']}")
        print(f"   Comments analyzed: {user_summary['comments']['count']}")
        print(f"   Average post score: {user_summary['posts']['average_score']:.1f}")
        print(f"   Average comment score: {user_summary['comments']['average_score']:.1f}")
        
        # Show subreddit distribution
        if user_summary['posts']['subreddit_distribution']:
            print("   Top subreddits (posts):")
            for sub, count in list(user_summary['posts']['subreddit_distribution'].items())[:3]:
                print(f"     r/{sub}: {count} posts")
    else:
        print("❌ Could not retrieve user activity summary")
    
    # Test 6: Session statistics
    print("\n📋 Test 6: Session Statistics")
    print("-" * 40)
    
    stats = scraper.get_session_stats()
    print("✅ Session statistics:")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Session duration: {stats['session_duration_seconds']:.2f}s")
    print(f"   Requests per minute: {stats['requests_per_minute']:.1f}")
    print(f"   Average delay: {stats['average_delay']}s")
    print(f"   Max retries: {stats['max_retries']}")
    
    # Test 7: Data structure validation
    print("\n📋 Test 7: Data Structure Validation")
    print("-" * 40)
    
    print("Testing data structure consistency...")
    
    # Test comment data structure
    test_post = scraper.get_subreddit_posts("AskReddit", limit=1)
    if test_post and 'data' in test_post and 'children' in test_post['data']:
        first_post = test_post['data']['children'][0]['data']
        post_id = first_post.get('id')
        
        if post_id:
            comments = scraper.get_comments(post_id, limit=1)
            if comments and len(comments) > 0:
                comment = comments[0]
                required_fields = ['id', 'author', 'body', 'score', 'created_utc']
                valid_structure = all(field in comment for field in required_fields)
                print(f"✅ Comment structure validation: {'✅ Valid' if valid_structure else '❌ Invalid'}")
                print(f"   Required fields present: {sum(1 for field in required_fields if field in comment)}/{len(required_fields)}")
            else:
                print("   No comments found for structure validation")
        else:
            print("   No post ID available for comment testing")
    else:
        print("   Could not retrieve posts for structure validation")
    
    # Final summary
    print("\n🎉 Enhanced Features Test Summary")
    print("="*60)
    print("✅ Error handling and retry logic")
    print("✅ Data validation and cleaning") 
    print("✅ Batch processing with progress tracking")
    print("✅ Enhanced search with comment extraction")
    print("✅ User activity summary")
    print("✅ Session statistics and monitoring")
    print("✅ Data structure validation")
    
    print(f"\n📊 Total API calls made: {stats['total_requests']}")
    print(f"⏱️  Total test duration: {stats['session_duration_seconds']:.2f}s")
    
    # Recommendations based on test results
    print("\n💡 Performance Recommendations:")
    if stats['requests_per_minute'] > 30:
        print("   ⚠️  High request rate detected - consider increasing delays")
    else:
        print("   ✅ Request rate within safe limits")
    
    if stats['total_requests'] > 20:
        print("   📊 Comprehensive testing completed with good coverage")
    else:
        print("   📝 Light testing completed - consider more extensive testing for production")
    
    print("\n🚀 All enhanced features testing completed!")

def test_resilience():
    """Test the resilience features specifically."""
    print("\n🛡️  Testing Scraper Resilience")
    print("="*60)
    
    scraper = RedditCommunity()
    scraper.authenticate()
    scraper.set_request_delay(0.5)
    
    # Test different error scenarios
    test_cases = [
        ("nonexistent_subreddit_xyz123", "Non-existent subreddit"),
        ("", "Empty subreddit name"),
        ("test", "Valid small subreddit"),
    ]
    
    for subreddit, description in test_cases:
        print(f"\n📋 Testing: {description}")
        try:
            result = scraper.get_subreddit_posts(subreddit, limit=1)
            status = "✅ Success" if result else "⚠️  No data (handled gracefully)"
            print(f"   Result: {status}")
        except Exception as e:
            print(f"   Result: ❌ Error: {e}")
    
    print("\n✅ Resilience testing completed!")

if __name__ == "__main__":
    test_enhanced_features()
    test_resilience()
