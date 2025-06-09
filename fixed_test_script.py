#!/usr/bin/env python3

"""
Fixed test script with absolute path to .env file
"""

import os
import sys

# Use absolute path to .env file
ENV_PATH = "/Users/hobangu/Project/UCLA-MASDS/SentimentAnalysis-418/.env"

print(f"🔍 Looking for .env file at: {ENV_PATH}")
print(f"File exists: {os.path.exists(ENV_PATH)}")

# Test python-dotenv installation
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv is installed")
except ImportError:
    print("❌ python-dotenv not installed")
    print("💡 Install with: pip install python-dotenv")
    sys.exit(1)

# Load .env file with absolute path
result = load_dotenv(ENV_PATH, override=True)
print(f"load_dotenv() result: {result}")

# Check what we got
client_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")
user_agent = os.getenv("REDDIT_USER_AGENT")

print(f"\n📊 Environment variables:")
print(f"REDDIT_CLIENT_ID: {repr(client_id)}")
print(f"REDDIT_CLIENT_SECRET: {repr(client_secret)}")
print(f"REDDIT_USER_AGENT: {repr(user_agent)}")

if client_id and client_secret:
    print("\n✅ Credentials loaded successfully!")
    
    # Test Reddit API
    try:
        import praw
        
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Test connection
        subreddit = reddit.subreddit("test")
        posts = list(subreddit.hot(limit=1))
        
        print(f"✅ Reddit API test successful!")
        
    except Exception as e:
        print(f"❌ Reddit API test failed: {e}")
else:
    print("\n❌ Credentials still not loaded")
    
    # Try manual parsing
    print("\n🔧 Trying manual parsing...")
    try:
        with open(ENV_PATH, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    if 'REDDIT' in key:
                        print(f"Found: {key} = {value}")
    except Exception as e:
        print(f"❌ Manual parsing failed: {e}")
