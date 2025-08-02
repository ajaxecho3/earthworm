#!/usr/bin/env python3
"""
Dynamic Reddit Scraper Test
Interactive test script that allows you to test different Reddit scraping scenarios.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.adapters.reddit.reddit_community import RedditCommunity
import json
import time
from typing import Optional, Dict, Any

class DynamicRedditTester:
    """Interactive tester for Reddit scraper functionality."""
    
    def __init__(self):
        self.scraper = RedditCommunity()
        self.scraper.authenticate()  # Always succeeds for web scraping
        self.test_results = {}
        
    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "🚀 " + "="*55)
        print(f"   {title}")
        print("="*60)
    
    def print_json_pretty(self, data: Any, max_depth: int = 3, current_depth: int = 0):
        """Print JSON data in a readable format with depth control."""
        if current_depth >= max_depth:
            print("   [... truncated for readability ...]")
            return
            
        if isinstance(data, dict):
            for key, value in list(data.items())[:10]:  # Limit to first 10 items
                if isinstance(value, (dict, list)) and current_depth < max_depth - 1:
                    print(f"   {'  ' * current_depth}{key}:")
                    self.print_json_pretty(value, max_depth, current_depth + 1)
                else:
                    if isinstance(value, str) and len(value) > 80:
                        value = value[:80] + "..."
                    print(f"   {'  ' * current_depth}{key}: {value}")
        elif isinstance(data, list):
            print(f"   {'  ' * current_depth}[List with {len(data)} items]")
            for i, item in enumerate(data[:3]):  # Show first 3 items
                print(f"   {'  ' * current_depth}Item {i+1}:")
                self.print_json_pretty(item, max_depth, current_depth + 1)
            if len(data) > 3:
                print(f"   {'  ' * current_depth}... and {len(data) - 3} more items")
    
    def test_subreddit_posts(self, subreddit: str = None, sort: str = None, limit: int = None, extract_comments: bool = None):
        """Test getting posts from a subreddit with optional comment extraction."""
        subreddit = subreddit or input("Enter subreddit name (without r/): ").strip()
        sort = sort or input("Enter sort method (hot/new/top/rising) [hot]: ").strip() or "hot"
        limit = limit or int(input("Enter limit (1-100) [10]: ").strip() or "10")
        
        if extract_comments is None:
            extract_comments_input = input("Extract comments from posts? (y/n) [n]: ").strip().lower()
            extract_comments = extract_comments_input in ['y', 'yes', '1', 'true']
        
        self.print_header(f"Testing r/{subreddit} - {sort} posts (limit: {limit})")
        if extract_comments:
            print("🔄 Comment extraction enabled - this will take longer...")
        
        try:
            start_time = time.time()
            result = self.scraper.get_subreddit_posts(subreddit, sort=sort, limit=limit)
            end_time = time.time()
            
            if result and 'data' in result and 'children' in result['data']:
                posts = result['data']['children']
                print(f"✅ Success! Retrieved {len(posts)} posts in {end_time - start_time:.2f}s")
                
                # Track comment extraction stats
                total_comments_extracted = 0
                posts_with_comments = 0
                
                for i, post in enumerate(posts[:3], 1):
                    post_data = post['data']
                    post_id = post_data.get('id', '')
                    num_comments = post_data.get('num_comments', 0)
                    
                    print(f"\n📝 Post {i}:")
                    print(f"   Title: {post_data.get('title', 'No title')[:80]}...")
                    print(f"   Author: u/{post_data.get('author', 'unknown')}")
                    print(f"   Score: {post_data.get('score', 0)} | Comments: {num_comments}")
                    print(f"   URL: {post_data.get('url', 'No URL')[:60]}...")
                    
                    # Extract comments if requested and post has comments
                    if extract_comments and num_comments > 0 and post_id:
                        print(f"   💬 Extracting comments from post {post_id}...")
                        try:
                            comment_start = time.time()
                            comments = self.scraper.get_comments(post_id, limit=10)  # Limit to 10 comments per post
                            comment_end = time.time()
                            
                            if comments:
                                valid_comments = [c for c in comments if c.get('body') and c['body'] not in ['[deleted]', '[removed]']]
                                total_comments_extracted += len(valid_comments)
                                posts_with_comments += 1
                                
                                print(f"   ✅ Extracted {len(valid_comments)} comments in {comment_end - comment_start:.2f}s")
                                
                                # Show top 2 comments
                                sorted_comments = sorted(valid_comments, key=lambda x: x.get('score', 0), reverse=True)
                                for j, comment in enumerate(sorted_comments[:2], 1):
                                    comment_body = comment.get('body', 'No content')[:60].replace('\n', ' ')
                                    comment_score = comment.get('score', 0)
                                    comment_author = comment.get('author', 'unknown')
                                    print(f"      {j}. u/{comment_author} (Score: {comment_score}): {comment_body}...")
                            else:
                                print(f"   ❌ No comments extracted")
                                
                        except Exception as e:
                            print(f"   ❌ Failed to extract comments: {e}")
                    elif extract_comments and num_comments == 0:
                        print(f"   📝 No comments to extract")
                
                if len(posts) > 3:
                    print(f"\n   ... and {len(posts) - 3} more posts")
                
                # Summary of comment extraction
                if extract_comments:
                    print(f"\n📊 Comment Extraction Summary:")
                    print(f"   💬 Total Comments Extracted: {total_comments_extracted}")
                    print(f"   📝 Posts with Comments: {posts_with_comments}/{min(len(posts), 3)}")
                    
                self.test_results[f"subreddit_{subreddit}_{sort}"] = True
            else:
                print("❌ Failed to retrieve posts")
                self.test_results[f"subreddit_{subreddit}_{sort}"] = False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            self.test_results[f"subreddit_{subreddit}_{sort}"] = False
    
    def test_user_analysis(self, username: str = None):
        """Test comprehensive user analysis."""
        username = username or input("Enter username (without u/): ").strip()
        
        self.print_header(f"Analyzing User: u/{username}")
        
        # Get user info
        print("📊 Getting user information...")
        user_info = self.scraper.get_user_info(username)
        
        if user_info:
            print("✅ User Info Retrieved:")
            print(f"   Account Age: {user_info.get('created_utc', 'Unknown')}")
            print(f"   Comment Karma: {user_info.get('comment_karma', 0):,}")
            print(f"   Link Karma: {user_info.get('link_karma', 0):,}")
            print(f"   Is Verified: {user_info.get('verified', False)}")
            print(f"   Has Verified Email: {user_info.get('has_verified_email', False)}")
        else:
            print("❌ Could not retrieve user info")
            return
        
        # Get user posts
        print("\n📝 Getting recent posts...")
        user_posts = self.scraper.get_user_posts(username, limit=5)
        
        if user_posts and 'data' in user_posts and 'children' in user_posts['data']:
            posts = user_posts['data']['children']
            print(f"✅ Found {len(posts)} recent posts:")
            
            for i, post in enumerate(posts, 1):
                post_data = post['data']
                print(f"   {i}. {post_data.get('title', 'No title')[:60]}...")
                print(f"      Subreddit: r/{post_data.get('subreddit', 'unknown')} | Score: {post_data.get('score', 0)}")
        else:
            print("❌ No posts found or user posts are private")
        
        # Get user comments
        print("\n💬 Getting recent comments...")
        user_comments = self.scraper.get_user_comments(username, limit=5)
        
        if user_comments and 'data' in user_comments and 'children' in user_comments['data']:
            comments = user_comments['data']['children']
            print(f"✅ Found {len(comments)} recent comments:")
            
            for i, comment in enumerate(comments, 1):
                comment_data = comment['data']
                body = comment_data.get('body', 'No content')[:80]
                print(f"   {i}. {body}...")
                print(f"      In: r/{comment_data.get('subreddit', 'unknown')} | Score: {comment_data.get('score', 0)}")
        else:
            print("❌ No comments found or user comments are private")
    
    def test_search_functionality(self, query: str = None, subreddit: str = None):
        """Test search functionality."""
        query = query or input("Enter search query: ").strip()
        subreddit = subreddit or input("Enter subreddit to search in (optional, press Enter for all): ").strip() or None
        
        search_scope = f"r/{subreddit}" if subreddit else "All of Reddit"
        self.print_header(f"Searching '{query}' in {search_scope}")
        
        try:
            start_time = time.time()
            results = self.scraper.search_posts(query, subreddit=subreddit, limit=10)
            end_time = time.time()
            
            if results and 'data' in results and 'children' in results['data']:
                posts = results['data']['children']
                print(f"✅ Found {len(posts)} results in {end_time - start_time:.2f}s")
                
                for i, post in enumerate(posts[:5], 1):
                    post_data = post['data']
                    print(f"\n🔍 Result {i}:")
                    print(f"   Title: {post_data.get('title', 'No title')[:80]}...")
                    print(f"   Subreddit: r/{post_data.get('subreddit', 'unknown')}")
                    print(f"   Score: {post_data.get('score', 0)} | Comments: {post_data.get('num_comments', 0)}")
                    
                if len(posts) > 5:
                    print(f"\n   ... and {len(posts) - 5} more results")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    def test_post_deep_dive(self, post_id: str = None):
        """Test detailed post analysis with comments."""
        post_id = post_id or input("Enter Reddit post ID (from URL): ").strip()
        
        self.print_header(f"Deep Dive: Post {post_id}")
        
        # Get post details
        print("📄 Getting post details...")
        post_details = self.scraper.get_post_details(post_id)
        
        if post_details and 'data' in post_details and 'children' in post_details['data']:
            post_data = post_details['data']['children'][0]['data']
            print("✅ Post Details:")
            print(f"   Title: {post_data.get('title', 'No title')}")
            print(f"   Author: u/{post_data.get('author', 'unknown')}")
            print(f"   Subreddit: r/{post_data.get('subreddit', 'unknown')}")
            print(f"   Score: {post_data.get('score', 0)} ({post_data.get('upvote_ratio', 0)*100:.1f}% upvoted)")
            print(f"   Comments: {post_data.get('num_comments', 0)}")
            print(f"   Created: {post_data.get('created_utc', 'Unknown')}")
            
            if post_data.get('selftext'):
                text = post_data['selftext'][:200]
                print(f"   Content: {text}{'...' if len(post_data['selftext']) > 200 else ''}")
        else:
            print("❌ Could not retrieve post details")
            return
        
        # Get comments
        print("\n💬 Getting top comments...")
        comments = self.scraper.get_comments(post_id, limit=10)
        
        if comments:
            print(f"✅ Retrieved {len(comments)} comments:")
            
            for i, comment in enumerate(comments[:5], 1):
                if comment.get('body') and comment['body'] != '[deleted]':
                    print(f"\n   Comment {i} by u/{comment.get('author', 'unknown')}:")
                    print(f"   Score: {comment.get('score', 0)}")
                    body = comment.get('body', 'No content')[:150]
                    print(f"   {body}{'...' if len(comment.get('body', '')) > 150 else ''}")
        else:
            print("❌ No comments found")
    
    def comprehensive_subreddit_extraction(self):
        """Extract comprehensive data from a subreddit including all comments."""
        subreddit = input("Enter subreddit name for comprehensive extraction: ").strip()
        sort = input("Enter sort method (hot/new/top/rising) [hot]: ").strip() or "hot"
        post_limit = int(input("Enter number of posts to analyze (1-50) [10]: ").strip() or "10")
        comment_limit = int(input("Enter max comments per post (1-100) [20]: ").strip() or "20")
        
        self.print_header(f"Comprehensive Data Extraction: r/{subreddit}")
        print(f"📊 Configuration:")
        print(f"   🏠 Subreddit: r/{subreddit}")
        print(f"   📈 Sort: {sort}")
        print(f"   📝 Posts: {post_limit}")
        print(f"   💬 Comments per post: {comment_limit}")
        print(f"   ⏱️  Estimated time: {post_limit * 2}s (with delays)")
        
        confirm = input("\nProceed with extraction? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '1']:
            print("❌ Extraction cancelled")
            return
        
        try:
            # Extract posts
            print(f"\n🔄 Step 1: Extracting posts from r/{subreddit}...")
            start_time = time.time()
            result = self.scraper.get_subreddit_posts(subreddit, sort=sort, limit=post_limit)
            
            if not result or 'data' not in result or 'children' not in result['data']:
                print("❌ Failed to retrieve posts")
                return
            
            posts = result['data']['children']
            print(f"✅ Retrieved {len(posts)} posts")
            
            # Extract comments for each post
            print(f"\n🔄 Step 2: Extracting comments from posts...")
            total_comments = 0
            successful_extractions = 0
            failed_extractions = 0
            
            extracted_data = {
                'subreddit': subreddit,
                'extraction_time': time.time(),
                'posts': []
            }
            
            for i, post in enumerate(posts, 1):
                post_data = post['data']
                post_id = post_data.get('id', '')
                num_comments = post_data.get('num_comments', 0)
                
                print(f"\n📝 Processing Post {i}/{len(posts)}: {post_data.get('title', 'No title')[:50]}...")
                print(f"   ID: {post_id} | Comments: {num_comments}")
                
                post_info = {
                    'id': post_id,
                    'title': post_data.get('title', ''),
                    'author': post_data.get('author', ''),
                    'score': post_data.get('score', 0),
                    'num_comments': num_comments,
                    'created_utc': post_data.get('created_utc', 0),
                    'url': post_data.get('url', ''),
                    'selftext': post_data.get('selftext', ''),
                    'comments': []
                }
                
                if num_comments > 0 and post_id:
                    try:
                        print(f"   💬 Extracting up to {comment_limit} comments...")
                        comments = self.scraper.get_comments(post_id, limit=comment_limit)
                        
                        if comments:
                            valid_comments = [c for c in comments if c.get('body') and c['body'] not in ['[deleted]', '[removed]']]
                            post_info['comments'] = valid_comments
                            total_comments += len(valid_comments)
                            successful_extractions += 1
                            print(f"   ✅ Extracted {len(valid_comments)} valid comments")
                        else:
                            failed_extractions += 1
                            print(f"   ❌ No comments extracted")
                            
                    except Exception as e:
                        failed_extractions += 1
                        print(f"   ❌ Failed to extract comments: {e}")
                else:
                    print(f"   📝 No comments to extract")
                
                extracted_data['posts'].append(post_info)
                
                # Progress indicator
                progress = (i / len(posts)) * 100
                print(f"   📊 Progress: {progress:.1f}% complete")
            
            end_time = time.time()
            
            # Final summary
            self.print_header("Extraction Complete - Summary")
            print(f"✅ Extraction completed in {end_time - start_time:.2f}s")
            print(f"📊 Final Statistics:")
            print(f"   🏠 Subreddit: r/{subreddit}")
            print(f"   📝 Posts Processed: {len(posts)}")
            print(f"   💬 Total Comments Extracted: {total_comments}")
            print(f"   ✅ Successful Comment Extractions: {successful_extractions}")
            print(f"   ❌ Failed Comment Extractions: {failed_extractions}")
            print(f"   📈 Average Comments per Post: {total_comments / len(posts) if posts else 0:.1f}")
            
            # Ask if user wants to save data
            save_data = input(f"\nSave extracted data to JSON file? (y/n): ").strip().lower()
            if save_data in ['y', 'yes', '1']:
                filename = f"reddit_data_{subreddit}_{sort}_{int(time.time())}.json"
                try:
                    import json
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
                    print(f"✅ Data saved to {filename}")
                except Exception as e:
                    print(f"❌ Failed to save data: {e}")
            
            return extracted_data
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return None
    def run_interactive_menu(self):
        """Run the interactive test menu."""
        print("🚀 Dynamic Reddit Scraper Tester")
        print("="*60)
        
        while True:
            print("\n🔧 Choose a test:")
            print("1. Test Subreddit Posts (with optional comments)")
            print("2. Analyze User Profile")
            print("3. Search Posts")
            print("4. Deep Dive into Post")
            print("5. Run Quick Demo")
            print("6. 🆕 Comprehensive Subreddit Extraction")
            print("7. Change Request Delay")
            print("8. Show Test Results Summary")
            print("0. Exit")
            
            choice = input("\nEnter your choice (0-8): ").strip()
            
            try:
                if choice == "1":
                    self.test_subreddit_posts()
                elif choice == "2":
                    self.test_user_analysis()
                elif choice == "3":
                    self.test_search_functionality()
                elif choice == "4":
                    self.test_post_deep_dive()
                elif choice == "5":
                    self.run_quick_demo()
                elif choice == "6":
                    self.comprehensive_subreddit_extraction()
                elif choice == "7":
                    delay = float(input("Enter delay in seconds (0.1-10): ") or "1.0")
                    self.scraper.set_request_delay(delay)
                    print(f"✅ Request delay set to {delay}s")
                elif choice == "8":
                    self.show_test_summary()
                elif choice == "0":
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Test interrupted by user")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                
            input("\nPress Enter to continue...")
    
    def run_quick_demo(self):
        """Run a quick demo with predefined tests."""
        self.print_header("Quick Demo - Testing Popular Subreddits with Comments")
        
        print("🎯 This demo will test subreddit scraping WITH comment extraction")
        print("   This will take longer but shows the full data collection capability")
        
        demo_tests = [
            ("python", "hot", 3, True),      # Extract comments
            ("MachineLearning", "top", 2, True),  # Extract comments  
            ("programming", "new", 2, False)  # No comments for speed
        ]
        
        for subreddit, sort, limit, extract_comments in demo_tests:
            print(f"\n🔄 Testing r/{subreddit} {'with' if extract_comments else 'without'} comments...")
            self.test_subreddit_posts(subreddit, sort, limit, extract_comments)
            time.sleep(1)  # Brief pause between tests
        
        print("\n🔍 Demo search test...")
        self.test_search_functionality("artificial intelligence", "MachineLearning")
    
    def show_test_summary(self):
        """Show summary of all tests run."""
        self.print_header("Test Results Summary")
        
        if not self.test_results:
            print("❌ No tests have been run yet")
            return
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        print(f"📊 Tests Run: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 Individual Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")

def main():
    """Main function to run the dynamic tester."""
    try:
        tester = DynamicRedditTester()
        tester.run_interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"❌ Failed to initialize tester: {e}")

if __name__ == "__main__":
    main()
