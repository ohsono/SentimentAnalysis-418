#!/usr/bin/env python3

"""
PostgreSQL Database Integration for UCLA Sentiment Analysis
Async database operations with appropriate schemas
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum

try:
    import asyncpg
    import asyncio
    from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text, Boolean, JSON
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker, declarative_base
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️  PostgreSQL dependencies not available. Install with: pip install asyncpg sqlalchemy")

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "ucla_sentiment"),
    "username": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "password")
}

# SQLAlchemy setup
Base = declarative_base()

class SentimentAnalysisResult(Base):
    """Table for storing sentiment analysis results"""
    __tablename__ = "sentiment_analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    text_content = Column(Text, nullable=False)
    text_hash = Column(String(64), nullable=False, index=True)  # For deduplication
    sentiment = Column(String(20), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    compound_score = Column(Float, nullable=False)
    probabilities = Column(JSON, nullable=True)
    processing_time_ms = Column(Float, nullable=False)
    model_used = Column(String(100), nullable=False, index=True)
    model_name = Column(String(200), nullable=True)
    source = Column(String(50), nullable=False, index=True)  # 'model-service', 'vader-fallback', 'simple-fallback'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class RedditPost(Base):
    """Table for storing Reddit posts"""
    __tablename__ = "reddit_posts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    selftext = Column(Text, nullable=True)
    subreddit = Column(String(100), nullable=False, index=True)
    author = Column(String(100), nullable=True)
    score = Column(Integer, nullable=True)
    upvote_ratio = Column(Float, nullable=True)
    num_comments = Column(Integer, nullable=True)
    created_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    scraped_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    sentiment_analysis_id = Column(Integer, nullable=True)  # FK to sentiment_analysis_results

class RedditComment(Base):
    """Table for storing Reddit comments"""
    __tablename__ = "reddit_comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(20), unique=True, nullable=False, index=True)
    post_id = Column(String(20), nullable=False, index=True)
    body = Column(Text, nullable=False)
    author = Column(String(100), nullable=True)
    score = Column(Integer, nullable=True)
    created_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    scraped_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    sentiment_analysis_id = Column(Integer, nullable=True)  # FK to sentiment_analysis_results

class SentimentAlert(Base):
    """Table for storing sentiment-based alerts"""
    __tablename__ = "sentiment_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String(50), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    content_type = Column(String(20), nullable=False)  # 'post', 'comment'
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    keywords_found = Column(JSON, nullable=True)
    subreddit = Column(String(100), nullable=False, index=True)
    author = Column(String(100), nullable=True)
    status = Column(String(20), default='active', index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    sentiment_analysis_id = Column(Integer, nullable=True)  # FK to sentiment_analysis_results

class DatabaseManager:
    """Async database manager for UCLA Sentiment Analysis"""
    
    def __init__(self):
        self.database_url = self._build_database_url()
        self.engine = None
        self.async_session = None
        self.connection_pool = None
        
    def _build_database_url(self) -> str:
        """Build database URL from configuration"""
        config = DATABASE_CONFIG
        return f"postgresql+asyncpg://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        if not POSTGRES_AVAILABLE:
            logger.warning("PostgreSQL dependencies not available")
            return False
        
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=10,
                max_overflow=20
            )
            
            # Create session factory
            self.async_session = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create connection pool for raw queries
            self.connection_pool = await asyncpg.create_pool(
                host=DATABASE_CONFIG["host"],
                port=DATABASE_CONFIG["port"],
                database=DATABASE_CONFIG["database"],
                user=DATABASE_CONFIG["username"],
                password=DATABASE_CONFIG["password"],
                min_size=5,
                max_size=20
            )
            
            # Create tables
            await self.create_tables()
            
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    async def create_tables(self):
        """Create database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    
    async def close(self):
        """Close database connections"""
        if self.connection_pool:
            await self.connection_pool.close()
        if self.engine:
            await self.engine.dispose()
    
    async def store_sentiment_result(self, sentiment_data: Dict[str, Any]) -> Optional[int]:
        """Store sentiment analysis result"""
        try:
            import hashlib
            
            # Create text hash for deduplication
            text_hash = hashlib.sha256(sentiment_data['text'].encode()).hexdigest()
            
            async with self.connection_pool.acquire() as conn:
                # Check if already exists
                existing = await conn.fetchval(
                    "SELECT id FROM sentiment_analysis_results WHERE text_hash = $1",
                    text_hash
                )
                
                if existing:
                    logger.debug(f"Sentiment result already exists for text hash: {text_hash[:16]}...")
                    return existing
                
                # Insert new result
                result_id = await conn.fetchval("""
                    INSERT INTO sentiment_analysis_results 
                    (text_content, text_hash, sentiment, confidence, compound_score, 
                     probabilities, processing_time_ms, model_used, model_name, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                """, 
                    sentiment_data['text'],
                    text_hash,
                    sentiment_data['sentiment'],
                    sentiment_data['confidence'],
                    sentiment_data['compound_score'],
                    sentiment_data.get('probabilities'),
                    sentiment_data['processing_time_ms'],
                    sentiment_data.get('model_used', 'unknown'),
                    sentiment_data.get('model_name', 'unknown'),
                    sentiment_data.get('source', 'api')
                )
                
                logger.debug(f"Stored sentiment result with ID: {result_id}")
                return result_id
                
        except Exception as e:
            logger.error(f"Failed to store sentiment result: {e}")
            return None
    
    async def store_reddit_post(self, post_data: Dict[str, Any], sentiment_id: Optional[int] = None) -> Optional[int]:
        """Store Reddit post data"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Check if post already exists
                existing = await conn.fetchval(
                    "SELECT id FROM reddit_posts WHERE post_id = $1",
                    post_data['post_id']
                )
                
                if existing:
                    # Update sentiment_analysis_id if provided
                    if sentiment_id:
                        await conn.execute(
                            "UPDATE reddit_posts SET sentiment_analysis_id = $1 WHERE id = $2",
                            sentiment_id, existing
                        )
                    return existing
                
                # Insert new post
                post_id = await conn.fetchval("""
                    INSERT INTO reddit_posts 
                    (post_id, title, selftext, subreddit, author, score, upvote_ratio, 
                     num_comments, created_utc, sentiment_analysis_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                """,
                    post_data['post_id'],
                    post_data['title'],
                    post_data.get('selftext', ''),
                    post_data.get('subreddit', 'UCLA'),
                    post_data.get('author'),
                    post_data.get('score'),
                    post_data.get('upvote_ratio'),
                    post_data.get('num_comments'),
                    datetime.fromisoformat(post_data['created_utc'].replace('Z', '+00:00')),
                    sentiment_id
                )
                
                logger.debug(f"Stored Reddit post with ID: {post_id}")
                return post_id
                
        except Exception as e:
            logger.error(f"Failed to store Reddit post: {e}")
            return None
    
    async def store_sentiment_alert(self, alert_data: Dict[str, Any], sentiment_id: Optional[int] = None) -> Optional[int]:
        """Store sentiment alert"""
        try:
            async with self.connection_pool.acquire() as conn:
                alert_id = await conn.fetchval("""
                    INSERT INTO sentiment_alerts 
                    (content_id, content_text, content_type, alert_type, severity, 
                     keywords_found, subreddit, author, sentiment_analysis_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """,
                    alert_data['content_id'],
                    alert_data['content_text'],
                    alert_data.get('content_type', 'post'),
                    alert_data['alert_type'],
                    alert_data['severity'],
                    alert_data.get('keywords_found'),
                    alert_data.get('subreddit', 'UCLA'),
                    alert_data.get('author'),
                    sentiment_id
                )
                
                logger.debug(f"Stored sentiment alert with ID: {alert_id}")
                return alert_id
                
        except Exception as e:
            logger.error(f"Failed to store sentiment alert: {e}")
            return None
    
    async def get_sentiment_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get sentiment analytics for dashboard"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Get sentiment distribution
                sentiment_dist = await conn.fetch("""
                    SELECT sentiment, COUNT(*) as count
                    FROM sentiment_analysis_results 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY sentiment
                """ % days)
                
                # Get model usage statistics
                model_stats = await conn.fetch("""
                    SELECT model_used, source, COUNT(*) as count
                    FROM sentiment_analysis_results 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY model_used, source
                """ % days)
                
                # Get average confidence by model
                confidence_stats = await conn.fetch("""
                    SELECT model_used, AVG(confidence) as avg_confidence, AVG(processing_time_ms) as avg_time
                    FROM sentiment_analysis_results 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY model_used
                """ % days)
                
                # Get recent alerts
                recent_alerts = await conn.fetch("""
                    SELECT alert_type, severity, COUNT(*) as count
                    FROM sentiment_alerts 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY alert_type, severity
                """ % days)
                
                return {
                    "sentiment_distribution": [dict(row) for row in sentiment_dist],
                    "model_usage": [dict(row) for row in model_stats],
                    "confidence_stats": [dict(row) for row in confidence_stats],
                    "recent_alerts": [dict(row) for row in recent_alerts],
                    "time_period_days": days,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get sentiment analytics: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to manage database size"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Delete old sentiment results
                deleted_sentiment = await conn.fetchval("""
                    DELETE FROM sentiment_analysis_results 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """ % days_to_keep)
                
                # Delete old Reddit posts
                deleted_posts = await conn.fetchval("""
                    DELETE FROM reddit_posts 
                    WHERE scraped_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """ % days_to_keep)
                
                # Delete old alerts (keep longer)
                deleted_alerts = await conn.fetchval("""
                    DELETE FROM sentiment_alerts 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """ % (days_to_keep * 2))
                
                logger.info(f"Cleanup completed: {deleted_sentiment} sentiment results, {deleted_posts} posts, {deleted_alerts} alerts deleted")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

class AsyncDataLoader:
    """Async data loader for background processing"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.processing_queue = asyncio.Queue()
        self.is_running = False
        
    async def start(self):
        """Start the async data loader"""
        self.is_running = True
        asyncio.create_task(self._process_queue())
        logger.info("Async data loader started")
    
    async def stop(self):
        """Stop the async data loader"""
        self.is_running = False
        logger.info("Async data loader stopped")
    
    async def queue_sentiment_result(self, sentiment_data: Dict[str, Any], post_data: Optional[Dict[str, Any]] = None):
        """Queue sentiment result for async processing"""
        await self.processing_queue.put({
            "type": "sentiment_result",
            "sentiment_data": sentiment_data,
            "post_data": post_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def queue_alert(self, alert_data: Dict[str, Any]):
        """Queue alert for async processing"""
        await self.processing_queue.put({
            "type": "alert",
            "alert_data": alert_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def _process_queue(self):
        """Process queued items"""
        while self.is_running:
            try:
                # Wait for items with timeout
                item = await asyncio.wait_for(self.processing_queue.get(), timeout=5.0)
                
                if item["type"] == "sentiment_result":
                    # Store sentiment result
                    sentiment_id = await self.db_manager.store_sentiment_result(item["sentiment_data"])
                    
                    # Store associated post data if provided
                    if item.get("post_data") and sentiment_id:
                        await self.db_manager.store_reddit_post(item["post_data"], sentiment_id)
                
                elif item["type"] == "alert":
                    # Store alert
                    await self.db_manager.store_sentiment_alert(item["alert_data"])
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except asyncio.TimeoutError:
                # No items in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing queue item: {e}")

# Global database manager and data loader
db_manager = DatabaseManager()
data_loader = AsyncDataLoader(db_manager)
