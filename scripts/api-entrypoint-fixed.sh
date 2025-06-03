#!/bin/bash

# Fixed API Entrypoint Script - skips problematic nc check
set -e

echo "🚀 Starting UCLA Sentiment Analysis API (Fixed Version)"
echo "⏰ $(date)"

# Function to test database connection directly
test_database() {
    echo "🗄️  Testing database connection..."
    
    python -c "
import asyncio
import asyncpg
import os
import sys

async def test_db():
    max_attempts = 15
    attempt = 1
    
    while attempt <= max_attempts:
        try:
            conn = await asyncpg.connect(
                host=os.getenv('POSTGRES_HOST', 'postgres'),
                port=int(os.getenv('POSTGRES_PORT', '5432')),
                database=os.getenv('POSTGRES_DB', 'ucla_sentiment'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'sentiment_password_2024')
            )
            
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            
            if result == 1:
                print('✅ Database connection successful')
                return True
                
        except Exception as e:
            print(f'🔄 Attempt {attempt}/{max_attempts}: Database not ready ({e})')
            if attempt < max_attempts:
                await asyncio.sleep(3)
            attempt += 1
    
    print('❌ Database connection failed after all attempts')
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

try:
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
    
except ImportError as e:
    print(f'⚠️  Database manager not available: {e}')
    print('✅ Continuing without database initialization')
    sys.exit(0)
"
    
    return $?
}

# Function to check model service
check_model_service() {
    echo "🤖 Checking model service..."
    
    if [ -n "$MODEL_SERVICE_URL" ]; then
        local url=${MODEL_SERVICE_URL}/health
        local max_attempts=5
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
                echo "✅ Model service is ready at $MODEL_SERVICE_URL"
                return 0
            fi
            
            echo "🔄 Attempt $attempt/$max_attempts: Model service not ready..."
            sleep 2
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
    echo "🔧 Starting fixed startup sequence..."
    
    # Test database connection directly (no nc check)
    if [ -n "$POSTGRES_HOST" ]; then
        echo "🗄️  Testing database connectivity..."
        test_database || {
            echo "❌ Database connection test failed"
            exit 1
        }
        
        # Initialize database
        init_database || {
            echo "⚠️  Database initialization had issues, continuing..."
        }
    else
        echo "⚠️  No database configuration, running in memory mode"
    fi
    
    # Check model service (optional)
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
    
    echo "✅ Fixed startup sequence completed successfully!"
    echo "🚀 Starting API server..."
    
    # Execute the main command
    exec "$@"
}

# Handle signals gracefully
trap 'echo "🛑 Received shutdown signal, stopping gracefully..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
