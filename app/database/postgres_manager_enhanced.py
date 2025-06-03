#!/usr/bin/env python3

"""
Enhanced PostgreSQL Database Integration for UCLA Sentiment Analysis
Async database operations with proper schemas and data loading
"""

import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

try:
    import asyncpg
    from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text, Boolean, JSON, Index
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy.dialects.postgresql import UUID
    import uuid
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️  PostgreSQL dependencies not available. Install with: pip install asyncpg sqlalchemy[asyncio]")

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
#Base = DeclarativeBase()
class Base(DeclarativeBase):
    pass

class SentimentAnalysisResult(Base):
    """Enhanced table for storing sentiment analysis results"""
    __tablename__ = "sentiment_analysis_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text_content = Column(Text, nullable=False)
    text_hash = Column(String(64), nullable=False, index=True)  # For deduplication
    
    # Sentiment results
    sentiment = Column(String(20), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    compound_score = Column(Float, nullable=False)
    probabilities = Column(JSON, nullable=True)
    
    # Processing metadata
    processing_time_ms = Column(Float, nullable=False)
    model_used = Column(String(100), nullable=False, index=True)
    model_name = Column(String(200), nullable=True)
    source = Column(String(50), nullable=False, index=True)  # 'llm-service', 'vader-fallback'
    
    # Request metadata
    request_type = Column(String(50), default='api', index=True)  # 'api', 'batch', 'scrape'
    batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Content metadata (for Reddit data)
    subreddit = Column(String(100), nullable=True, index=True)
    post_id = Column(String(50), nullable=True, index=True)
    comment_id = Column(String(50), nullable=True, index=True)
    author = Column(String(100), nullable=True, index=True)
    category = Column(String(50), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    content_created_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_sentiment_created_at', 'sentiment', 'created_at'),
        Index('idx_model_source', 'model_used', 'source'),
        Index('idx_text_hash_unique', 'text_hash'),
        Index('idx_subreddit_created', 'subreddit', 'created_at'),
        Index('idx_category_sentiment', 'category', 'sentiment'),
        Index('idx_source_created', 'source', 'created_at'),
    )

class RedditPost(Base):
    """Enhanced table for storing Reddit posts"""
    __tablename__ = "reddit_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Content
    title = Column(Text, nullable=False)
    selftext = Column(Text, nullable=True)
    subreddit = Column(String(100), nullable=False, index=True)
    author = Column(String(100), nullable=True, index=True)
    
    # Reddit metadata
    score = Column(Integer, nullable=True)
    upvote_ratio = Column(Float, nullable=True)
    num_comments = Column(Integer, nullable=True)
    reddit_created_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Processing status
    sentiment_analysis_id = Column(UUID(as_uuid=True), nullable=True)
    sentiment_analyzed = Column(Boolean, default=False, index=True)
    alert_checked = Column(Boolean, default=False, index=True)
    
    # Timestamps
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    __table_args__ = (
        Index('idx_subreddit_reddit_created', 'subreddit', 'reddit_created_utc'),
        Index('idx_sentiment_analyzed', 'sentiment_analyzed', 'created_at'),
    )

class RedditComment(Base):
    """Table for storing Reddit comments"""
    __tablename__ = "reddit_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id = Column(String(20), unique=True, nullable=False, index=True)
    post_id = Column(String(20), nullable=False, index=True)
    
    # Content
    body = Column(Text, nullable=False)
    author = Column(String(100), nullable=True, index=True)
    score = Column(Integer, nullable=True)
    reddit_created_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Processing status
    sentiment_analysis_id = Column(UUID(as_uuid=True), nullable=True)
    sentiment_analyzed = Column(Boolean, default=False, index=True)
    
    # Timestamps
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

class SentimentAlert(Base):
    """Enhanced table for storing sentiment-based alerts"""
    __tablename__ = "sentiment_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(String(50), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    content_type = Column(String(20), nullable=False, index=True)  # 'post', 'comment', 'api_request'
    
    # Alert details
    alert_type = Column(String(50), nullable=False, index=True)  # 'mental_health', 'stress', 'harassment'
    severity = Column(String(20), nullable=False, index=True)    # 'low', 'medium', 'high', 'critical'
    keywords_found = Column(JSON, nullable=True)
    
    # Sentiment context
    sentiment = Column(String(20), nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    compound_score = Column(Float, nullable=True)
    sentiment_analysis_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Content metadata
    subreddit = Column(String(100), nullable=True, index=True)
    author = Column(String(100), nullable=True, index=True)
    
    # Alert status and handling
    status = Column(String(20), default='active', index=True)  # 'active', 'reviewed', 'resolved', 'false_positive'
    priority = Column(Integer, default=50, index=True)  # 1-100, higher = more urgent
    assigned_to = Column(String(100), nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_alert_type_severity', 'alert_type', 'severity'),
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_priority_status', 'priority', 'status'),
        Index('idx_subreddit_severity', 'subreddit', 'severity'),
    )

class BatchProcessingJob(Base):
    """Table for tracking batch processing jobs"""
    __tablename__ = "batch_processing_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    # Job details
    job_type = Column(String(50), nullable=False, index=True)  # 'sentiment_batch', 'reddit_scrape'
    total_items = Column(Integer, nullable=False)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    
    # Processing status
    status = Column(String(20), nullable=False, default='pending', index=True)  # 'pending', 'processing', 'completed', 'failed'
    progress_percentage = Column(Float, default=0.0)
    
    # Performance metrics
    total_processing_time_ms = Column(Float, nullable=True)
    average_time_per_item_ms = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    job_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SystemMetrics(Base):
    """Table for storing system performance metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_category = Column(String(50), nullable=False, index=True)  # 'performance', 'usage', 'error', 'failsafe'
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # 'ms', 'count', 'percentage', etc.
    
    # Context
    source_service = Column(String(50), nullable=False, index=True)  # 'api', 'model-service', 'database'
    source_component = Column(String(100), nullable=True)
    additional_tags = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    __table_args__ = (
        Index('idx_metric_category_created', 'metric_category', 'created_at'),
        Index('idx_source_metric', 'source_service', 'metric_name'),
        Index('idx_metric_name_created', 'metric_name', 'created_at'),
    )

class AnalyticsCache(Base):
    """Table for caching computed analytics"""
    __tablename__ = "analytics_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(200), unique=True, nullable=False, index=True)
    cache_data = Column(JSON, nullable=False)
    
    # Cache metadata
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    computation_time_ms = Column(Float, nullable=True)
    cache_version = Column(String(20), default='1.0')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class DatabaseManager:
    """Enhanced async database manager with comprehensive features"""
    
    def __init__(self):
        self.database_url = self._build_database_url()
        self.engine = None
        self.async_session = None
        self.connection_pool = None
        self.initialized = False
        
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
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600
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
                min_size=10,
                max_size=30,
                command_timeout=60
            )
            
            # Create tables
            await self.create_tables()
            
            # Test connection
            await self.test_connection()
            
            self.initialized = True
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
    
    async def test_connection(self):
        """Test database connection"""
        async with self.connection_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise Exception("Database connection test failed")
        logger.info("Database connection test passed")
    
    async def close(self):
        """Close database connections"""
        if self.connection_pool:
            await self.connection_pool.close()
        if self.engine:
            await self.engine.dispose()
        logger.info("Database connections closed")
    
    async def store_sentiment_result(self, sentiment_data: Dict[str, Any]) -> Optional[str]:
        """Store sentiment analysis result with comprehensive data"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Check if already exists by text hash
                existing = await conn.fetchval(
                    "SELECT id FROM sentiment_analysis_results WHERE text_hash = $1",
                    sentiment_data['text_hash']
                )
                
                if existing:
                    logger.debug(f"Sentiment result already exists: {sentiment_data['text_hash'][:16]}...")
                    return str(existing)
                
                # Insert new result
                result_id = await conn.fetchval("""
                    INSERT INTO sentiment_analysis_results 
                    (text_content, text_hash, sentiment, confidence, compound_score, 
                     probabilities, processing_time_ms, model_used, model_name, source,
                     request_type, batch_id, subreddit, post_id, comment_id, author, category)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    RETURNING id
                """, 
                    sentiment_data['text'],
                    sentiment_data['text_hash'],
                    sentiment_data['sentiment'],
                    sentiment_data['confidence'],
                    sentiment_data['compound_score'],
                    sentiment_data.get('probabilities'),
                    sentiment_data['processing_time_ms'],
                    sentiment_data.get('model_used', 'unknown'),
                    sentiment_data.get('model_name', 'unknown'),
                    sentiment_data.get('source', 'api'),
                    sentiment_data.get('request_type', 'api'),
                    sentiment_data.get('batch_id'),
                    sentiment_data.get('subreddit'),
                    sentiment_data.get('post_id'),
                    sentiment_data.get('comment_id'),
                    sentiment_data.get('author'),
                    sentiment_data.get('category')
                )
                
                logger.debug(f"Stored sentiment result: {result_id}")
                return str(result_id)
                
        except Exception as e:
            logger.error(f"Failed to store sentiment result: {e}")
            return None
    
    async def store_reddit_post(self, post_data: Dict[str, Any], sentiment_id: Optional[str] = None) -> Optional[str]:
        """Store Reddit post with enhanced metadata"""
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
                            "UPDATE reddit_posts SET sentiment_analysis_id = $1, sentiment_analyzed = TRUE WHERE id = $2",
                            uuid.UUID(sentiment_id), existing
                        )
                    return str(existing)
                
                # Parse Reddit created time
                reddit_created = datetime.fromisoformat(post_data['created_utc'].replace('Z', '+00:00'))
                
                # Insert new post
                post_id = await conn.fetchval("""
                    INSERT INTO reddit_posts 
                    (post_id, title, selftext, subreddit, author, score, upvote_ratio, 
                     num_comments, reddit_created_utc, sentiment_analysis_id, sentiment_analyzed)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
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
                    reddit_created,
                    uuid.UUID(sentiment_id) if sentiment_id else None,
                    sentiment_id is not None
                )
                
                logger.debug(f"Stored Reddit post: {post_id}")
                return str(post_id)
                
        except Exception as e:
            logger.error(f"Failed to store Reddit post: {e}")
            return None
    
    async def store_sentiment_alert(self, alert_data: Dict[str, Any], sentiment_id: Optional[str] = None) -> Optional[str]:
        """Store sentiment alert with enhanced tracking"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Calculate priority based on severity and type
                priority_map = {
                    'critical': 90,
                    'high': 70,
                    'medium': 50,
                    'low': 30
                }
                
                # Mental health alerts get higher priority
                base_priority = priority_map.get(alert_data['severity'], 50)
                if alert_data['alert_type'] == 'mental_health':
                    base_priority = min(95, base_priority + 20)
                
                alert_id = await conn.fetchval("""
                    INSERT INTO sentiment_alerts 
                    (content_id, content_text, content_type, alert_type, severity, 
                     keywords_found, sentiment, confidence, compound_score, sentiment_analysis_id,
                     subreddit, author, priority)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    RETURNING id
                """,
                    alert_data['content_id'],
                    alert_data['content_text'],
                    alert_data.get('content_type', 'post'),
                    alert_data['alert_type'],
                    alert_data['severity'],
                    alert_data.get('keywords_found'),
                    alert_data.get('sentiment'),
                    alert_data.get('confidence'),
                    alert_data.get('compound_score'),
                    uuid.UUID(sentiment_id) if sentiment_id else None,
                    alert_data.get('subreddit', 'UCLA'),
                    alert_data.get('author'),
                    base_priority
                )
                
                logger.debug(f"Stored sentiment alert: {alert_id}")
                return str(alert_id)
                
        except Exception as e:
            logger.error(f"Failed to store sentiment alert: {e}")
            return None
    
    async def get_sentiment_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive sentiment analytics"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Get sentiment distribution
                sentiment_dist = await conn.fetch("""
                    SELECT sentiment, COUNT(*) as count
                    FROM sentiment_analysis_results 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY sentiment
                """ % days)
                
                # Get model performance stats
                model_stats = await conn.fetch("""
                    SELECT model_used, source, COUNT(*) as count,
                           AVG(confidence) as avg_confidence,
                           AVG(processing_time_ms) as avg_processing_time
                    FROM sentiment_analysis_results 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY model_used, source
                """ % days)
                
                # Get recent alerts by severity
                alert_stats = await conn.fetch("""
                    SELECT alert_type, severity, COUNT(*) as count
                    FROM sentiment_alerts 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY alert_type, severity
                """ % days)
                
                # Get hourly activity
                hourly_activity = await conn.fetch("""
                    SELECT DATE_TRUNC('hour', created_at) as hour, COUNT(*) as count
                    FROM sentiment_analysis_results 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY DATE_TRUNC('hour', created_at)
                    ORDER BY hour
                """ % days)
                
                # Get subreddit breakdown
                subreddit_stats = await conn.fetch("""
                    SELECT subreddit, sentiment, COUNT(*) as count,
                           AVG(compound_score) as avg_sentiment
                    FROM sentiment_analysis_results 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                      AND subreddit IS NOT NULL
                    GROUP BY subreddit, sentiment
                """ % days)
                
                return {
                    "sentiment_distribution": [dict(row) for row in sentiment_dist],
                    "model_performance": [dict(row) for row in model_stats],
                    "alert_statistics": [dict(row) for row in alert_stats],
                    "hourly_activity": [dict(row) for row in hourly_activity],
                    "subreddit_breakdown": [dict(row) for row in subreddit_stats],
                    "time_period_days": days,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get sentiment analytics: {e}")
            return {}
    
    async def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get active alerts with enhanced filtering"""
        try:
            async with self.connection_pool.acquire() as conn:
                alerts = await conn.fetch("""
                    SELECT id, content_id, content_text, content_type, alert_type, severity,
                           keywords_found, sentiment, confidence, compound_score,
                           subreddit, author, status, priority, created_at, updated_at
                    FROM sentiment_alerts 
                    WHERE status = 'active'
                    ORDER BY priority DESC, created_at DESC
                    LIMIT $1
                """, limit)
                
                return [dict(alert) for alert in alerts]
                
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    async def update_alert_status(self, alert_id: str, status: str, notes: Optional[str] = None, reviewed_by: Optional[str] = None) -> bool:
        """Update alert status with audit trail"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Update alert
                result = await conn.execute("""
                    UPDATE sentiment_alerts 
                    SET status = $1, notes = $2, reviewed_by = $3, 
                        reviewed_at = NOW(), updated_at = NOW()
                    WHERE id = $4
                """, status, notes, reviewed_by, uuid.UUID(alert_id))
                
                return result == "UPDATE 1"
                
        except Exception as e:
            logger.error(f"Failed to update alert status: {e}")
            return False
    
    async def store_system_metric(self, metric_name: str, metric_value: float, 
                                  category: str = "performance", source: str = "api",
                                  unit: Optional[str] = None, tags: Optional[Dict] = None):
        """Store system performance metric"""
        try:
            async with self.connection_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO system_metrics 
                    (metric_name, metric_category, metric_value, metric_unit, source_service, additional_tags)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, metric_name, category, metric_value, unit, source, tags)
                
        except Exception as e:
            logger.error(f"Failed to store system metric: {e}")
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data with enhanced retention policies"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Clean up old sentiment results (keep longer for analytics)
                deleted_sentiment = await conn.fetchval("""
                    DELETE FROM sentiment_analysis_results 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """ % (days_to_keep * 2))
                
                # Clean up old Reddit posts
                deleted_posts = await conn.fetchval("""
                    DELETE FROM reddit_posts 
                    WHERE scraped_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """ % days_to_keep)
                
                # Clean up resolved alerts (keep longer for audit trail)
                deleted_alerts = await conn.fetchval("""
                    DELETE FROM sentiment_alerts 
                    WHERE status IN ('resolved', 'false_positive') 
                      AND updated_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """ % (days_to_keep * 3))
                
                # Clean up old system metrics
                deleted_metrics = await conn.fetchval("""
                    DELETE FROM system_metrics 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """ % (days_to_keep // 2))
                
                # Clean up expired cache entries
                deleted_cache = await conn.fetchval("""
                    DELETE FROM analytics_cache 
                    WHERE expires_at < NOW()
                    RETURNING COUNT(*)
                """)
                
                logger.info(f"Cleanup completed: {deleted_sentiment} sentiment results, "
                           f"{deleted_posts} posts, {deleted_alerts} alerts, "
                           f"{deleted_metrics} metrics, {deleted_cache} cache entries deleted")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

class AsyncDataLoader:
    """Enhanced async data loader with batch processing and error handling"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.processing_queue = asyncio.Queue(maxsize=1000)
        self.is_running = False
        self.batch_size = 50
        self.batch_timeout = 5.0  # seconds
        self.retry_attempts = 3
        
        # Metrics
        self.items_processed = 0
        self.items_failed = 0
        self.batches_processed = 0
        
    async def start(self):
        """Start the async data loader"""
        self.is_running = True
        asyncio.create_task(self._process_queue())
        logger.info("Enhanced async data loader started")
    
    async def stop(self):
        """Stop the async data loader"""
        self.is_running = False
        # Process remaining items
        await self._process_remaining_items()
        logger.info("Enhanced async data loader stopped")
    
    async def queue_sentiment_result(self, sentiment_data: Dict[str, Any], post_data: Optional[Dict[str, Any]] = None):
        """Queue sentiment result for async processing"""
        try:
            await self.processing_queue.put({
                "type": "sentiment_result",
                "data": sentiment_data,
                "post_data": post_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "retry_count": 0
            })
        except asyncio.QueueFull:
            logger.warning("Processing queue is full, dropping sentiment result")
    
    async def queue_alert(self, alert_data: Dict[str, Any]):
        """Queue alert for async processing"""
        try:
            await self.processing_queue.put({
                "type": "alert",
                "data": alert_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "retry_count": 0
            })
        except asyncio.QueueFull:
            logger.warning("Processing queue is full, dropping alert")
    
    async def queue_metric(self, metric_name: str, metric_value: float, **kwargs):
        """Queue system metric for async processing"""
        try:
            await self.processing_queue.put({
                "type": "metric",
                "data": {
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    **kwargs
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "retry_count": 0
            })
        except asyncio.QueueFull:
            logger.warning("Processing queue is full, dropping metric")
    
    async def _process_queue(self):
        """Process queued items with batching and error handling"""
        batch = []
        last_batch_time = time.time()
        
        while self.is_running:
            try:
                # Wait for items with timeout
                try:
                    item = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                    batch.append(item)
                except asyncio.TimeoutError:
                    # Process batch if we have items and timeout reached
                    if batch and (time.time() - last_batch_time) > self.batch_timeout:
                        await self._process_batch(batch)
                        batch = []
                        last_batch_time = time.time()
                    continue
                
                # Process batch if it's full or timeout reached
                if (len(batch) >= self.batch_size or 
                    (time.time() - last_batch_time) > self.batch_timeout):
                    await self._process_batch(batch)
                    batch = []
                    last_batch_time = time.time()
                
            except Exception as e:
                logger.error(f"Error in queue processing loop: {e}")
                await asyncio.sleep(1)
        
        # Process final batch
        if batch:
            await self._process_batch(batch)
    
    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of items"""
        if not batch:
            return
        
        try:
            start_time = time.time()
            
            # Group items by type for efficient processing
            sentiment_items = [item for item in batch if item["type"] == "sentiment_result"]
            alert_items = [item for item in batch if item["type"] == "alert"]
            metric_items = [item for item in batch if item["type"] == "metric"]
            
            # Process each type
            if sentiment_items:
                await self._process_sentiment_batch(sentiment_items)
            
            if alert_items:
                await self._process_alert_batch(alert_items)
            
            if metric_items:
                await self._process_metric_batch(metric_items)
            
            processing_time = (time.time() - start_time) * 1000
            self.batches_processed += 1
            self.items_processed += len(batch)
            
            logger.debug(f"Processed batch of {len(batch)} items in {processing_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            self.items_failed += len(batch)
            
            # Retry failed items individually
            for item in batch:
                if item["retry_count"] < self.retry_attempts:
                    item["retry_count"] += 1
                    try:
                        await self.processing_queue.put(item)
                    except asyncio.QueueFull:
                        logger.warning("Queue full, dropping retry item")
    
    async def _process_sentiment_batch(self, items: List[Dict[str, Any]]):
        """Process a batch of sentiment results"""
        for item in items:
            try:
                sentiment_id = await self.db_manager.store_sentiment_result(item["data"])
                
                # Store associated post data if provided
                if item.get("post_data") and sentiment_id:
                    await self.db_manager.store_reddit_post(item["post_data"], sentiment_id)
                    
            except Exception as e:
                logger.error(f"Error processing sentiment item: {e}")
                raise
    
    async def _process_alert_batch(self, items: List[Dict[str, Any]]):
        """Process a batch of alerts"""
        for item in items:
            try:
                await self.db_manager.store_sentiment_alert(item["data"])
            except Exception as e:
                logger.error(f"Error processing alert item: {e}")
                raise
    
    async def _process_metric_batch(self, items: List[Dict[str, Any]]):
        """Process a batch of metrics"""
        for item in items:
            try:
                data = item["data"]
                await self.db_manager.store_system_metric(
                    data["metric_name"],
                    data["metric_value"],
                    data.get("category", "performance"),
                    data.get("source", "api"),
                    data.get("unit"),
                    data.get("tags")
                )
            except Exception as e:
                logger.error(f"Error processing metric item: {e}")
                raise
    
    async def _process_remaining_items(self):
        """Process remaining items in queue during shutdown"""
        remaining_items = []
        
        # Drain the queue
        while not self.processing_queue.empty():
            try:
                item = self.processing_queue.get_nowait()
                remaining_items.append(item)
            except asyncio.QueueEmpty:
                break
        
        if remaining_items:
            logger.info(f"Processing {len(remaining_items)} remaining items during shutdown")
            await self._process_batch(remaining_items)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "is_running": self.is_running,
            "queue_size": self.processing_queue.qsize(),
            "items_processed": self.items_processed,
            "items_failed": self.items_failed,
            "batches_processed": self.batches_processed,
            "success_rate": (
                self.items_processed / (self.items_processed + self.items_failed)
                if (self.items_processed + self.items_failed) > 0 else 1.0
            )
        }

# Global instances
db_manager = DatabaseManager()
data_loader = AsyncDataLoader(db_manager)
