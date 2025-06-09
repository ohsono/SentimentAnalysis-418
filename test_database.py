#!/usr/bin/env python3

"""
Comprehensive Database Connection Test
Tests PostgreSQL connection, creates tables, and verifies data storage
"""

import os
import sys
import asyncio
from datetime import datetime, timezone

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, '.env'))
    print("✅ Environment variables loaded")
except ImportError:
    print("❌ python-dotenv not installed")

async def test_database_setup():
    """Test complete database setup"""
    print("🗄️  COMPREHENSIVE DATABASE TEST")
    print("=" * 50)
    
    # 1. Check environment variables
    print("\n📊 Checking database environment variables:")
    db_vars = {
        'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
        'POSTGRES_PORT': os.getenv('POSTGRES_PORT'),
        'POSTGRES_DB': os.getenv('POSTGRES_DB'),
        'POSTGRES_USER': os.getenv('POSTGRES_USER'),
        'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD')
    }
    
    for var, value in db_vars.items():
        print(f"  {var}: {'✅ Found' if value else '❌ Missing'}")
    
    if not all(db_vars.values()):
        print("❌ Missing required database environment variables!")
        return False
    
    # 2. Check dependencies
    print("\n📦 Checking database dependencies:")
    try:
        import asyncpg
        print("  ✅ asyncpg installed")
    except ImportError:
        print("  ❌ asyncpg not installed")
        print("     Install with: pip install asyncpg")
        return False
    
    try:
        import sqlalchemy
        print("  ✅ sqlalchemy installed")
    except ImportError:
        print("  ❌ sqlalchemy not installed")
        print("     Install with: pip install sqlalchemy[asyncio]")
        return False
    
    # 3. Test basic PostgreSQL connection
    print("\n🔌 Testing PostgreSQL connection:")
    try:
        conn = await asyncpg.connect(
            host=db_vars['POSTGRES_HOST'],
            port=int(db_vars['POSTGRES_PORT']),
            database=db_vars['POSTGRES_DB'],
            user=db_vars['POSTGRES_USER'],
            password=db_vars['POSTGRES_PASSWORD']
        )
        print("  ✅ PostgreSQL connection successful!")
        
        # Test basic query
        version = await conn.fetchval('SELECT version()')
        print(f"  📋 PostgreSQL version: {version.split(',')[0]}")
        
        await conn.close()
        
    except Exception as e:
        print(f"  ❌ PostgreSQL connection failed: {e}")
        
        if "database" in str(e) and "does not exist" in str(e):
            print("\n💡 Database doesn't exist. Let's create it...")
            await create_database(db_vars)
            return await test_database_setup()  # Retry after creating database
        
        print("\n💡 Make sure PostgreSQL is running:")
        print("     - macOS: brew services start postgresql")
        print("     - Linux: sudo systemctl start postgresql")
        print("     - Windows: Start PostgreSQL service")
        return False
    
    # 4. Test DatabaseManager
    print("\n🔧 Testing DatabaseManager:")
    try:
        from app.database.postgres_manager import DatabaseManager
        print("  ✅ DatabaseManager imported successfully")
        
        db_manager = DatabaseManager()
        print("  ✅ DatabaseManager instance created")
        
        # Initialize database
        success = await db_manager.initialize()
        if success:
            print("  ✅ Database initialized successfully")
            print("  ✅ Tables created/verified")
        else:
            print("  ❌ Database initialization failed")
            return False
        
        # 5. Test data storage
        print("\n💾 Testing data storage:")
        
        # Test sentiment result storage
        sentiment_data = {
            'text': 'This is a test message for UCLA sentiment analysis',
            'sentiment': 'positive',
            'confidence': 0.85,
            'compound_score': 0.6,
            'processing_time_ms': 150.0,
            'model_used': 'test_model',
            'source': 'test'
        }
        
        sentiment_id = await db_manager.store_sentiment_result(sentiment_data)
        if sentiment_id:
            print(f"  ✅ Sentiment result stored with ID: {sentiment_id}")
        else:
            print("  ❌ Failed to store sentiment result")
            return False
        
        # Test Reddit post storage
        post_data = {
            'post_id': 'test_post_123',
            'title': 'Test UCLA Post',
            'selftext': 'This is a test post about UCLA',
            'subreddit': 'UCLA',
            'author': 'test_user',
            'score': 10,
            'upvote_ratio': 0.9,
            'num_comments': 5,
            'created_utc': datetime.now(timezone.utc).isoformat()
        }
        
        post_id = await db_manager.store_reddit_post(post_data, sentiment_id)
        if post_id:
            print(f"  ✅ Reddit post stored with ID: {post_id}")
        else:
            print("  ❌ Failed to store Reddit post")
            return False
        
        # Test alert storage
        alert_data = {
            'content_id': 'test_post_123',
            'content_text': 'Test alert content',
            'content_type': 'post',
            'alert_type': 'test_alert',
            'severity': 'low',
            'keywords_found': ['test'],
            'subreddit': 'UCLA',
            'author': 'test_user'
        }
        
        alert_id = await db_manager.store_sentiment_alert(alert_data, sentiment_id)
        if alert_id:
            print(f"  ✅ Alert stored with ID: {alert_id}")
        else:
            print("  ❌ Failed to store alert")
            return False
        
        # 6. Test data retrieval
        print("\n📊 Testing data retrieval:")
        analytics = await db_manager.get_sentiment_analytics(days=1)
        if analytics:
            print("  ✅ Analytics retrieved successfully")
            print(f"     Sentiment distribution: {len(analytics.get('sentiment_distribution', []))} entries")
        else:
            print("  ❌ Failed to retrieve analytics")
        
        # Close database connection
        await db_manager.close()
        print("  ✅ Database connection closed")
        
        print("\n🎉 ALL DATABASE TESTS PASSED!")
        print("✅ Your database is ready to store Reddit scraper data!")
        return True
        
    except Exception as e:
        print(f"  ❌ DatabaseManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def create_database(db_vars):
    """Create the database if it doesn't exist"""
    print("\n🔨 Creating database:")
    try:
        # Connect to default postgres database to create our database
        conn = await asyncpg.connect(
            host=db_vars['POSTGRES_HOST'],
            port=int(db_vars['POSTGRES_PORT']),
            database='postgres',  # Connect to default database
            user=db_vars['POSTGRES_USER'],
            password=db_vars['POSTGRES_PASSWORD']
        )
        
        # Create the database
        await conn.execute(f"CREATE DATABASE {db_vars['POSTGRES_DB']}")
        print(f"  ✅ Database '{db_vars['POSTGRES_DB']}' created successfully")
        
        await conn.close()
        
    except Exception as e:
        if "already exists" in str(e):
            print(f"  ⚠️  Database '{db_vars['POSTGRES_DB']}' already exists")
        else:
            print(f"  ❌ Failed to create database: {e}")
            raise

async def check_postgresql_status():
    """Check if PostgreSQL is running"""
    print("\n🔍 Checking PostgreSQL status:")
    
    # Try different ways to check PostgreSQL status
    import subprocess
    import shutil
    
    # Check if PostgreSQL is in PATH
    pg_isready = shutil.which('pg_isready')
    if pg_isready:
        try:
            result = subprocess.run([pg_isready], capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ PostgreSQL is running and accepting connections")
                return True
            else:
                print("  ❌ PostgreSQL is not accepting connections")
        except Exception as e:
            print(f"  ⚠️  Could not check PostgreSQL status: {e}")
    
    # Check if PostgreSQL process is running
    try:
        result = subprocess.run(['pgrep', 'postgres'], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ PostgreSQL process is running")
            return True
        else:
            print("  ❌ PostgreSQL process not found")
    except Exception:
        pass
    
    print("  💡 To start PostgreSQL:")
    print("     macOS with Homebrew: brew services start postgresql")
    print("     Linux: sudo systemctl start postgresql")
    print("     Docker: docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres")
    
    return False

if __name__ == "__main__":
    asyncio.run(test_database_setup())
