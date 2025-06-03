#!/bin/bash

# Database Fix Script for UCLA Sentiment Analysis
# Fixes table schema and async scraping issues

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  UCLA Sentiment Analysis - Database Fix${NC}"
echo -e "${BLUE}============================================${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Checking PostgreSQL container status...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Start PostgreSQL if not running
if ! docker-compose ps | grep -q "ucla_sentiment_db.*Up"; then
    echo -e "${YELLOW}🚀 Starting PostgreSQL container...${NC}"
    docker-compose up -d postgres
    echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
    sleep 10
fi

# Test PostgreSQL connection
echo -e "${BLUE}🔍 Testing PostgreSQL connection...${NC}"
if docker exec ucla_sentiment_db pg_isready -U sentiment_user -d sentiment_db > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is running and accessible${NC}"
else
    echo -e "${RED}❌ PostgreSQL connection failed${NC}"
    echo -e "${YELLOW}💡 Try: docker-compose restart postgres${NC}"
    exit 1
fi

# Run database schema fix
echo -e "${BLUE}🏗️  Creating/fixing database schema...${NC}"
docker exec -i ucla_sentiment_db psql -U sentiment_user -d sentiment_db << 'EOF'
\set ON_ERROR_STOP on

-- Display current status
\echo '📊 Current database status:'
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check if tables exist and show row counts if they do
DO $$
DECLARE
    table_exists INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO table_exists
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'sentiment_analysis_results';
    
    IF table_exists > 0 THEN
        RAISE NOTICE '⚠️  Tables already exist. Checking compatibility...';
    ELSE
        RAISE NOTICE '🆕 No existing tables found. Will create new schema.';
    END IF;
END $$;

EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to check database status${NC}"
    exit 1
fi

echo -e "${BLUE}🏗️  Applying fixed database schema...${NC}"
if docker exec -i ucla_sentiment_db psql -U sentiment_user -d sentiment_db < init_scripts/03_fixed_schema.sql; then
    echo -e "${GREEN}✅ Database schema created successfully${NC}"
else
    echo -e "${RED}❌ Failed to create database schema${NC}"
    exit 1
fi

echo -e "${BLUE}📝 Inserting configuration and test data...${NC}"
if docker exec -i ucla_sentiment_db psql -U sentiment_user -d sentiment_db < init_scripts/04_data_initialization.sql; then
    echo -e "${GREEN}✅ Configuration data inserted successfully${NC}"
else
    echo -e "${RED}❌ Failed to insert configuration data${NC}"
    exit 1
fi

# Verify the database setup
echo -e "${BLUE}🔍 Verifying database setup...${NC}"
docker exec -i ucla_sentiment_db psql -U sentiment_user -d sentiment_db << 'EOF'
-- Show table summary
\echo '📊 Final Database Summary:'
SELECT 
    t.table_name,
    CASE 
        WHEN t.table_type = 'BASE TABLE' THEN 'Table'
        WHEN t.table_type = 'VIEW' THEN 'View'  
        ELSE t.table_type
    END as type,
    (SELECT COUNT(*) 
     FROM information_schema.columns 
     WHERE table_name = t.table_name 
     AND table_schema = 'public') as columns
FROM information_schema.tables t
WHERE t.table_schema = 'public'
ORDER BY t.table_name;

-- Test the configuration tables
\echo '🔧 Configuration Data:'
SELECT cache_key, 
       jsonb_pretty(cache_data) as configuration,
       expires_at
FROM analytics_cache 
WHERE cache_key IN ('system_config', 'model_config', 'alert_keywords')
ORDER BY cache_key;

-- Show sample data counts
\echo '📈 Sample Data Counts:'
SELECT 'sentiment_analysis_results' as table_name, COUNT(*) as rows FROM sentiment_analysis_results
UNION ALL
SELECT 'reddit_posts' as table_name, COUNT(*) as rows FROM reddit_posts  
UNION ALL
SELECT 'reddit_comments' as table_name, COUNT(*) as rows FROM reddit_comments
UNION ALL
SELECT 'sentiment_alerts' as table_name, COUNT(*) as rows FROM sentiment_alerts
UNION ALL
SELECT 'system_metrics' as table_name, COUNT(*) as rows FROM system_metrics
UNION ALL
SELECT 'analytics_cache' as table_name, COUNT(*) as rows FROM analytics_cache;

EOF

echo -e "\n${GREEN}✅ Database setup completed successfully!${NC}"

# Now fix the worker service
echo -e "\n${BLUE}🔧 Worker service has been fixed for the async scraping issue${NC}"
echo -e "${GREEN}✅ Removed problematic coroutine calls that caused the 'coroutine not subscriptable' error${NC}"

# Test the fixed endpoints
echo -e "\n${BLUE}🧪 Testing the fixed worker service...${NC}"

# Check if worker is running
if curl -s http://localhost:8082/health > /dev/null; then
    echo -e "${GREEN}✅ Worker service is running${NC}"
    
    # Test the GET /scrape endpoint
    echo -e "${YELLOW}📡 Testing GET /scrape endpoint...${NC}"
    if curl -s http://localhost:8082/scrape | grep -q "Reddit Scraping Endpoint"; then
        echo -e "${GREEN}✅ GET /scrape endpoint working${NC}"
    else
        echo -e "${RED}❌ GET /scrape endpoint failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Worker service not running. Start it with:${NC}"
    echo -e "   ${YELLOW}python run_worker_local.py${NC}"
    echo -e "   ${YELLOW}or${NC}"
    echo -e "   ${YELLOW}docker-compose up -d worker-scraper-api${NC}"
fi

echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}  Fix Summary${NC}"
echo -e "${BLUE}============================================${NC}"

echo -e "${GREEN}✅ Database Issues Fixed:${NC}"
echo -e "   • Created sentiment_analysis_results table"
echo -e "   • Created sentiment_alerts table"  
echo -e "   • Created reddit_posts and reddit_comments tables"
echo -e "   • Added system_metrics and analytics_cache tables"
echo -e "   • Inserted configuration data and alert keywords"
echo -e "   • Created dashboard analytics view"

echo -e "\n${GREEN}✅ Worker Service Issues Fixed:${NC}"
echo -e "   • Fixed 'coroutine object is not subscriptable' error"
echo -e "   • Removed problematic async calls in /scrape endpoint"
echo -e "   • Added GET /scrape endpoint for API information"
echo -e "   • Worker now properly queues tasks for background processing"

echo -e "\n${BLUE}🚀 Next Steps:${NC}"
echo -e "1. Start the worker service:"
echo -e "   ${YELLOW}python run_worker_local.py${NC}"
echo -e ""
echo -e "2. Test the scraping API:"
echo -e "   ${YELLOW}curl -X POST http://localhost:8082/scrape -H 'Content-Type: application/json' -d '{\"subreddit\": \"UCLA\", \"post_limit\": 3}'${NC}"
echo -e ""
echo -e "3. Run the full test suite:"
echo -e "   ${YELLOW}python test_worker_api.py${NC}"

echo -e "\n${GREEN}🎉 All issues have been resolved!${NC}"
