-- UCLA Sentiment Analysis Database Schema
-- PostgreSQL database schema for Reddit scraping and sentiment analysis
-- 
-- Usage:
--   psql -h localhost -U sentiment_user -d sentiment_db -f database_schema.sql
--
-- Or from within psql:
--   \i database_schema.sql

-- =============================================================================
-- DROP TABLES (Uncomment if you need to reset the database)
-- =============================================================================

-- DROP TABLE IF EXISTS sentiment_alerts CASCADE;
-- DROP TABLE IF EXISTS reddit_comments CASCADE; 
-- DROP TABLE IF EXISTS reddit_posts CASCADE;
-- DROP TABLE IF EXISTS sentiment_analysis_results CASCADE;

-- =============================================================================
-- CREATE TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Sentiment Analysis Results Table
-- Stores all sentiment analysis results with deduplication support
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentiment_analysis_results (
    id SERIAL PRIMARY KEY,
    text_content TEXT NOT NULL,                          -- The text that was analyzed
    text_hash VARCHAR(64) NOT NULL,                      -- SHA256 hash for deduplication
    sentiment VARCHAR(20) NOT NULL,                      -- 'positive', 'negative', 'neutral'
    confidence REAL NOT NULL,                            -- Confidence score (0.0 to 1.0)
    compound_score REAL NOT NULL,                        -- VADER compound score (-1.0 to 1.0)
    probabilities JSONB,                                 -- Model probability scores
    processing_time_ms REAL NOT NULL,                    -- Time taken to analyze (milliseconds)
    model_used VARCHAR(100) NOT NULL,                    -- Model identifier
    model_name VARCHAR(200),                             -- Human-readable model name
    source VARCHAR(50) NOT NULL,                         -- 'model-service', 'vader-fallback', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),   -- When the analysis was performed
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()    -- Last update timestamp
);

-- Add indexes for sentiment_analysis_results
CREATE INDEX IF NOT EXISTS idx_sentiment_text_hash ON sentiment_analysis_results (text_hash);
CREATE INDEX IF NOT EXISTS idx_sentiment_sentiment ON sentiment_analysis_results (sentiment);
CREATE INDEX IF NOT EXISTS idx_sentiment_model_used ON sentiment_analysis_results (model_used);
CREATE INDEX IF NOT EXISTS idx_sentiment_source ON sentiment_analysis_results (source);
CREATE INDEX IF NOT EXISTS idx_sentiment_created_at ON sentiment_analysis_results (created_at);

-- Add comment
COMMENT ON TABLE sentiment_analysis_results IS 'Stores sentiment analysis results with deduplication and performance metrics';

-- -----------------------------------------------------------------------------
-- Reddit Posts Table
-- Stores Reddit post metadata and content
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reddit_posts (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(20) UNIQUE NOT NULL,                 -- Reddit post ID (unique identifier)
    title TEXT NOT NULL,                                 -- Post title
    selftext TEXT,                                       -- Post content (can be empty for link posts)
    subreddit VARCHAR(100) NOT NULL,                     -- Subreddit name (e.g., 'UCLA')
    author VARCHAR(100),                                 -- Reddit username (NULL if deleted)
    score INTEGER,                                       -- Reddit score (upvotes - downvotes)
    upvote_ratio REAL,                                   -- Ratio of upvotes (0.0 to 1.0)
    num_comments INTEGER,                                -- Number of comments on the post
    created_utc TIMESTAMP WITH TIME ZONE NOT NULL,       -- When the post was created on Reddit
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),   -- When we scraped this post
    sentiment_analysis_id INTEGER                        -- FK to sentiment_analysis_results
);

-- Add indexes for reddit_posts
CREATE INDEX IF NOT EXISTS idx_posts_post_id ON reddit_posts (post_id);
CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON reddit_posts (subreddit);
CREATE INDEX IF NOT EXISTS idx_posts_created_utc ON reddit_posts (created_utc);
CREATE INDEX IF NOT EXISTS idx_posts_scraped_at ON reddit_posts (scraped_at);
CREATE INDEX IF NOT EXISTS idx_posts_author ON reddit_posts (author);

-- Add comment
COMMENT ON TABLE reddit_posts IS 'Stores Reddit posts with metadata and links to sentiment analysis';

-- -----------------------------------------------------------------------------
-- Reddit Comments Table
-- Stores Reddit comment metadata and content
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reddit_comments (
    id SERIAL PRIMARY KEY,
    comment_id VARCHAR(20) UNIQUE NOT NULL,              -- Reddit comment ID (unique identifier)
    post_id VARCHAR(20) NOT NULL,                        -- Reddit post ID this comment belongs to
    body TEXT NOT NULL,                                  -- Comment content
    author VARCHAR(100),                                 -- Reddit username (NULL if deleted)
    score INTEGER,                                       -- Comment score (upvotes - downvotes)
    created_utc TIMESTAMP WITH TIME ZONE NOT NULL,       -- When the comment was created on Reddit
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),   -- When we scraped this comment
    sentiment_analysis_id INTEGER                        -- FK to sentiment_analysis_results
);

-- Add indexes for reddit_comments
CREATE INDEX IF NOT EXISTS idx_comments_comment_id ON reddit_comments (comment_id);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON reddit_comments (post_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_utc ON reddit_comments (created_utc);
CREATE INDEX IF NOT EXISTS idx_comments_scraped_at ON reddit_comments (scraped_at);
CREATE INDEX IF NOT EXISTS idx_comments_author ON reddit_comments (author);

-- Add comment
COMMENT ON TABLE reddit_comments IS 'Stores Reddit comments with metadata and links to sentiment analysis';

-- -----------------------------------------------------------------------------
-- Sentiment Alerts Table
-- Stores alerts for concerning content based on sentiment and keywords
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentiment_alerts (
    id SERIAL PRIMARY KEY,
    content_id VARCHAR(50) NOT NULL,                     -- Reddit post/comment ID
    content_text TEXT NOT NULL,                          -- The concerning text content
    content_type VARCHAR(20) NOT NULL,                   -- 'post' or 'comment'
    alert_type VARCHAR(50) NOT NULL,                     -- 'mental_health', 'stress', 'academic', 'harassment'
    severity VARCHAR(20) NOT NULL,                       -- 'low', 'medium', 'high'
    keywords_found JSONB,                                -- Array of keywords that triggered the alert
    subreddit VARCHAR(100) NOT NULL,                     -- Subreddit where content was found
    author VARCHAR(100),                                 -- Reddit username (NULL if deleted)
    status VARCHAR(20) DEFAULT 'active',                 -- 'active', 'reviewed', 'resolved'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),   -- When the alert was created
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),   -- Last update timestamp
    sentiment_analysis_id INTEGER                        -- FK to sentiment_analysis_results
);

-- Add indexes for sentiment_alerts
CREATE INDEX IF NOT EXISTS idx_alerts_content_id ON sentiment_alerts (content_id);
CREATE INDEX IF NOT EXISTS idx_alerts_alert_type ON sentiment_alerts (alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON sentiment_alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alerts_subreddit ON sentiment_alerts (subreddit);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON sentiment_alerts (status);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON sentiment_alerts (created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_content_type ON sentiment_alerts (content_type);

-- Add comment
COMMENT ON TABLE sentiment_alerts IS 'Stores alerts for concerning content identified through sentiment analysis and keyword matching';

-- =============================================================================
-- FOREIGN KEY CONSTRAINTS (Optional - for data integrity)
-- =============================================================================

-- Add foreign key constraints to link tables properly
-- Note: These are optional but recommended for data integrity

-- ALTER TABLE reddit_posts 
--     ADD CONSTRAINT fk_posts_sentiment 
--     FOREIGN KEY (sentiment_analysis_id) 
--     REFERENCES sentiment_analysis_results(id) 
--     ON DELETE SET NULL;

-- ALTER TABLE reddit_comments 
--     ADD CONSTRAINT fk_comments_sentiment 
--     FOREIGN KEY (sentiment_analysis_id) 
--     REFERENCES sentiment_analysis_results(id) 
--     ON DELETE SET NULL;

-- ALTER TABLE sentiment_alerts 
--     ADD CONSTRAINT fk_alerts_sentiment 
--     FOREIGN KEY (sentiment_analysis_id) 
--     REFERENCES sentiment_analysis_results(id) 
--     ON DELETE SET NULL;

-- =============================================================================
-- USEFUL VIEWS (Optional - for easier querying)
-- =============================================================================

-- View to get posts with their sentiment analysis
CREATE OR REPLACE VIEW posts_with_sentiment AS
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

-- View to get comments with their sentiment analysis
CREATE OR REPLACE VIEW comments_with_sentiment AS
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

-- View for alert dashboard
CREATE OR REPLACE VIEW alert_summary AS
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

-- =============================================================================
-- SAMPLE QUERIES (For testing and reference)
-- =============================================================================

-- Example queries to test the schema:

-- 1. Get recent posts with positive sentiment
-- SELECT * FROM posts_with_sentiment 
-- WHERE sentiment = 'positive' 
-- AND created_utc >= NOW() - INTERVAL '7 days'
-- ORDER BY created_utc DESC;

-- 2. Get active high-severity alerts
-- SELECT * FROM sentiment_alerts 
-- WHERE severity = 'high' 
-- AND status = 'active'
-- ORDER BY created_at DESC;

-- 3. Get sentiment distribution for UCLA subreddit
-- SELECT sentiment, COUNT(*) as count
-- FROM posts_with_sentiment 
-- WHERE subreddit = 'UCLA'
-- GROUP BY sentiment;

-- 4. Get users with most concerning posts
-- SELECT author, COUNT(*) as alert_count
-- FROM sentiment_alerts 
-- WHERE severity IN ('high', 'medium')
-- AND created_at >= NOW() - INTERVAL '30 days'
-- GROUP BY author
-- ORDER BY alert_count DESC;

-- =============================================================================
-- PERMISSIONS (Adjust as needed for your setup)
-- =============================================================================

-- Grant permissions to the sentiment_user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sentiment_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sentiment_user;

-- =============================================================================
-- MAINTENANCE QUERIES (For database cleanup)
-- =============================================================================

-- Delete old sentiment results (older than 90 days)
-- DELETE FROM sentiment_analysis_results 
-- WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete old Reddit posts (older than 90 days)  
-- DELETE FROM reddit_posts 
-- WHERE scraped_at < NOW() - INTERVAL '90 days';

-- Delete resolved alerts (older than 30 days)
-- DELETE FROM sentiment_alerts 
-- WHERE status = 'resolved' 
-- AND updated_at < NOW() - INTERVAL '30 days';

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================

-- Schema created successfully!
-- Tables: sentiment_analysis_results, reddit_posts, reddit_comments, sentiment_alerts
-- Indexes: Added for performance optimization
-- Views: Added for easier querying
-- Ready for UCLA Sentiment Analysis Reddit scraper!
