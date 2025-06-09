#!/usr/bin/env python3

"""
Simple test script to verify Reddit API connection
Save this as test_reddit_connection.py and run it to test your setup
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Load environment variables
try:
    from dotenv import load_dotenv
    # Use absolute path to ensure we find the .env file
    env_path = "/Users/hobangu/Project/UCLA-MASDS/SentimentAnalysis-418/.env"
    load_dotenv(env_path, override=True)
    print("✅ Environment variables loaded")
except ImportError:
    print("❌ python-dotenv not installed")
    sys.exit(1)

# Test PRAW installation
try:
    import praw
    print("✅ PRAW library installed")
except ImportError:
    print("❌ PRAW not installed")
    print("💡 Install with: pip install praw")
    sys.exit(1)

def test_reddit_credentials():
    """Test Reddit API credentials"""
    print("\n🔍 Checking Reddit API credentials...")
    
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "UCLA Sentiment Analysis Bot 1.0")
    
    print(f"Client ID: {'✅ Found' if client_id else '❌ Missing'}")
    print(f"Client Secret: {'✅ Found' if client_secret else '❌ Missing'}")
    print(f"User Agent: {user_agent}")
    
    if not client_id or not client_secret:
        print("\n❌ Missing Reddit credentials!")
        print("💡 Make sure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are set in .env file")
        return False
    
    return True

def test_reddit_connection():
    """Test actual Reddit API connection"""
    print("\n🌐 Testing Reddit API connection...")
    
    try:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "UCLA Sentiment Analysis Bot 1.0")
        
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Test connection by getting one post from a test subreddit
        subreddit = reddit.subreddit("test")
        posts = list(subreddit.hot(limit=1))
        
        print("✅ Successfully connected to Reddit API!")
        print(f"✅ Retrieved {len(posts)} test post(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Reddit API connection failed: {e}")
        return False

def test_ucla_subreddit():
    """Test accessing UCLA subreddit specifically"""
    print("\n🎓 Testing UCLA subreddit access...")
    
    try:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "UCLA Sentiment Analysis Bot 1.0")
        
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Test UCLA subreddit specifically
        subreddit = reddit.subreddit("UCLA")
        posts = list(subreddit.hot(limit=3))
        
        print(f"✅ Successfully accessed r/UCLA!")
        print(f"✅ Retrieved {len(posts)} post(s)")
        
        for i, post in enumerate(posts, 1):
            print(f"  {i}. {post.title[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ UCLA subreddit access failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Reddit API Connection Test")
    print("=" * 40)
    
    # Test 1: Check credentials
    if not test_reddit_credentials():
        sys.exit(1)
    
    # Test 2: Test basic connection
    if not test_reddit_connection():
        sys.exit(1)
    
    # Test 3: Test UCLA subreddit
    if not test_ucla_subreddit():
        sys.exit(1)
    
    print("\n🎉 All tests passed! Reddit scraper should work now.")
    print("\n💡 Next steps:")
    print("  1. Run your reddit_scraper.py script")
    print("  2. It should now connect to Reddit successfully")
    print("  3. If you still see 'mock data' warnings, check the import paths")
