#!/usr/bin/env python3

"""
Reddit Scraper Validation Script
Tests the Reddit scraping functionality specifically
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "worker"))

def test_reddit_credentials():
    """Test Reddit API credentials"""
    print("🔐 Testing Reddit API Credentials")
    print("-" * 40)
    
    try:
        from worker.config.worker_config import config
        reddit_config = config.get_reddit_config()
        
        client_id = reddit_config.get('client_id')
        client_secret = reddit_config.get('client_secret')
        user_agent = reddit_config.get('user_agent')
        
        print(f"   Client ID: {'Set' if client_id else 'NOT SET'}")
        print(f"   Client Secret: {'Set' if client_secret else 'NOT SET'}")
        print(f"   User Agent: {user_agent}")
        
        if not client_id or not client_secret:
            print("   ❌ Reddit credentials are not properly configured")
            return False, "Credentials missing"
        
        print("   ✅ Reddit credentials are configured")
        return True, "Credentials configured"
        
    except Exception as e:
        print(f"   ❌ Error checking credentials: {e}")
        return False, f"Error: {e}"

def test_reddit_connection():
    """Test actual Reddit API connection"""
    print("\n🌐 Testing Reddit API Connection")
    print("-" * 40)
    
    try:
        import praw
        from worker.config.worker_config import config
        
        reddit_config = config.get_reddit_config()
        
        # Create Reddit instance
        reddit = praw.Reddit(
            client_id=reddit_config['client_id'],
            client_secret=reddit_config['client_secret'],
            user_agent=reddit_config['user_agent']
        )
        
        # Set to read-only mode
        reddit.read_only = True
        
        print(f"   📱 User Agent: {reddit.config.user_agent}")
        print(f"   🔒 Read Only: {reddit.read_only}")
        
        # Test connection by getting Reddit version info
        print(f"   🔌 Testing connection...")
        
        # Try to access a test subreddit
        test_subreddit = reddit.subreddit('test')
        subreddit_info = {
            'name': test_subreddit.display_name,
            'subscribers': test_subreddit.subscribers,
            'description': test_subreddit.public_description[:100] + "..." if test_subreddit.public_description else "No description"
        }
        
        print(f"   ✅ Connection successful!")
        print(f"   📊 Test subreddit: r/{subreddit_info['name']}")
        print(f"   👥 Subscribers: {subreddit_info['subscribers']:,}")
        
        return True, subreddit_info
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False, str(e)

def test_reddit_scraper_import():
    """Test Reddit scraper import and basic functionality"""
    print("\n🛠️ Testing Reddit Scraper Import")
    print("-" * 40)
    
    try:
        from worker.scrapers.RedditScraper import RedditScraper
        print("   ✅ RedditScraper imported successfully")
        
        # Test basic instantiation (without actual API calls)
        test_config = {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'user_agent': 'test_user_agent',
            'subreddit': 'test',
            'post_limit': 5,
            'comment_limit': 3,
            'data_dir': str(project_root / 'worker' / 'data')
        }
        
        scraper = RedditScraper(test_config)
        print("   ✅ RedditScraper can be instantiated")
        
        return True, "Import and instantiation successful"
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False, f"Import error: {e}"
    except Exception as e:
        print(f"   ❌ Instantiation failed: {e}")
        return False, f"Instantiation error: {e}"

def test_small_scraping_operation():
    """Test a small scraping operation"""
    print("\n🕷️ Testing Small Scraping Operation")
    print("-" * 40)
    
    try:
        from worker.scrapers.RedditScraper import RedditScraper
        from worker.config.worker_config import config
        
        # Get configuration
        reddit_config = config.get_reddit_config()
        
        # Configure for small test
        scraper_config = {
            **reddit_config,
            'subreddit': 'test',  # Use test subreddit
            'post_limit': 2,      # Very small limit
            'comment_limit': 1,   # Very small limit
            'data_dir': str(project_root / 'worker' / 'data')
        }
        
        print(f"   🎯 Target: r/{scraper_config['subreddit']}")
        print(f"   📊 Limits: {scraper_config['post_limit']} posts, {scraper_config['comment_limit']} comments")
        
        # Create scraper
        scraper = RedditScraper(scraper_config)
        
        # Run scraping
        print(f"   🚀 Starting scraping operation...")
        stats = scraper.scrape_subreddit()
        
        print(f"   ✅ Scraping completed!")
        print(f"   📈 Stats:")
        print(f"      New posts processed: {stats.get('new_posts_processed', 0)}")
        print(f"      Total comments collected: {stats.get('total_comments_collected', 0)}")
        print(f"      Duplicate posts skipped: {stats.get('duplicate_posts_skipped', 0)}")
        print(f"      Errors encountered: {stats.get('errors_encountered', 0)}")
        
        return True, stats
        
    except Exception as e:
        print(f"   ❌ Scraping failed: {e}")
        return False, str(e)

def check_data_files():
    """Check if scraping created data files"""
    print("\n📁 Checking Data Files")
    print("-" * 40)
    
    data_dir = project_root / 'worker' / 'data'
    
    # Look for parquet files
    parquet_files = list(data_dir.glob("*.parquet"))
    
    if parquet_files:
        print(f"   ✅ Found {len(parquet_files)} parquet files:")
        for file in parquet_files[-5:]:  # Show last 5 files
            file_size = file.stat().st_size
            modified_time = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"      📄 {file.name} ({file_size:,} bytes, {modified_time.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print(f"   ⚠️ No parquet files found in {data_dir}")
    
    # Look for JSON files (processed posts tracking)
    json_files = list(data_dir.glob("*.json"))
    
    if json_files:
        print(f"   ✅ Found {len(json_files)} JSON files:")
        for file in json_files[-3:]:  # Show last 3 files
            print(f"      📄 {file.name}")
    
    return len(parquet_files), len(json_files)

def validate_scraped_data():
    """Validate the structure of scraped data"""
    print("\n🔍 Validating Scraped Data")
    print("-" * 40)
    
    try:
        import pandas as pd
        
        data_dir = project_root / 'worker' / 'data'
        parquet_files = list(data_dir.glob("*.parquet"))
        
        if not parquet_files:
            print("   ⚠️ No parquet files to validate")
            return False, "No data files"
        
        # Read the most recent parquet file
        latest_file = max(parquet_files, key=lambda f: f.stat().st_mtime)
        print(f"   📊 Validating: {latest_file.name}")
        
        df = pd.read_parquet(latest_file)
        
        print(f"   📈 Data shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"   📝 Columns: {list(df.columns)}")
        
        # Check for required columns
        required_columns = ['id', 'title', 'selftext', 'created_utc', 'score', 'subreddit']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"   ⚠️ Missing columns: {missing_columns}")
        else:
            print(f"   ✅ All required columns present")
        
        # Show sample data
        if len(df) > 0:
            print(f"   📄 Sample post:")
            sample = df.iloc[0]
            print(f"      ID: {sample.get('id', 'N/A')}")
            print(f"      Title: {str(sample.get('title', 'N/A'))[:100]}...")
            print(f"      Subreddit: {sample.get('subreddit', 'N/A')}")
            print(f"      Score: {sample.get('score', 'N/A')}")
        
        return True, {"rows": len(df), "columns": list(df.columns)}
        
    except Exception as e:
        print(f"   ❌ Data validation failed: {e}")
        return False, str(e)

def main():
    """Main validation function"""
    print("🕷️ Reddit Scraper Validation")
    print("=" * 60)
    print(f"📁 Project Root: {project_root}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Credentials
    cred_success, cred_msg = test_reddit_credentials()
    results.append(("Credentials", cred_success, cred_msg))
    
    if not cred_success:
        print("\n❌ Cannot proceed without valid Reddit credentials")
        print("💡 Configure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env.scheduler")
        return
    
    # Test 2: Connection
    conn_success, conn_msg = test_reddit_connection()
    results.append(("Connection", conn_success, conn_msg))
    
    if not conn_success:
        print("\n❌ Cannot proceed without Reddit API connection")
        return
    
    # Test 3: Scraper Import
    import_success, import_msg = test_reddit_scraper_import()
    results.append(("Scraper Import", import_success, import_msg))
    
    if not import_success:
        print("\n❌ Cannot proceed without RedditScraper import")
        return
    
    # Test 4: Small Scraping Operation
    print("\n⚠️ About to perform a small scraping test (2 posts from r/test)")
    print("This will make actual API calls to Reddit.")
    
    user_input = input("Proceed with scraping test? [y/N]: ").strip().lower()
    
    if user_input == 'y':
        scrape_success, scrape_msg = test_small_scraping_operation()
        results.append(("Scraping Test", scrape_success, scrape_msg))
        
        if scrape_success:
            # Test 5: Check Data Files
            parquet_count, json_count = check_data_files()
            results.append(("Data Files", parquet_count > 0, f"{parquet_count} parquet, {json_count} JSON"))
            
            # Test 6: Validate Data
            if parquet_count > 0:
                validate_success, validate_msg = validate_scraped_data()
                results.append(("Data Validation", validate_success, validate_msg))
    else:
        print("   ⏭️ Skipping scraping test")
        results.append(("Scraping Test", None, "Skipped by user"))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 REDDIT SCRAPER VALIDATION SUMMARY")
    print("=" * 60)
    
    total_tests = len([r for r in results if r[1] is not None])
    passed_tests = len([r for r in results if r[1] is True])
    failed_tests = len([r for r in results if r[1] is False])
    
    print(f"📈 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    
    print("\n📋 Detailed Results:")
    for test_name, status, message in results:
        if status is True:
            print(f"   ✅ {test_name}: {message}")
        elif status is False:
            print(f"   ❌ {test_name}: {message}")
        else:
            print(f"   ⏭️ {test_name}: {message}")
    
    if failed_tests == 0 and passed_tests > 0:
        print("\n🎉 Reddit scraper validation successful!")
        print("🚀 Ready to use Reddit scraping functionality")
    elif failed_tests > 0:
        print(f"\n⚠️ Reddit scraper validation completed with {failed_tests} issues")
    
    print("\n💡 Next steps:")
    print("   • Test full pipeline: python test_pipeline_api.py")
    print("   • Start worker service: python run_scheduled_worker.py")

if __name__ == "__main__":
    main()
