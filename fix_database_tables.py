#!/usr/bin/env python3

"""
Fix database tables to match the DatabaseManager expectations
This will drop existing tables and recreate them with the correct structure
"""

import os
import asyncio

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("❌ python-dotenv not installed")

async def fix_database_tables():
    """Drop and recreate tables with correct structure"""
    print("🔧 FIXING DATABASE TABLES")
    print("=" * 40)
    
    try:
        import asyncpg
        
        # Connect to database
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database=os.getenv('POSTGRES_DB', 'sentiment_db'),
            user=os.getenv('POSTGRES_USER', 'sentiment_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'sentiment_password')
        )
        print("✅ Connected to PostgreSQL")
        
        print("\n⚠️  WARNING: This will drop all existing tables!")
        print("Press Enter to continue, or Ctrl+C to cancel...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            return
        
        # Drop existing tables
        print("\n🗑️  Dropping existing tables...")
        drop_queries = [
            "DROP TABLE IF EXISTS sentiment_alerts CASCADE",
            "DROP TABLE IF EXISTS reddit_comments CASCADE", 
            "DROP TABLE IF EXISTS reddit_posts CASCADE",
            "DROP TABLE IF EXISTS sentiment_analysis_results CASCADE"
        ]
        
        for query in drop_queries:
            await conn.execute(query)
            print(f"  ✅ {query}")
        
        # Create tables with correct structure (matching DatabaseManager)
        print("\n📊 Creating tables with correct structure...")
        
        # Create sentiment_analysis_results table (matches DatabaseManager model)
        await conn.execute('''
            CREATE TABLE sentiment_analysis_results (
                id SERIAL PRIMARY KEY,
                text_content TEXT NOT NULL,
                text_hash VARCHAR(64) NOT NULL,
                sentiment VARCHAR(20) NOT NULL,
                confidence REAL NOT NULL,
                compound_score REAL NOT NULL,
                probabilities JSONB,
                processing_time_ms REAL NOT NULL,
                model_used VARCHAR(100) NOT NULL,
                model_name VARCHAR(200),
                source VARCHAR(50) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        ''')
        
        # Add indexes
        await conn.execute('CREATE INDEX ON sentiment_analysis_results (text_hash)')
        await conn.execute('CREATE INDEX ON sentiment_analysis_results (sentiment)')
        await conn.execute('CREATE INDEX ON sentiment_analysis_results (model_used)')
        await conn.execute('CREATE INDEX ON sentiment_analysis_results (source)')
        await conn.execute('CREATE INDEX ON sentiment_analysis_results (created_at)')
        print("  ✅ sentiment_analysis_results table created")
        
        # Create reddit_posts table
        await conn.execute('''
            CREATE TABLE reddit_posts (
                id SERIAL PRIMARY KEY,
                post_id VARCHAR(20) UNIQUE NOT NULL,
                title TEXT NOT NULL,
                selftext TEXT,
                subreddit VARCHAR(100) NOT NULL,
                author VARCHAR(100),
                score INTEGER,
                upvote_ratio REAL,
                num_comments INTEGER,
                created_utc TIMESTAMP WITH TIME ZONE NOT NULL,
                scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                sentiment_analysis_id INTEGER
            )
        ''')
        
        # Add indexes
        await conn.execute('CREATE INDEX ON reddit_posts (post_id)')
        await conn.execute('CREATE INDEX ON reddit_posts (subreddit)')
        await conn.execute('CREATE INDEX ON reddit_posts (created_utc)')
        print("  ✅ reddit_posts table created")
        
        # Create reddit_comments table
        await conn.execute('''
            CREATE TABLE reddit_comments (
                id SERIAL PRIMARY KEY,
                comment_id VARCHAR(20) UNIQUE NOT NULL,
                post_id VARCHAR(20) NOT NULL,
                body TEXT NOT NULL,
                author VARCHAR(100),
                score INTEGER,
                created_utc TIMESTAMP WITH TIME ZONE NOT NULL,
                scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                sentiment_analysis_id INTEGER
            )
        ''')
        
        # Add indexes
        await conn.execute('CREATE INDEX ON reddit_comments (comment_id)')
        await conn.execute('CREATE INDEX ON reddit_comments (post_id)')
        await conn.execute('CREATE INDEX ON reddit_comments (created_utc)')
        print("  ✅ reddit_comments table created")
        
        # Create sentiment_alerts table
        await conn.execute('''
            CREATE TABLE sentiment_alerts (
                id SERIAL PRIMARY KEY,
                content_id VARCHAR(50) NOT NULL,
                content_text TEXT NOT NULL,
                content_type VARCHAR(20) NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                keywords_found JSONB,
                subreddit VARCHAR(100) NOT NULL,
                author VARCHAR(100),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                sentiment_analysis_id INTEGER
            )
        ''')
        
        # Add indexes  
        await conn.execute('CREATE INDEX ON sentiment_alerts (content_id)')
        await conn.execute('CREATE INDEX ON sentiment_alerts (alert_type)')
        await conn.execute('CREATE INDEX ON sentiment_alerts (severity)')
        await conn.execute('CREATE INDEX ON sentiment_alerts (subreddit)')
        await conn.execute('CREATE INDEX ON sentiment_alerts (status)')
        await conn.execute('CREATE INDEX ON sentiment_alerts (created_at)')
        print("  ✅ sentiment_alerts table created")
        
        # Test data insertion with correct columns
        print("\n💾 Testing data insertion...")
        
        # Insert test sentiment result
        sentiment_id = await conn.fetchval('''
            INSERT INTO sentiment_analysis_results 
            (text_content, text_hash, sentiment, confidence, compound_score, 
             processing_time_ms, model_used, source)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        ''', 
            'This is a test message for UCLA sentiment analysis',
            'test_hash_123',
            'positive',
            0.85,
            0.6,
            150.0,
            'test_model',
            'test'
        )
        print(f"  ✅ Test sentiment result inserted with ID: {sentiment_id}")
        
        # Insert test Reddit post
        from datetime import datetime, timezone
        post_id = await conn.fetchval('''
            INSERT INTO reddit_posts 
            (post_id, title, selftext, subreddit, author, score, 
             upvote_ratio, num_comments, created_utc, sentiment_analysis_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
        ''',
            'test_post_456',
            'Test UCLA Post - Fixed',
            'This is a test post with fixed structure',
            'UCLA',
            'test_user',
            15,
            0.95,
            3,
            datetime.now(timezone.utc),
            sentiment_id
        )
        print(f"  ✅ Test Reddit post inserted with ID: {post_id}")
        
        await conn.close()
        
        print("\n🎉 DATABASE TABLES FIXED!")
        print("✅ All tables now match the DatabaseManager expectations")
        print("✅ You can now run the Reddit scraper with database storage")
        
        print("\n💡 Next steps:")
        print("  1. Run: python test_database.py")
        print("  2. Run: python reddit_scraper_with_db.py")
        
    except Exception as e:
        print(f"❌ Error fixing database tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_database_tables())
