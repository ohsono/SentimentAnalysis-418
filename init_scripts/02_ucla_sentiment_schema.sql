-- UCLA Sentiment Analysis Database Schema
-- PostgreSQL Script to create tables, indexes, and test data

-- ========================================
-- DROP EXISTING TABLES (Clean slate)
-- ========================================

DROP TABLE IF EXISTS analytics_cache CASCADE;
DROP TABLE IF EXISTS system_metrics CASCADE;
DROP TABLE IF EXISTS alert_events CASCADE;
DROP TABLE IF EXISTS reddit_content CASCADE;
DROP TABLE IF EXISTS batch_processing CASCADE;
DROP TABLE IF EXISTS sentiment_analysis CASCADE;

-- ========================================
-- CREATE TABLES
-- ========================================

-- 1. Sentiment Analysis Results Table
CREATE TABLE sentiment_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    compound_score FLOAT NOT NULL,
    probabilities JSONB,
    
    -- Model information
    model_used VARCHAR(100) NOT NULL,
    model_name VARCHAR(200),
    source VARCHAR(50) NOT NULL,
    
    -- Processing metadata
    processing_time_ms FLOAT,
    batch_id UUID,
    
    -- Content metadata
    subreddit VARCHAR(100),
    post_id VARCHAR(50),
    comment_id VARCHAR(50),
    author VARCHAR(100),
    category VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    content_created_at TIMESTAMPTZ
);

-- 2. Batch Processing Jobs Table
CREATE TABLE batch_processing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL UNIQUE,
    total_texts INTEGER NOT NULL,
    processed_texts INTEGER DEFAULT 0,
    failed_texts INTEGER DEFAULT 0,
    
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    model_used VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,
    
    total_processing_time_ms FLOAT,
    average_time_per_text_ms FLOAT,
    
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    
    error_message TEXT,
    processing_metadata JSONB
);

-- 3. Reddit Content Table
CREATE TABLE reddit_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id VARCHAR(50) NOT NULL UNIQUE,
    content_type VARCHAR(20) NOT NULL,
    
    -- Content data
    title TEXT,
    body TEXT NOT NULL,
    author VARCHAR(100),
    subreddit VARCHAR(100) NOT NULL,
    
    -- Reddit metadata
    score INTEGER DEFAULT 0,
    upvote_ratio FLOAT,
    num_comments INTEGER DEFAULT 0,
    parent_id VARCHAR(50),
    
    -- Processing status
    sentiment_analyzed BOOLEAN DEFAULT FALSE,
    alert_checked BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reddit_created_at TIMESTAMPTZ NOT NULL
);

-- 4. Alert Events Table
CREATE TABLE alert_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id VARCHAR(50) NOT NULL,
    content_text TEXT NOT NULL,
    
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    keywords_found JSONB,
    
    -- Sentiment context
    sentiment VARCHAR(20),
    confidence FLOAT,
    compound_score FLOAT,
    
    -- Content metadata
    subreddit VARCHAR(100),
    author VARCHAR(100),
    
    -- Alert status
    status VARCHAR(20) DEFAULT 'active',
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. System Metrics Table
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    
    -- Additional context
    source VARCHAR(50) NOT NULL,
    details JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. Analytics Cache Table
CREATE TABLE analytics_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(200) NOT NULL UNIQUE,
    cache_data JSONB NOT NULL,
    
    -- Cache metadata
    expires_at TIMESTAMPTZ NOT NULL,
    computation_time_ms FLOAT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CREATE INDEXES
-- ========================================

-- Sentiment Analysis Indexes
CREATE INDEX idx_sentiment_analysis_text_hash ON sentiment_analysis(text_hash);
CREATE INDEX idx_sentiment_analysis_sentiment ON sentiment_analysis(sentiment);
CREATE INDEX idx_sentiment_analysis_model_used ON sentiment_analysis(model_used);
CREATE INDEX idx_sentiment_analysis_source ON sentiment_analysis(source);
CREATE INDEX idx_sentiment_analysis_batch_id ON sentiment_analysis(batch_id);
CREATE INDEX idx_sentiment_analysis_subreddit ON sentiment_analysis(subreddit);
CREATE INDEX idx_sentiment_analysis_post_id ON sentiment_analysis(post_id);
CREATE INDEX idx_sentiment_analysis_comment_id ON sentiment_analysis(comment_id);
CREATE INDEX idx_sentiment_analysis_author ON sentiment_analysis(author);
CREATE INDEX idx_sentiment_analysis_category ON sentiment_analysis(category);
CREATE INDEX idx_sentiment_analysis_created_at ON sentiment_analysis(created_at);
CREATE INDEX idx_sentiment_analysis_content_created_at ON sentiment_analysis(content_created_at);
CREATE INDEX idx_sentiment_created_at ON sentiment_analysis(sentiment, created_at);
CREATE INDEX idx_model_source ON sentiment_analysis(model_used, source);
CREATE INDEX idx_subreddit_created ON sentiment_analysis(subreddit, created_at);
CREATE INDEX idx_category_sentiment ON sentiment_analysis(category, sentiment);

-- Batch Processing Indexes
CREATE INDEX idx_batch_processing_batch_id ON batch_processing(batch_id);
CREATE INDEX idx_batch_processing_status ON batch_processing(status);

-- Reddit Content Indexes
CREATE INDEX idx_reddit_content_content_id ON reddit_content(content_id);
CREATE INDEX idx_reddit_content_content_type ON reddit_content(content_type);
CREATE INDEX idx_reddit_content_author ON reddit_content(author);
CREATE INDEX idx_reddit_content_subreddit ON reddit_content(subreddit);
CREATE INDEX idx_reddit_content_parent_id ON reddit_content(parent_id);
CREATE INDEX idx_reddit_content_sentiment_analyzed ON reddit_content(sentiment_analyzed);
CREATE INDEX idx_reddit_content_alert_checked ON reddit_content(alert_checked);
CREATE INDEX idx_reddit_content_reddit_created_at ON reddit_content(reddit_created_at);
CREATE INDEX idx_reddit_subreddit_created ON reddit_content(subreddit, reddit_created_at);
CREATE INDEX idx_reddit_sentiment_analyzed ON reddit_content(sentiment_analyzed, created_at);
CREATE INDEX idx_reddit_content_type_subreddit ON reddit_content(content_type, subreddit);

-- Alert Events Indexes
CREATE INDEX idx_alert_events_content_id ON alert_events(content_id);
CREATE INDEX idx_alert_events_alert_type ON alert_events(alert_type);
CREATE INDEX idx_alert_events_severity ON alert_events(severity);
CREATE INDEX idx_alert_events_sentiment ON alert_events(sentiment);
CREATE INDEX idx_alert_events_subreddit ON alert_events(subreddit);
CREATE INDEX idx_alert_events_author ON alert_events(author);
CREATE INDEX idx_alert_events_status ON alert_events(status);
CREATE INDEX idx_alert_events_created_at ON alert_events(created_at);
CREATE INDEX idx_alert_type_severity ON alert_events(alert_type, severity);
CREATE INDEX idx_alert_status_created ON alert_events(status, created_at);
CREATE INDEX idx_alert_subreddit_severity ON alert_events(subreddit, severity);

-- System Metrics Indexes
CREATE INDEX idx_system_metrics_metric_type ON system_metrics(metric_type);
CREATE INDEX idx_system_metrics_metric_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_source ON system_metrics(source);
CREATE INDEX idx_system_metrics_created_at ON system_metrics(created_at);
CREATE INDEX idx_metric_type_created ON system_metrics(metric_type, created_at);
CREATE INDEX idx_source_metric ON system_metrics(source, metric_name);

-- Analytics Cache Indexes
CREATE INDEX idx_analytics_cache_cache_key ON analytics_cache(cache_key);
CREATE INDEX idx_analytics_cache_expires_at ON analytics_cache(expires_at);

-- ========================================
-- INSERT TEST DATA
-- ========================================

-- Test data for sentiment_analysis
INSERT INTO sentiment_analysis (
    text, text_hash, sentiment, confidence, compound_score, probabilities,
    model_used, model_name, source, processing_time_ms,
    subreddit, category, author
) VALUES 
(
    'This is a test sentiment analysis for UCLA campus life!',
    'test_hash_123',
    'positive',
    0.85,
    0.7,
    '{"positive": 0.85, "negative": 0.1, "neutral": 0.05}'::jsonb,
    'test_model_v1',
    'Test Sentiment Model',
    'test-service',
    150.5,
    'UCLA',
    'campus_life',
    'test_user'
),
(
    'I love studying at UCLA, the campus is beautiful!',
    'test_hash_456',
    'positive',
    0.92,
    0.8,
    '{"positive": 0.92, "negative": 0.03, "neutral": 0.05}'::jsonb,
    'test_model_v1',
    'Test Sentiment Model',
    'test-service',
    145.2,
    'UCLA',
    'campus_life',
    'happy_student'
),
(
    'Finals week is so stressful, I can barely handle it',
    'test_hash_789',
    'negative',
    0.88,
    -0.6,
    '{"positive": 0.05, "negative": 0.88, "neutral": 0.07}'::jsonb,
    'test_model_v1',
    'Test Sentiment Model',
    'test-service',
    155.8,
    'UCLA',
    'academic',
    'stressed_student'
);

-- Test data for reddit_content
INSERT INTO reddit_content (
    content_id, content_type, title, body, author, subreddit,
    score, upvote_ratio, num_comments, reddit_created_at
) VALUES 
(
    'test_post_123',
    'post',
    'Test UCLA Post',
    'This is a test post about UCLA campus life',
    'test_user',
    'UCLA',
    10,
    0.9,
    5,
    CURRENT_TIMESTAMP
),
(
    'test_comment_456',
    'comment',
    NULL,
    'Great point about UCLA! I totally agree.',
    'commenter_user',
    'UCLA',
    3,
    NULL,
    0,
    CURRENT_TIMESTAMP
);

-- Test data for batch_processing
INSERT INTO batch_processing (
    batch_id, total_texts, processed_texts, failed_texts,
    status, model_used, source, total_processing_time_ms,
    average_time_per_text_ms, completed_at, processing_metadata
) VALUES (
    gen_random_uuid(),
    100,
    95,
    5,
    'completed',
    'test_model_v1',
    'test-service',
    15000.0,
    150.0,
    CURRENT_TIMESTAMP,
    '{"test": true, "batch_type": "test_run"}'::jsonb
);

-- Test data for alert_events
INSERT INTO alert_events (
    content_id, content_text, alert_type, severity,
    keywords_found, sentiment, confidence, compound_score,
    subreddit, author
) VALUES (
    'test_alert_123',
    'I''m feeling really stressed about finals',
    'stress',
    'medium',
    '["stressed", "finals"]'::jsonb,
    'negative',
    0.8,
    -0.6,
    'UCLA',
    'stressed_student'
);

-- Test data for system_metrics
INSERT INTO system_metrics (
    metric_type, metric_name, metric_value, source, details
) VALUES 
(
    'api_response_time',
    'sentiment_analysis_endpoint',
    125.5,
    'api',
    '{"endpoint": "/api/v1/sentiment", "method": "POST"}'::jsonb
),
(
    'model_service_health',
    'model_availability',
    1.0,
    'model-service',
    '{"status": "healthy", "uptime": 3600}'::jsonb
);

-- Test data for analytics_cache
INSERT INTO analytics_cache (
    cache_key, cache_data, expires_at, computation_time_ms
) VALUES (
    'test_analytics_hourly_2024',
    '{"total_posts": 150, "positive_sentiment": 0.6}'::jsonb,
    CURRENT_TIMESTAMP + INTERVAL '1 hour',
    500.0
);

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Show all tables
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_name = t.table_name AND table_schema = 'public') as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY table_name;

-- Show row counts for each table
SELECT 
    'sentiment_analysis' as table_name, 
    COUNT(*) as row_count 
FROM sentiment_analysis
UNION ALL
SELECT 
    'reddit_content' as table_name, 
    COUNT(*) as row_count 
FROM reddit_content
UNION ALL
SELECT 
    'batch_processing' as table_name, 
    COUNT(*) as row_count 
FROM batch_processing
UNION ALL
SELECT 
    'alert_events' as table_name, 
    COUNT(*) as row_count 
FROM alert_events
UNION ALL
SELECT 
    'system_metrics' as table_name, 
    COUNT(*) as row_count 
FROM system_metrics
UNION ALL
SELECT 
    'analytics_cache' as table_name, 
    COUNT(*) as row_count 
FROM analytics_cache;

-- Show indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Test some sample queries
SELECT 
    sentiment,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence
FROM sentiment_analysis 
GROUP BY sentiment;

SELECT 
    subreddit,
    COUNT(*) as post_count
FROM reddit_content 
GROUP BY subreddit;

SELECT 
    alert_type,
    severity,
    COUNT(*) as alert_count
FROM alert_events 
GROUP BY alert_type, severity;

-- ========================================
-- SUCCESS MESSAGE
-- ========================================

SELECT 'UCLA Sentiment Analysis Database Setup Complete!' as status;
