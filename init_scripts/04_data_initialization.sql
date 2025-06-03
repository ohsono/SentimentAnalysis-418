-- UCLA Sentiment Analysis Database - Data Initialization
-- Insert sample configuration and test data with correct table names

-- ========================================
-- INSERT SAMPLE CONFIGURATION DATA
-- ========================================

-- Insert system configuration
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

-- ========================================
-- INSERT TEST DATA
-- ========================================

-- Test data for sentiment_analysis_results
INSERT INTO sentiment_analysis_results (
    text, text_hash, sentiment, confidence, compound_score, probabilities,
    model_used, model_name, source, processing_time_ms,
    subreddit, category, author
) VALUES 
(
    'This is a test sentiment analysis for UCLA campus life!',
    encode(sha256('test_text_1'::bytea), 'hex'),
    'positive',
    0.85,
    0.7,
    '{"positive": 0.85, "negative": 0.1, "neutral": 0.05}'::jsonb,
    'distilbert-sentiment',
    'DistilBERT Sentiment Model',
    'worker-service',
    150.5,
    'UCLA',
    'campus_life',
    'test_user'
),
(
    'I love studying at UCLA, the campus is beautiful!',
    encode(sha256('test_text_2'::bytea), 'hex'),
    'positive',
    0.92,
    0.8,
    '{"positive": 0.92, "negative": 0.03, "neutral": 0.05}'::jsonb,
    'distilbert-sentiment',
    'DistilBERT Sentiment Model',
    'worker-service',
    145.2,
    'UCLA',
    'campus_life',
    'happy_student'
),
(
    'Finals week is so stressful, I can barely handle it',
    encode(sha256('test_text_3'::bytea), 'hex'),
    'negative',
    0.88,
    -0.6,
    '{"positive": 0.05, "negative": 0.88, "neutral": 0.07}'::jsonb,
    'distilbert-sentiment',
    'DistilBERT Sentiment Model',
    'worker-service',
    155.8,
    'UCLA',
    'academic',
    'stressed_student'
);

-- Test data for reddit_posts
INSERT INTO reddit_posts (
    reddit_id, title, body, author, subreddit,
    score, upvote_ratio, num_comments, reddit_created_utc
) VALUES 
(
    'test_post_123',
    'Test UCLA Post',
    'This is a test post about UCLA campus life',
    'test_user',
    'UCLA',
    10,
    0.9,
    5,
    CURRENT_TIMESTAMP - INTERVAL '1 hour'
),
(
    'test_post_456',
    'UCLA Study Tips',
    'Here are some great study tips for UCLA students during finals',
    'helpful_student',
    'UCLA',
    25,
    0.95,
    8,
    CURRENT_TIMESTAMP - INTERVAL '2 hours'
);

-- Test data for reddit_comments
INSERT INTO reddit_comments (
    reddit_id, post_id, body, author, subreddit, score, reddit_created_utc
) VALUES 
(
    'test_comment_789',
    'test_post_123',
    'Great point about UCLA! I totally agree.',
    'commenter_user',
    'UCLA',
    3,
    CURRENT_TIMESTAMP - INTERVAL '30 minutes'
),
(
    'test_comment_101',
    'test_post_456',
    'Thanks for these tips! Very helpful for finals.',
    'grateful_student',
    'UCLA',
    5,
    CURRENT_TIMESTAMP - INTERVAL '15 minutes'
);

-- Test data for sentiment_alerts
INSERT INTO sentiment_alerts (
    content_id, content_text, alert_type, severity, priority,
    keywords_found, sentiment, confidence, compound_score,
    subreddit, author
) VALUES (
    'test_alert_123',
    'I''m feeling really stressed about finals',
    'stress',
    'medium',
    2,
    '["stressed", "finals"]'::jsonb,
    'negative',
    0.8,
    -0.6,
    'UCLA',
    'stressed_student'
);

-- Test data for system_metrics
INSERT INTO system_metrics (
    metric_name, metric_category, metric_value, source_service, details
) VALUES 
(
    'sentiment_analysis_endpoint_response_time',
    'api_performance',
    125.5,
    'gateway-api',
    '{"endpoint": "/api/v1/sentiment", "method": "POST"}'::jsonb
),
(
    'model_availability',
    'model_service_health',
    1.0,
    'model-service',
    '{"status": "healthy", "uptime": 3600}'::jsonb
),
(
    'database_initialized',
    'system',
    1,
    'postgresql',
    '{"tables_created": 7, "indexes_created": 15}'::jsonb
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
    'distilbert-sentiment',
    'worker-service',
    15000.0,
    150.0,
    CURRENT_TIMESTAMP,
    '{"test": true, "batch_type": "initial_test_run"}'::jsonb
);

-- Log initialization
INSERT INTO system_metrics (metric_name, metric_category, metric_value, source_service)
VALUES ('database_data_initialized', 'system', 1, 'postgresql');

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Show all tables and their row counts
DO $$
DECLARE
    table_name TEXT;
    row_count INTEGER;
BEGIN
    RAISE NOTICE '📊 Database Table Summary:';
    
    FOR table_name IN 
        SELECT t.table_name 
        FROM information_schema.tables t 
        WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', table_name) INTO row_count;
        RAISE NOTICE '   % - % rows', table_name, row_count;
    END LOOP;
END $$;

-- Test some sample queries
SELECT 
    sentiment,
    COUNT(*) as count,
    ROUND(AVG(confidence), 3) as avg_confidence
FROM sentiment_analysis_results 
GROUP BY sentiment;

-- ========================================
-- SUCCESS MESSAGE
-- ========================================

DO $$
BEGIN
    RAISE NOTICE '✅ UCLA Sentiment Analysis Database Data Initialized Successfully!';
    RAISE NOTICE '📝 Configuration data inserted into analytics_cache';
    RAISE NOTICE '🧪 Test data inserted into all tables';
    RAISE NOTICE '📊 Sample alert keywords and system configs created';
    RAISE NOTICE '🚀 Database is ready for Reddit scraping and sentiment analysis!';
END $$;
