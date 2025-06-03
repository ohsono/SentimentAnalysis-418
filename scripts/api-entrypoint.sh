#!/bin/bash

# Enhanced API Entrypoint Script
# Handles database initialization, health checks, and graceful startup

set -e

echo "🚀 Starting UCLA Sentiment Analysis API (Enhanced)"
echo "⏰ $(date)"

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name at $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "🔄 Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Function to test database connection
test_database() {
    echo "🗄️  Testing database connection..."
    
    python -c "
import asyncio
import asyncpg
import os
import sys

async def test_db():
    try:
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'ucla_sentiment'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'password')
        )
        
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        
        if result == 1:
            print('✅ Database connection successful')
            return True
        else:
            print('❌ Database connection failed')
            return False
            
    except Exception as e:
        print(f'❌ Database error: {e}')
        return False

success = asyncio.run(test_db())
sys.exit(0 if success else 1)
"
    
    return $?
}

# Function to initialize database
init_database() {
    echo "🗄️  Initializing database..."
    
    python -c "
import asyncio
import sys
import os
sys.path.append('/app')

from app.database.postgres_manager_enhanced import DatabaseManager

async def init_db():
    try:
        db_manager = DatabaseManager()
        success = await db_manager.initialize()
        await db_manager.close()
        return success
    except Exception as e:
        print(f'Database initialization error: {e}')
        return False

success = asyncio.run(init_db())
print('✅ Database initialized' if success else '❌ Database initialization failed')
sys.exit(0 if success else 1)
"
    
    return $?
}

# Function to check model service
check_model_service() {
    echo "🤖 Checking model service..."
    
    if [ -n "$MODEL_SERVICE_URL" ]; then
        local url=${MODEL_SERVICE_URL}/health
        local max_attempts=10
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -s --max-time 10 "$url" > /dev/null 2>&1; then
                echo "✅ Model service is ready at $MODEL_SERVICE_URL"
                return 0
            fi
            
            echo "🔄 Attempt $attempt/$max_attempts: Model service not ready..."
            sleep 3
            attempt=$((attempt + 1))
        done
        
        echo "⚠️  Model service not ready, will use VADER fallback"
        return 0  # Continue anyway, fallback will handle this
    else
        echo "⚠️  MODEL_SERVICE_URL not set, using VADER fallback only"
        return 0
    fi
}

# Main startup sequence
main() {
    echo "🔧 Starting enhanced startup sequence..."
    
    # Wait for PostgreSQL
    if [ -n "$POSTGRES_HOST" ]; then
        wait_for_service "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}" "PostgreSQL" || {
            echo "❌ PostgreSQL startup failed"
            exit 1
        }
        
        # Test database connection
        test_database || {
            echo "❌ Database connection test failed"
            exit 1
        }
        
        # Initialize database
        init_database || {
            echo "❌ Database initialization failed"
            exit 1
        }
    else
        echo "⚠️  No database configuration, running in memory mode"
    fi
    
    # Wait for Redis if configured
    if [ -n "$REDIS_HOST" ]; then
        wait_for_service "$REDIS_HOST" "${REDIS_PORT:-6379}" "Redis" || {
            echo "⚠️  Redis not ready, continuing without caching"
        }
    fi
    
    # Check model service
    check_model_service
    
    # Set environment defaults
    export API_HOST=${API_HOST:-0.0.0.0}
    export API_PORT=${API_PORT:-8080}
    export ENV=${ENV:-production}
    
    # Enhanced configuration
    export FAILSAFE_MAX_LLM_FAILURES=${FAILSAFE_MAX_LLM_FAILURES:-3}
    export FAILSAFE_FAILURE_WINDOW_SECONDS=${FAILSAFE_FAILURE_WINDOW_SECONDS:-300}
    export FALLBACK_TO_VADER=${FALLBACK_TO_VADER:-true}
    
    echo "🎯 Configuration:"
    echo "   API: $API_HOST:$API_PORT"
    echo "   Environment: $ENV"
    echo "   Database: ${POSTGRES_HOST:-none}"
    echo "   Model Service: ${MODEL_SERVICE_URL:-none}"
    echo "   Failsafe Max Failures: $FAILSAFE_MAX_LLM_FAILURES"
    echo "   VADER Fallback: $FALLBACK_TO_VADER"
    
    echo "✅ Enhanced startup sequence completed successfully!"
    echo "🚀 Starting API server..."
    
    # Execute the main command
    exec "$@"
}

# Handle signals gracefully
trap 'echo "🛑 Received shutdown signal, stopping gracefully..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
