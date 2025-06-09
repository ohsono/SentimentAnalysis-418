#!/usr/bin/env python3

"""
Comprehensive debug script to find the exact .env loading issue
"""

import os
import sys
from pathlib import Path

def debug_everything():
    """Comprehensive debugging"""
    print("🔍 COMPREHENSIVE ENVIRONMENT DEBUG")
    print("=" * 60)
    
    # 1. Current environment
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {__file__}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    # 2. Check if python-dotenv is installed
    print(f"\n📦 Checking python-dotenv installation:")
    try:
        import dotenv
        print(f"✅ python-dotenv is installed: {dotenv.__file__}")
    except ImportError:
        print(f"❌ python-dotenv is NOT installed")
        print(f"💡 Install with: pip install python-dotenv")
        return
    
    # 3. Find all .env files
    print(f"\n📁 Searching for .env files:")
    possible_locations = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        '/Users/hobangu/Project/UCLA-MASDS/SentimentAnalysis-418',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'),
    ]
    
    env_files_found = []
    for location in possible_locations:
        env_path = os.path.join(location, '.env')
        abs_path = os.path.abspath(env_path)
        if os.path.exists(abs_path):
            env_files_found.append(abs_path)
            print(f"✅ Found: {abs_path}")
        else:
            print(f"❌ Not found: {abs_path}")
    
    if not env_files_found:
        print(f"\n❌ No .env files found!")
        return
    
    # 4. Check the contents of found .env files
    for env_file in env_files_found:
        print(f"\n📄 Contents of {env_file}:")
        try:
            with open(env_file, 'r') as f:
                for i, line in enumerate(f, 1):
                    if 'REDDIT' in line.upper():
                        print(f"  Line {i}: {line.strip()}")
        except Exception as e:
            print(f"❌ Error reading {env_file}: {e}")
    
    # 5. Test loading each .env file
    from dotenv import load_dotenv
    
    for env_file in env_files_found:
        print(f"\n🔧 Testing load_dotenv with: {env_file}")
        
        # Clear existing environment variables
        for key in ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT']:
            if key in os.environ:
                del os.environ[key]
        
        # Try loading
        result = load_dotenv(env_file, override=True)
        print(f"  load_dotenv() returned: {result}")
        
        # Check what we got
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET") 
        user_agent = os.getenv("REDDIT_USER_AGENT")
        
        print(f"  REDDIT_CLIENT_ID: {repr(client_id)}")
        print(f"  REDDIT_CLIENT_SECRET: {repr(client_secret)}")
        print(f"  REDDIT_USER_AGENT: {repr(user_agent)}")
        
        if client_id and client_secret:
            print(f"  ✅ SUCCESS with this file!")
            break
        else:
            print(f"  ❌ Still missing credentials")
    
    # 6. Manual parsing test
    print(f"\n🔧 Manual parsing test:")
    if env_files_found:
        env_file = env_files_found[0]  # Use the first one found
        print(f"Parsing: {env_file}")
        
        try:
            manual_vars = {}
            with open(env_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    original_line = line
                    line = line.strip()
                    
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        
                        manual_vars[key] = value
                        
                        if 'REDDIT' in key:
                            print(f"  Line {line_num}: {original_line.strip()}")
                            print(f"    Parsed as: {key} = {repr(value)}")
            
            print(f"\nManual parsing results:")
            for key in ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT']:
                if key in manual_vars:
                    print(f"  {key}: {repr(manual_vars[key])}")
                    # Set in environment for testing
                    os.environ[key] = manual_vars[key]
                else:
                    print(f"  {key}: ❌ Not found")
            
            # Test with manual values
            print(f"\n🧪 Testing with manually parsed values:")
            client_id = os.getenv("REDDIT_CLIENT_ID")
            client_secret = os.getenv("REDDIT_CLIENT_SECRET")
            user_agent = os.getenv("REDDIT_USER_AGENT")
            
            print(f"  REDDIT_CLIENT_ID: {repr(client_id)}")
            print(f"  REDDIT_CLIENT_SECRET: {repr(client_secret)}")
            print(f"  REDDIT_USER_AGENT: {repr(user_agent)}")
            
            if client_id and client_secret:
                print(f"  ✅ Manual parsing worked!")
                
                # Test Reddit connection
                try:
                    import praw
                    reddit = praw.Reddit(
                        client_id=client_id,
                        client_secret=client_secret,
                        user_agent=user_agent or "Test Bot"
                    )
                    
                    # Test with a simple request
                    subreddit = reddit.subreddit("test")
                    posts = list(subreddit.hot(limit=1))
                    print(f"  ✅ Reddit API test successful! Got {len(posts)} post(s)")
                    
                except Exception as e:
                    print(f"  ❌ Reddit API test failed: {e}")
            
        except Exception as e:
            print(f"❌ Manual parsing failed: {e}")

if __name__ == "__main__":
    debug_everything()
