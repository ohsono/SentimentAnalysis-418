#!/bin/bash

# Worker Entrypoint Script
# Handles background worker initialization and Celery startup

set -e

echo "👷 Starting UCLA Sentiment Analysis Background Worker"
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

# Function to test Redis connection
test_redis() {
    echo "🔄 Testing Redis connection..."
    
    python -c "
import redis
import os
import sys

try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        password=os.getenv('REDIS_PASSWORD', ''),
        decode_responses=True
    )
    
    r.ping()
    print('✅ Redis connection successful')
    sys.exit(0)
    
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    sys.exit(1)
"
    
    return $?
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

# Main startup sequence
main() {
    echo "🔧 Starting worker startup sequence..."
    
    # Wait for Redis
    if [ -n "$REDIS_HOST" ]; then
        wait_for_service "$REDIS_HOST" "${REDIS_PORT:-6379}" "Redis" || {
            echo "❌ Redis startup failed"
            exit 1
        }
        
        test_redis || {
            echo "❌ Redis connection test failed"
            exit 1
        }
    fi
    
    # Wait for PostgreSQL
    if [ -n "$POSTGRES_HOST" ]; then
        wait_for_service "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}" "PostgreSQL" || {
            echo "❌ PostgreSQL startup failed"
            exit 1
        }
        
        test_database || {
            echo "❌ Database connection test failed"
            exit 1
        }
    fi
    
    # Set worker configuration
    export CELERY_BROKER_URL=${CELERY_BROKER_URL:-"redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0"}
    export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-"redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0"}
    
    echo "🎯 Worker Configuration:"
    echo "   Broker URL: ${CELERY_BROKER_URL}"
    echo "   Result Backend: ${CELERY_RESULT_BACKEND}"
    echo "   Database: ${POSTGRES_HOST:-none}"
    echo "   Redis: ${REDIS_HOST:-none}"
    
    echo "✅ Worker startup sequence completed!"
    echo "🚀 Starting Celery worker..."
    
    # Execute the main command
    exec "$@"
}

# Handle signals gracefully
trap 'echo "🛑 Received shutdown signal, stopping worker..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
