-- Fix missing database views
-- Run this if the views weren't created during initial setup

-- Drop views if they exist (to recreate them)
DROP VIEW IF EXISTS posts_with_sentiment CASCADE;
DROP VIEW IF EXISTS comments_with_sentiment CASCADE;
DROP VIEW IF EXISTS alert_summary CASCADE;

-- Create posts_with_sentiment view
CREATE VIEW posts_with_sentiment AS
SELECT 
    p.id,
    p.post_id,
    p.title,
    p.subreddit,
    p.author,
    p.score,
    p.created_utc,
    p.scraped_at,
    s.sentiment,
    s.confidence,
    s.compound_score,
    s.model_used
FROM reddit_posts p
LEFT JOIN sentiment_analysis_results s ON p.sentiment_analysis_id = s.id;

-- Create comments_with_sentiment view
CREATE VIEW comments_with_sentiment AS
SELECT 
    c.id,
    c.comment_id,
    c.post_id,
    c.body,
    c.author,
    c.score,
    c.created_utc,
    c.scraped_at,
    s.sentiment,
    s.confidence,
    s.compound_score,
    s.model_used
FROM reddit_comments c
LEFT JOIN sentiment_analysis_results s ON c.sentiment_analysis_id = s.id;

-- Create alert_summary view
CREATE VIEW alert_summary AS
SELECT 
    alert_type,
    severity,
    content_type,
    subreddit,
    COUNT(*) as alert_count,
    MIN(created_at) as first_alert,
    MAX(created_at) as latest_alert
FROM sentiment_alerts 
WHERE status = 'active'
GROUP BY alert_type, severity, content_type, subreddit
ORDER BY alert_count DESC;

-- Test the views
SELECT 'Views created successfully!' as status;

-- Show what data exists
SELECT 
    'reddit_posts' as table_name, 
    COUNT(*) as row_count 
FROM reddit_posts
UNION ALL
SELECT 
    'reddit_comments' as table_name, 
    COUNT(*) as row_count 
FROM reddit_comments
UNION ALL
SELECT 
    'sentiment_analysis_results' as table_name, 
    COUNT(*) as row_count 
FROM sentiment_analysis_results
UNION ALL
SELECT 
    'sentiment_alerts' as table_name, 
    COUNT(*) as row_count 
FROM sentiment_alerts;
