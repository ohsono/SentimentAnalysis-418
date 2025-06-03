#!/usr/bin/env python3

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import os

Base = declarative_base()

class SentimentAnalysis(Base):
    """
    Store individual sentiment analysis results
    """
    __tablename__ = 'sentiment_analysis'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    text_hash = Column(String(64), nullable=False, index=True)  # For deduplication
    sentiment = Column(String(20), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    compound_score = Column(Float, nullable=False)
    probabilities = Column(JSON)  # Store positive, negative, neutral probabilities
    
    # Model information
    model_used = Column(String(100), nullable=False, index=True)
    model_name = Column(String(200))
    source = Column(String(50), nullable=False, index=True)  # 'model-service', 'vader-fallback', etc.
    
    # Processing metadata
    processing_time_ms = Column(Float)
    batch_id = Column(UUID(as_uuid=True), index=True)  # For batch processing
    
    # Content metadata
    subreddit = Column(String(100), index=True)
    post_id = Column(String(50), index=True)
    comment_id = Column(String(50), index=True)
    author = Column(String(100), index=True)
    category = Column(String(50), index=True)  # academic, campus_life, sports, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    content_created_at = Column(DateTime(timezone=True), index=True)  # Original content timestamp
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_sentiment_created_at', 'sentiment', 'created_at'),
        Index('idx_model_source', 'model_used', 'source'),
        Index('idx_subreddit_created', 'subreddit', 'created_at'),
        Index('idx_category_sentiment', 'category', 'sentiment'),
    )

class BatchProcessing(Base):
    """Track batch processing jobs"""
    __tablename__ = 'batch_processing'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    total_texts = Column(Integer, nullable=False)
    processed_texts = Column(Integer, default=0)
    failed_texts = Column(Integer, default=0)
    
    status = Column(String(20), nullable=False, default='processing', index=True)  # processing, completed, failed
    model_used = Column(String(100), nullable=False)
    source = Column(String(50), nullable=False)
    
    total_processing_time_ms = Column(Float)
    average_time_per_text_ms = Column(Float)
    
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    
    error_message = Column(Text)
    job_metadata = Column(JSON)  # Additional processing information

class RedditContent(Base):
    """
    Store Reddit posts and comments
    """
    __tablename__ = 'reddit_content'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(String(50), nullable=False, unique=True, index=True)  # Reddit post/comment ID
    content_type = Column(String(20), nullable=False, index=True)  # 'post' or 'comment'
    
    # Content data
    title = Column(Text)  # For posts
    body = Column(Text, nullable=False)
    author = Column(String(100), index=True)
    subreddit = Column(String(100), nullable=False, index=True)
    
    # Reddit metadata
    score = Column(Integer, default=0)
    upvote_ratio = Column(Float)
    num_comments = Column(Integer, default=0)
    parent_id = Column(String(50), index=True)  # For comments
    
    # Processing status
    sentiment_analyzed = Column(Boolean, default=False, index=True)
    alert_checked = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reddit_created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_subreddit_created', 'subreddit', 'reddit_created_at'),
        Index('idx_sentiment_analyzed', 'sentiment_analyzed', 'created_at'),
        Index('idx_content_type_subreddit', 'content_type', 'subreddit'),
    )

class AlertEvents(Base):
    """
    Store alert events for mental health and safety monitoring
    """
    __tablename__ = 'alert_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(String(50), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    
    alert_type = Column(String(50), nullable=False, index=True)  # stress, mental_health, harassment
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    keywords_found = Column(JSON)  # List of trigger keywords
    
    # Sentiment context
    sentiment = Column(String(20), index=True)
    confidence = Column(Float)
    compound_score = Column(Float)
    
    # Content metadata
    subreddit = Column(String(100), index=True)
    author = Column(String(100), index=True)
    
    # Alert status
    status = Column(String(20), default='active', index=True)  # active, reviewed, resolved
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_alert_type_severity', 'alert_type', 'severity'),
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_subreddit_severity', 'subreddit', 'severity'),
    )

class SystemMetrics(Base):
    """Store system performance and health metrics"""
    __tablename__ = 'system_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(String(50), nullable=False, index=True)  # api_response_time, model_service_health, etc.
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    
    # Additional context
    source = Column(String(50), nullable=False, index=True)  # api, model-service, database
    details = Column(JSON)  # Additional metric details
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_metric_type_created', 'metric_type', 'created_at'),
        Index('idx_source_metric', 'source', 'metric_name'),
    )

class AnalyticsCache(Base):
    """Cache computed analytics for dashboard performance"""
    __tablename__ = 'analytics_cache'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(200), nullable=False, unique=True, index=True)
    cache_data = Column(JSON, nullable=False)
    
    # Cache metadata
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    computation_time_ms = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# Database configuration
def get_database_url():
    """Get database URL from environment or default"""
    return os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost:5432/ucla_sentiment'
    )

def create_database_engine():
    """Create database engine with connection pooling"""
    database_url = get_database_url()
    
    engine = create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
    )
    
    return engine

def create_tables(engine):
    """
    Create all tables
    """
    Base.metadata.create_all(engine)

def get_session_maker(engine):
    """
    Get session maker for database operations
    """
    return sessionmaker(bind=engine)

# Global database setup
engine = create_database_engine()
SessionLocal = get_session_maker(engine)

def get_db_session():
    """Get database session (for dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
