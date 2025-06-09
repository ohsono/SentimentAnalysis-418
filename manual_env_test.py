#!/usr/bin/env python3

"""
Manual test that sets environment variables directly
This bypasses the .env loading issue to test if Reddit API works
"""

import os
import sys

# Set environment variables manually (bypass .env file issues)
os.environ['REDDIT_CLIENT_ID'] = 'xT7hVYft2ks-YANApfrKHw'
os.environ['REDDIT_CLIENT_SECRET'] = 'yuio5D23aeNXe0RcRQbEAk5dfs4NJA'
os.environ['REDDIT_USER_AGENT'] = 'UCLA_STATS418_Sentiment_Analysis_Academic_Project'

print("🔧 Set environment variables manually")
print(f"REDDIT_CLIENT_ID: {os.getenv('REDDIT_CLIENT_ID')}")
print(f"REDDIT_CLIENT_SECRET: {os.getenv('REDDIT_CLIENT_SECRET')}")
print(f"REDDIT_USER_AGENT: {os.getenv('REDDIT_USER_AGENT')}")

# Test Reddit connection
try:
    import praw
    print("\n✅ PRAW imported successfully")
    
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT')
    )
    
    print("✅ Reddit client created")
    
    # Test connection
    subreddit = reddit.subreddit("test")
    posts = list(subreddit.hot(limit=1))
    
    print(f"✅ Reddit API connection successful! Retrieved {len(posts)} post(s)")
    
    # Test UCLA subreddit
    ucla_subreddit = reddit.subreddit("UCLA")
    ucla_posts = list(ucla_subreddit.hot(limit=3))
    
    print(f"✅ UCLA subreddit access successful! Retrieved {len(ucla_posts)} post(s)")
    
    for i, post in enumerate(ucla_posts, 1):
        print(f"  {i}. {post.title[:60]}...")
    
    print("\n🎉 SUCCESS! Your Reddit API credentials work perfectly!")
    print("The issue is just with loading the .env file.")
    
except ImportError:
    print("❌ PRAW not installed. Install with: pip install praw")
except Exception as e:
    print(f"❌ Reddit API error: {e}")
    if "received 401 HTTP response" in str(e):
        print("💡 This suggests your Reddit API credentials might be invalid")
    elif "received 429 HTTP response" in str(e):
        print("💡 Rate limited - too many requests")
