#!/bin/bash

# Model Service Entrypoint Script
# Handles model downloads, caching, and service initialization

set -e

echo "🤖 Starting UCLA Sentiment Analysis Model Service"
echo "⏰ $(date)"

# Function to check available memory
check_memory() {
    local available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    echo "💾 Available memory: ${available_memory}MB"
    
    if [ "$available_memory" -lt 1024 ]; then
        echo "⚠️  Warning: Low memory (${available_memory}MB). Consider reducing model size or increasing memory."
    fi
}

# Function to prepare model directory
prepare_model_directory() {
    echo "📁 Preparing model directory..."
    
    mkdir -p /app/models
    chown -R modeluser:modeluser /app/models
    
    # Set cache permissions
    export HF_HOME=/app/models
    export TRANSFORMERS_CACHE=/app/models
    export TORCH_HOME=/app/models
    
    echo "✅ Model directory prepared"
}

# Function to pre-download models
preload_models() {
    echo "📥 Pre-loading models..."
    
    if [ -n "$PRELOAD_MODEL" ]; then
        echo "🔄 Pre-loading model: $PRELOAD_MODEL"
        
        python -c "
import os
import sys
sys.path.append('/app')

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    
    model_name = os.getenv('PRELOAD_MODEL', 'distilbert-sentiment')
    
    # Map model keys to actual model names
    model_mapping = {
        'distilbert-sentiment': 'distilbert-base-uncased-finetuned-sst-2-english',
        'twitter-roberta': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
        'bert-sentiment': 'nlptown/bert-base-multilingual-uncased-sentiment'
    }
    
    actual_model_name = model_mapping.get(model_name, model_name)
    
    print(f'🔄 Downloading {actual_model_name}...')
    
    # Download tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(actual_model_name)
    model = AutoModelForSequenceClassification.from_pretrained(actual_model_name)
    
    print(f'✅ Successfully pre-loaded {model_name}')
    
except Exception as e:
    print(f'⚠️  Warning: Failed to pre-load model {os.getenv(\"PRELOAD_MODEL\", \"unknown\")}: {e}')
    print('🔄 Service will continue and download on first request')
"
    else
        echo "⚠️  No PRELOAD_MODEL specified, models will be downloaded on first request"
    fi
}

# Function to optimize for inference
optimize_for_inference() {
    echo "⚡ Optimizing for inference..."
    
    # Set threading for optimal performance
    export OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
    export MKL_NUM_THREADS=${MKL_NUM_THREADS:-2}
    export TOKENIZERS_PARALLELISM=false
    
    # Disable unnecessary logging
    export TF_CPP_MIN_LOG_LEVEL=2
    export TRANSFORMERS_VERBOSITY=error
    
    echo "✅ Inference optimizations applied"
}

# Function to test model service
test_model_service() {
    echo "🧪 Testing model service functionality..."
    
    python -c "
import sys
sys.path.append('/app')

try:
    # Test basic imports
    from app.ml.lightweight_model_manager import LightweightModelManager
    
    print('✅ Model manager imports successful')
    
    # Basic initialization test
    manager = LightweightModelManager()
    print('✅ Model manager initialization successful')
    
except Exception as e:
    print(f'⚠️  Model service test warning: {e}')
    print('🔄 Service will continue with limited functionality')
"
}

# Function to start health monitoring
start_health_monitoring() {
    echo "💓 Starting health monitoring..."
    
    # Create health check script
    cat > /tmp/health_monitor.py << 'EOF'
import asyncio
import aiohttp
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check():
    """Periodic health check"""
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8081/health', timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Health check OK: {data.get('status', 'unknown')}")
                    else:
                        logger.warning(f"Health check failed: {response.status}")
        except Exception as e:
            logger.error(f"Health check error: {e}")
        
        await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    asyncio.run(health_check())
EOF
    
    # Start health monitoring in background
    python /tmp/health_monitor.py &
    
    echo "✅ Health monitoring started"
}

# Main startup sequence
main() {
    echo "🔧 Starting model service startup sequence..."
    
    # Check system resources
    check_memory
    
    # Prepare environment
    prepare_model_directory
    optimize_for_inference
    
    # Test basic functionality
    test_model_service
    
    # Pre-load models if specified
    preload_models
    
    # Start health monitoring
    start_health_monitoring
    
    # Set service configuration
    export HOST=${HOST:-0.0.0.0}
    export PORT=${PORT:-8081}
    
    echo "🎯 Model Service Configuration:"
    echo "   Host: $HOST"
    echo "   Port: $PORT"
    echo "   Preload Model: ${PRELOAD_MODEL:-none}"
    echo "   Cache Directory: $HF_HOME"
    echo "   Threading: OMP=$OMP_NUM_THREADS, MKL=$MKL_NUM_THREADS"
    
    echo "✅ Model service startup sequence completed!"
    echo "🚀 Starting model service..."
    
    # Execute the main command
    exec "$@"
}

# Handle signals gracefully
cleanup() {
    echo "🛑 Received shutdown signal, cleaning up..."
    
    # Kill background processes
    jobs -p | xargs -r kill
    
    echo "✅ Cleanup completed"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Run main function
main "$@"
