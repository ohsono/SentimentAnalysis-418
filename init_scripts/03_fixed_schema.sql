-- UCLA Sentiment Analysis Database Schema - Fixed Version
-- Corrects table name mismatches and ensures compatibility

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ========================================
-- DROP EXISTING TABLES (Clean slate)
-- ========================================

DROP MATERIALIZED VIEW IF EXISTS dashboard_analytics CASCADE;
DROP TABLE IF EXISTS analytics_cache CASCADE;
DROP TABLE IF EXISTS system_metrics CASCADE;
DROP TABLE IF EXISTS sentiment_alerts CASCADE;
DROP TABLE IF EXISTS sentiment_analysis_results CASCADE;
DROP TABLE IF EXISTS reddit_content CASCADE;
DROP TABLE IF EXISTS reddit_posts CASCADE;
DROP TABLE IF EXISTS reddit_comments CASCADE;
DROP TABLE IF EXISTS batch_processing CASCADE;
DROP TABLE IF EXISTS alert_events CASCADE;
DROP TABLE IF EXISTS sentiment_analysis CASCADE;

-- ========================================
-- CREATE CORE TABLES
-- ========================================

-- 1. Sentiment Analysis Results Table (Main analysis table)
CREATE TABLE sentiment_analysis_results (
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

-- 2. Sentiment Alerts Table (For alert functionality)
CREATE TABLE sentiment_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id VARCHAR(50) NOT NULL,
    content_text TEXT NOT NULL,
    
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    priority INTEGER DEFAULT 0,
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

-- 3. Reddit Posts Table
CREATE TABLE reddit_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reddit_id VARCHAR(50) NOT NULL UNIQUE,
    
    -- Post content
    title TEXT NOT NULL,
    body TEXT,
    author VARCHAR(100),
    subreddit VARCHAR(100) NOT NULL,
    
    -- Reddit metadata
    score INTEGER DEFAULT 0,
    upvote_ratio FLOAT,
    num_comments INTEGER DEFAULT 0,
    permalink TEXT,
    url TEXT,
    
    -- Processing status
    sentiment_analyzed BOOLEAN DEFAULT FALSE,
    alert_checked BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reddit_created_utc TIMESTAMPTZ NOT NULL
);

-- 4. Reddit Comments Table
CREATE TABLE reddit_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reddit_id VARCHAR(50) NOT NULL UNIQUE,
    post_id VARCHAR(50) NOT NULL,
    parent_id VARCHAR(50),
    
    -- Comment content
    body TEXT NOT NULL,
    author VARCHAR(100),
    subreddit VARCHAR(100) NOT NULL,
    
    -- Reddit metadata
    score INTEGER DEFAULT 0,
    is_submitter BOOLEAN DEFAULT FALSE,
    
    -- Processing status
    sentiment_analyzed BOOLEAN DEFAULT FALSE,
    alert_checked BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reddit_created_utc TIMESTAMPTZ NOT NULL
);

-- 5. System Metrics Table
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    
    -- Additional context
    source_service VARCHAR(50) NOT NULL,
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

-- 7. Batch Processing Jobs Table
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

-- ========================================
-- CREATE INDEXES FOR PERFORMANCE
-- ========================================

-- Sentiment Analysis Results Indexes
CREATE INDEX idx_sentiment_analysis_text_hash ON sentiment_analysis_results(text_hash);
CREATE INDEX idx_sentiment_analysis_sentiment ON sentiment_analysis_results(sentiment);
CREATE INDEX idx_sentiment_analysis_created_at ON sentiment_analysis_results(created_at);
CREATE INDEX idx_sentiment_analysis_created_source ON sentiment_analysis_results(created_at, source);
CREATE INDEX idx_sentiment_analysis_subreddit ON sentiment_analysis_results(subreddit);

-- Sentiment Alerts Indexes
CREATE INDEX idx_alerts_severity_status ON sentiment_alerts(severity, status, created_at);
CREATE INDEX idx_alerts_alert_type ON sentiment_alerts(alert_type);
CREATE INDEX idx_alerts_created_at ON sentiment_alerts(created_at);

-- Reddit Posts Indexes
CREATE INDEX idx_reddit_posts_reddit_id ON reddit_posts(reddit_id);
CREATE INDEX idx_reddit_posts_subreddit_created ON reddit_posts(subreddit, reddit_created_utc);
CREATE INDEX idx_reddit_posts_sentiment_analyzed ON reddit_posts(sentiment_analyzed);

-- Reddit Comments Indexes
CREATE INDEX idx_reddit_comments_reddit_id ON reddit_comments(reddit_id);
CREATE INDEX idx_reddit_comments_post_id ON reddit_comments(post_id);
CREATE INDEX idx_reddit_comments_subreddit ON reddit_comments(subreddit);

-- System Metrics Indexes
CREATE INDEX idx_system_metrics_created_at ON system_metrics(created_at);
CREATE INDEX idx_system_metrics_category ON system_metrics(metric_category);

-- Analytics Cache Indexes
CREATE INDEX idx_analytics_cache_expires_at ON analytics_cache(expires_at);

-- ========================================
-- CREATE FUNCTIONS FOR ANALYTICS
-- ========================================

-- Function to get sentiment summary
CREATE OR REPLACE FUNCTION get_sentiment_summary(days_back INTEGER DEFAULT 7)
RETURNS TABLE(
    sentiment TEXT,
    count BIGINT,
    avg_confidence NUMERIC,
    avg_compound_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.sentiment,
        COUNT(*) as count,
        ROUND(AVG(s.confidence), 3) as avg_confidence,
        ROUND(AVG(s.compound_score), 3) as avg_compound_score
    FROM sentiment_analysis_results s
    WHERE s.created_at >= NOW() - INTERVAL '1 day' * days_back
    GROUP BY s.sentiment
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get alert statistics
CREATE OR REPLACE FUNCTION get_alert_statistics(days_back INTEGER DEFAULT 7)
RETURNS TABLE(
    alert_type TEXT,
    severity TEXT,
    count BIGINT,
    avg_priority NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.alert_type,
        a.severity,
        COUNT(*) as count,
        ROUND(AVG(a.priority), 1) as avg_priority
    FROM sentiment_alerts a
    WHERE a.created_at >= NOW() - INTERVAL '1 day' * days_back
    GROUP BY a.alert_type, a.severity
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- CREATE MATERIALIZED VIEW
-- ========================================

CREATE MATERIALIZED VIEW dashboard_analytics AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    source,
    sentiment,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence,
    AVG(compound_score) as avg_compound_score,
    AVG(processing_time_ms) as avg_processing_time
FROM sentiment_analysis_results 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', created_at), source, sentiment
ORDER BY hour DESC;

-- Create unique index on materialized view
CREATE UNIQUE INDEX idx_dashboard_analytics_unique
    ON dashboard_analytics(hour, source, sentiment);

-- Function to refresh analytics
CREATE OR REPLACE FUNCTION refresh_dashboard_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_analytics;
    -- Update analytics cache timestamp
    INSERT INTO analytics_cache (cache_key, cache_data, expires_at)
    VALUES ('dashboard_last_refresh', 
            json_build_object('timestamp', NOW()),
            NOW() + INTERVAL '1 hour')
    ON CONFLICT (cache_key) 
    DO UPDATE SET 
        cache_data = EXCLUDED.cache_data,
        expires_at = EXCLUDED.expires_at,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- SUCCESS MESSAGE
-- ========================================

DO $$
BEGIN
    RAISE NOTICE '✅ UCLA Sentiment Analysis Database Schema Created Successfully!';
    RAISE NOTICE '📊 Tables: sentiment_analysis_results, sentiment_alerts, reddit_posts, reddit_comments';
    RAISE NOTICE '📈 Additional: system_metrics, analytics_cache, batch_processing';
    RAISE NOTICE '🔍 Views: dashboard_analytics (materialized)';
    RAISE NOTICE '⚡ Functions: get_sentiment_summary(), get_alert_statistics()';
END $$;
