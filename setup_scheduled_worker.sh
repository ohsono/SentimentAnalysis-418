#!/bin/bash

# Scheduled Worker Setup Script
# Sets up and starts the enhanced worker service with scheduling

set -e

echo "🚀 UCLA Sentiment Analysis - Scheduled Worker Setup"
echo "=================================================="

# Function to print colored output
print_status() {
    echo -e "\033[1;32m$1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m$1\033[0m"
}

print_error() {
    echo -e "\033[1;31m$1\033[0m"
}

# Check if we're in the right directory
if [ ! -f "worker/main.py" ]; then
    print_error "❌ Error: Please run this script from the project root directory"
    exit 1
fi

print_status "✅ Project directory detected"

# Check for Python
if ! command -v python3 &> /dev/null; then
    print_error "❌ Error: Python 3 is required but not installed"
    exit 1
fi

print_status "✅ Python 3 detected"

# Check for required environment variables
print_status "🔍 Checking environment configuration..."

# Copy scheduler configuration if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.scheduler" ]; then
        print_status "📋 Copying scheduler configuration to .env..."
        cp .env.scheduler .env
    else
        print_warning "⚠️  No .env file found. Creating from template..."
        cp .env.docker .env
        print_warning "⚠️  Please edit .env with your actual credentials"
    fi
else
    print_status "✅ .env file exists"
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | xargs) 2>/dev/null || true
fi

# Check Reddit credentials
if [ -z "$REDDIT_CLIENT_ID" ] || [ -z "$REDDIT_CLIENT_SECRET" ]; then
    print_error "❌ Error: Reddit API credentials not configured"
    print_warning "💡 Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file"
    exit 1
fi

print_status "✅ Reddit API credentials configured"

# Check database configuration
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_USER" ]; then
    print_warning "⚠️  Database configuration incomplete - database features will be disabled"
else
    print_status "✅ Database configuration found"
fi

# Test imports
print_status "🧪 Testing worker imports..."
python3 -c "from worker.worker_orchestrator import WorkerOrchestrator; print('✅ Import successful')" || {
    print_error "❌ Error: Worker imports failed"
    print_warning "💡 Try: pip install -r requirements_worker_scraper_minimal.txt"
    exit 1
}

# Show configuration summary
print_status "📋 Current Configuration:"
echo "   Scheduler Enabled: ${SCHEDULER_ENABLED:-true}"
echo "   Scraping Interval: ${SCRAPING_INTERVAL_MINUTES:-30} minutes"
echo "   Auto Pipeline: ${AUTO_PIPELINE_ENABLED:-true}"
echo "   Default Subreddit: ${DEFAULT_SUBREDDIT:-UCLA}"
echo "   Post Limit: ${DEFAULT_POST_LIMIT:-100}"
echo "   Comment Limit: ${DEFAULT_COMMENT_LIMIT:-50}"

# Ask user how they want to run
echo ""
echo "🎯 How would you like to run the scheduled worker?"
echo "1) Production mode (30-60 minute intervals)"
echo "2) Test mode (short intervals for testing)"
echo "3) Manual mode (no scheduler, manual tasks only)"
echo "4) Custom configuration"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        print_status "🏭 Starting in production mode..."
        python3 run_scheduled_worker.py --config scheduler
        ;;
    2)
        print_status "🧪 Starting in test mode..."
        python3 run_scheduled_worker.py --test-mode
        ;;
    3)
        print_status "📋 Starting in manual mode..."
        python3 run_scheduled_worker.py --no-scheduler
        ;;
    4)
        echo "Available options:"
        echo "  --interval MINUTES     Set scraping interval"
        echo "  --no-scheduler         Disable scheduler"
        echo "  --no-pipeline          Disable auto pipeline"
        echo "  --test-mode           Use test settings"
        echo ""
        read -p "Enter custom arguments: " custom_args
        print_status "⚙️ Starting with custom configuration..."
        python3 run_scheduled_worker.py $custom_args
        ;;
    *)
        print_error "❌ Invalid choice. Starting in production mode..."
        python3 run_scheduled_worker.py --config scheduler
        ;;
esac
