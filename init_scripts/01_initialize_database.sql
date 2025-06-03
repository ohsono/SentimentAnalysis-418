-- UCLA Sentiment Analysis Database Initialization Script
-- Creates initial database structure and sample data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create functions for analytics
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

-- Create function for alert statistics
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

-- Create materialized view for dashboard analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_analytics AS
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

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboard_analytics_unique
    ON dashboard_analytics(hour, source, sentiment);

-- Create function to refresh analytics
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

-- Insert sample configuration data
INSERT INTO analytics_cache (cache_key, cache_data, expires_at)
VALUES 
    ('system_config', 
     json_build_object(
         'version', '2.0.0',
         'failsafe_enabled', true,
         'vader_fallback', true,
         'max_llm_failures', 3
     ),
     NOW() + INTERVAL '1 year'
    ),
    ('model_config',
     json_build_object(
         'default_model', 'distilbert-sentiment',
         'available_models', json_build_array(
             'distilbert-sentiment',
             'twitter-roberta',
             'bert-sentiment'
         ),
         'model_service_enabled', true
     ),
     NOW() + INTERVAL '1 day'
    )
ON CONFLICT (cache_key) DO NOTHING;

-- Create sample alert keywords for reference
INSERT INTO analytics_cache (cache_key, cache_data, expires_at)
VALUES (
    'alert_keywords',
    json_build_object(
        'mental_health', json_build_array('depressed', 'depression', 'suicide', 'kill myself', 'worthless', 'hopeless'),
        'stress', json_build_array('overwhelmed', 'stressed', 'anxious', 'panic', 'breakdown', 'can''t handle'),
        'academic', json_build_array('failing', 'dropped out', 'academic probation', 'expelled', 'flunking'),
        'harassment', json_build_array('bullied', 'harassed', 'threatened', 'stalked', 'discriminated')
    ),
    NOW() + INTERVAL '1 month'
)
ON CONFLICT (cache_key) DO NOTHING;

-- Log initialization
INSERT INTO system_metrics (metric_name, metric_category, metric_value, source_service)
VALUES ('database_initialized', 'system', 1, 'postgresql');

-- Print completion message
DO $$
BEGIN
    RAISE NOTICE 'UCLA Sentiment Analysis database initialized successfully!';
    RAISE NOTICE 'Created tables, indexes, functions, and sample data.';
    RAISE NOTICE 'Materialized view created for dashboard analytics.';
END $$;



-- Create indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sentiment_analysis_text_hash 
    ON sentiment_analysis_results(text_hash);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sentiment_analysis_created_source
    ON sentiment_analysis_results(created_at, source);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_severity_status
    ON sentiment_alerts(severity, status, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reddit_posts_subreddit_created
    ON reddit_posts(subreddit, reddit_created_utc);
