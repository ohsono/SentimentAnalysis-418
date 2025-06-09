#!/usr/bin/env python3

"""
Debug environment variable loading for reddit_scraper_with_db.py
"""

import os
import sys

print("🔍 DEBUGGING ENVIRONMENT LOADING")
print("=" * 50)

# 1. Check current working directory
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")

# 2. Test different ways to load .env
print("\n📁 Looking for .env file:")
env_locations = [
    ".env",
    "/Users/hobangu/Project/UCLA-MASDS/SentimentAnalysis-418/.env",
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
]

for location in env_locations:
    exists = os.path.exists(location)
    print(f"  {'✅' if exists else '❌'} {location}")

# 3. Try loading with python-dotenv
print("\n🔧 Testing dotenv loading:")
try:
    from dotenv import load_dotenv
    
    # Try loading from project root
    project_root = "/Users/hobangu/Project/UCLA-MASDS/SentimentAnalysis-418"
    env_path = os.path.join(project_root, ".env")
    
    print(f"Loading from: {env_path}")
    result = load_dotenv(env_path, override=True)
    print(f"load_dotenv() result: {result}")
    
    # Check what we got
    reddit_vars = {
        'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
        'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
        'REDDIT_USER_AGENT': os.getenv('REDDIT_USER_AGENT')
    }
    
    db_vars = {
        'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
        'POSTGRES_PORT': os.getenv('POSTGRES_PORT'),
        'POSTGRES_DB': os.getenv('POSTGRES_DB'),
        'POSTGRES_USER': os.getenv('POSTGRES_USER'),
        'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD')
    }
    
    print("\n📊 Reddit Environment Variables:")
    for key, value in reddit_vars.items():
        print(f"  {key}: {'✅ Found' if value else '❌ Missing'}")
        if value:
            print(f"    Value: {value[:10]}..." if len(value) > 10 else f"    Value: {value}")
    
    print("\n🗄️  Database Environment Variables:")
    for key, value in db_vars.items():
        print(f"  {key}: {'✅ Found' if value else '❌ Missing'}")
        if value and key != 'POSTGRES_PASSWORD':
            print(f"    Value: {value}")
        elif value and key == 'POSTGRES_PASSWORD':
            print(f"    Value: {'*' * len(value)}")

except ImportError:
    print("❌ python-dotenv not installed")
except Exception as e:
    print(f"❌ Error loading dotenv: {e}")

# 4. Manual .env file reading
print("\n📄 Manual .env file reading:")
env_file = "/Users/hobangu/Project/UCLA-MASDS/SentimentAnalysis-418/.env"
try:
    with open(env_file, 'r') as f:
        lines = f.readlines()
        print(f"Found {len(lines)} lines in .env file")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if 'REDDIT' in key or 'POSTGRES' in key:
                    print(f"  Line {line_num}: {key} = {value[:10]}..." if len(value) > 10 else f"  Line {line_num}: {key} = {value}")

except Exception as e:
    print(f"❌ Error reading .env file: {e}")

print("\n💡 Solutions:")
print("1. Make sure you're running from the project root directory")
print("2. Use absolute path to .env file")
print("3. Check that .env file has no quotes around values")
print("4. Verify file permissions")
