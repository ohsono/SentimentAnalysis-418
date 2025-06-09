#!/bin/bash

# UCLA Sentiment Analysis Database Setup Script
# This script sets up the PostgreSQL database using the schema file

set -e  # Exit on any error

echo "🗄️  UCLA Sentiment Analysis Database Setup"
echo "=" $(printf '=%.0s' {1..50})

# Load environment variables from .env file
if [ -f .env ]; then
    echo "✅ Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found!"
    echo "💡 Make sure you have POSTGRES_* variables set"
    exit 1
fi

# Set default values if not provided
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-sentiment_db}
POSTGRES_USER=${POSTGRES_USER:-sentiment_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-sentiment_password}

echo "📊 Database Configuration:"
echo "  Host: $POSTGRES_HOST"
echo "  Port: $POSTGRES_PORT"
echo "  Database: $POSTGRES_DB"
echo "  User: $POSTGRES_USER"

# Check if PostgreSQL is running
echo ""
echo "🔍 Checking PostgreSQL connection..."
if command -v pg_isready &> /dev/null; then
    if pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB &> /dev/null; then
        echo "✅ PostgreSQL is running and accessible"
    else
        echo "❌ Cannot connect to PostgreSQL"
        echo "💡 Make sure PostgreSQL is running:"
        echo "   macOS: brew services start postgresql"
        echo "   Linux: sudo systemctl start postgresql"
        echo "   Docker: docker run --name postgres -e POSTGRES_PASSWORD=\$POSTGRES_PASSWORD -p 5432:5432 -d postgres"
        exit 1
    fi
else
    echo "⚠️  pg_isready not found, skipping connection check"
fi

# Check if schema file exists
if [ ! -f "database_schema.sql" ]; then
    echo "❌ database_schema.sql file not found!"
    echo "💡 Make sure you're running this script from the project directory"
    exit 1
fi

echo ""
echo "🔧 Applying database schema..."
echo "⚠️  This will drop existing tables if they exist!"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled by user"
    exit 0
fi

# Apply the schema
export PGPASSWORD=$POSTGRES_PASSWORD
if psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -f database_schema.sql; then
    echo ""
    echo "🎉 Database schema applied successfully!"
    
    # Test the setup
    echo ""
    echo "🧪 Testing database setup..."
    
    # Check if tables were created
    TABLE_COUNT=$(psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -t -c "
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('sentiment_analysis_results', 'reddit_posts', 'reddit_comments', 'sentiment_alerts')
    " | tr -d ' ')
    
    if [ "$TABLE_COUNT" = "4" ]; then
        echo "✅ All 4 tables created successfully"
        
        # Show table info
        echo ""
        echo "📋 Created tables:"
        psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "
            SELECT 
                schemaname,
                tablename,
                tableowner
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('sentiment_analysis_results', 'reddit_posts', 'reddit_comments', 'sentiment_alerts')
            ORDER BY tablename;
        "
        
        echo ""
        echo "📊 Created views:"
        psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "
            SELECT 
                schemaname,
                viewname,
                viewowner
            FROM pg_views 
            WHERE schemaname = 'public' 
            AND viewname IN ('posts_with_sentiment', 'comments_with_sentiment', 'alert_summary')
            ORDER BY viewname;
        "
        
    else
        echo "❌ Expected 4 tables, found $TABLE_COUNT"
        exit 1
    fi
    
    echo ""
    echo "🎯 Database is ready for Reddit scraping!"
    echo ""
    echo "💡 Next steps:"
    echo "   1. Test database: python test_database.py"
    echo "   2. Run scraper: python reddit_scraper_with_db.py"
    echo "   3. Check data: psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB"
    
else
    echo ""
    echo "❌ Failed to apply database schema"
    echo "💡 Check the error messages above"
    exit 1
fi

# Clean up
unset PGPASSWORD

echo ""
echo "✅ Database setup complete!"
