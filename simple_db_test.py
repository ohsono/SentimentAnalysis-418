#!/usr/bin/env python3

"""
Simple database test that bypasses DatabaseManager
This will help us identify if the issue is with the DatabaseManager class or something else
"""

import os
import sys
import asyncio
from datetime import datetime, timezone

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("❌ python-dotenv not installed")

async def simple_database_test():
    """Test database operations without using DatabaseManager"""
    print("🔧 SIMPLE DATABASE TEST")
    print("=" * 40)
    
    try:
        import asyncpg
        print("✅ asyncpg imported")
        
        # Connect to database
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database=os.getenv('POSTGRES_DB', 'sentiment_db'),
            user=os.getenv('POSTGRES_USER', 'sentiment_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'sentiment_password')
        )
        print("✅ Connected to PostgreSQL")
        
        # Create tables manually
        print("\n📊 Creating tables...")
        
        # Create sentiment_analysis_results table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_analysis_results (
                id SERIAL PRIMARY KEY,
                text_content TEXT NOT NULL,
                text_hash VARCHAR(64) NOT NULL,
                sentiment VARCHAR(20) NOT NULL,
                confidence FLOAT NOT NULL,
                compound_score FLOAT NOT NULL,
                probabilities JSONB,
                processing_time_ms FLOAT NOT NULL,
                model_used VARCHAR(100) NOT NULL,
                model_name VARCHAR(200),
                source VARCHAR(50) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        ''')
        print("  ✅ sentiment_analysis_results table created")
        
        # Create reddit_posts table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS reddit_posts (
                id SERIAL PRIMARY KEY,
                post_id VARCHAR(20) UNIQUE NOT NULL,
                title TEXT NOT NULL,
                selftext TEXT,
                subreddit VARCHAR(100) NOT NULL,
                author VARCHAR(100),
                score INTEGER,
                upvote_ratio FLOAT,
                num_comments INTEGER,
                created_utc TIMESTAMP WITH TIME ZONE NOT NULL,
                scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                sentiment_analysis_id INTEGER
            )
        ''')
        print("  ✅ reddit_posts table created")
        
        # Create reddit_comments table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS reddit_comments (
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
        print("  ✅ reddit_comments table created")
        
        # Create sentiment_alerts table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_alerts (
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
        print("  ✅ sentiment_alerts table created")
        
        # Test data insertion
        print("\n💾 Testing data insertion...")
        
        # Insert test sentiment result
        sentiment_id = await conn.fetchval('''
            INSERT INTO sentiment_analysis_results 
            (text_content, text_hash, sentiment, confidence, compound_score, 
             processing_time_ms, model_used, source)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        ''', 
            'This is a test message',
            'test_hash_123',
            'positive',
            0.85,
            0.6,
            150.0,
            'test_model',
            'test'
        )
        print(f"  ✅ Sentiment result inserted with ID: {sentiment_id}")
        
        # Insert test Reddit post
        post_id = await conn.fetchval('''
            INSERT INTO reddit_posts 
            (post_id, title, selftext, subreddit, author, score, 
             upvote_ratio, num_comments, created_utc, sentiment_analysis_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
        ''',
            'test_post_123',
            'Test UCLA Post',
            'This is a test post',
            'UCLA',
            'test_user',
            10,
            0.9,
            5,
            datetime.now(timezone.utc),
            sentiment_id
        )
        print(f"  ✅ Reddit post inserted with ID: {post_id}")
        
        # Insert test comment
        comment_id = await conn.fetchval('''
            INSERT INTO reddit_comments 
            (comment_id, post_id, body, author, score, created_utc, sentiment_analysis_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        ''',
            'test_comment_123',
            'test_post_123',
            'This is a test comment',
            'test_user_2',
            5,
            datetime.now(timezone.utc),
            sentiment_id
        )
        print(f"  ✅ Reddit comment inserted with ID: {comment_id}")
        
        # Insert test alert
        alert_id = await conn.fetchval('''
            INSERT INTO sentiment_alerts 
            (content_id, content_text, content_type, alert_type, severity, 
             keywords_found, subreddit, author, sentiment_analysis_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        ''',
            'test_post_123',
            'Test alert content',
            'post',
            'test_alert',
            'low',
            '["test"]',
            'UCLA',
            'test_user',
            sentiment_id
        )
        print(f"  ✅ Alert inserted with ID: {alert_id}")
        
        # Test data retrieval
        print("\n📊 Testing data retrieval...")
        
        # Count records
        sentiment_count = await conn.fetchval('SELECT COUNT(*) FROM sentiment_analysis_results')
        posts_count = await conn.fetchval('SELECT COUNT(*) FROM reddit_posts')
        comments_count = await conn.fetchval('SELECT COUNT(*) FROM reddit_comments')
        alerts_count = await conn.fetchval('SELECT COUNT(*) FROM sentiment_alerts')
        
        print(f"  📈 Sentiment results: {sentiment_count}")
        print(f"  📈 Reddit posts: {posts_count}")
        print(f"  📈 Reddit comments: {comments_count}")
        print(f"  📈 Alerts: {alerts_count}")
        
        # Close connection
        await conn.close()
        print("\n🎉 SIMPLE DATABASE TEST PASSED!")
        print("✅ Your database is working perfectly!")
        print("✅ The issue must be with the DatabaseManager class or test script")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Simple database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(simple_database_test())
