#!/bin/bash

# Robust Docker Build Script with Error Handling
# Fixes common dependency and build issues

set -e

echo "🚀 Starting robust Docker build process..."

# Navigate to project directory
cd ~/Project/UCLA-MASDS/SentimentAnalysis-418

echo "🧹 Comprehensive Docker cleanup..."
docker system prune -a --volumes -f
docker builder prune -a -f
docker volume prune -f

echo "📊 Current disk space:"
df -h | head -3
echo ""
docker system df

echo ""
echo "🔍 Validating requirements files..."

# Check for common requirement file issues
echo "Checking for torch-audio (should be torchaudio)..."
if grep -q "torch-audio" requirements*.txt 2>/dev/null; then
    echo "❌ Found torch-audio in requirements. This should be torchaudio"
    echo "Fixing automatically..."
    sed -i.bak 's/torch-audio/torchaudio/g' requirements*.txt
    echo "✅ Fixed torch-audio -> torchaudio"
fi

echo ""
echo "🔨 Building Docker images with enhanced error handling..."

# Function to build with retry logic
build_with_retry() {
    local dockerfile=$1
    local tag=$2
    local max_attempts=2
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo "📦 Building $tag (attempt $attempt/$max_attempts)..."
        
        if docker build -f $dockerfile -t $tag . --no-cache --progress=plain; then
            echo "✅ Successfully built $tag"
            return 0
        else
            echo "❌ Build failed for $tag (attempt $attempt)"
            if [ $attempt -eq $max_attempts ]; then
                echo "💥 Failed to build $tag after $max_attempts attempts"
                return 1
            fi
            echo "🔄 Retrying in 5 seconds..."
            sleep 5
            # Additional cleanup between attempts
            docker builder prune -f
        fi
        
        ((attempt++))
    done
}

# Build each service with retry logic
echo ""
echo "1️⃣ Building API service..."
if ! build_with_retry "Dockerfile.api-enhanced" "ucla-sentiment-api:latest"; then
    echo "💥 API build failed. Check logs above."
    exit 1
fi

echo ""
echo "2️⃣ Building Model service..."
if ! build_with_retry "Dockerfile.model-service-enhanced" "ucla-sentiment-model-service:latest"; then
    echo "💥 Model service build failed. Check logs above."
    exit 1
fi

echo ""
echo "3️⃣ Building Worker service..."
if ! build_with_retry "Dockerfile.worker" "ucla-sentiment-worker:latest"; then
    echo "💥 Worker build failed. Check logs above."
    exit 1
fi

echo ""
echo "🎉 All Docker images built successfully!"
echo ""
echo "📋 Built images:"
docker images | grep ucla-sentiment | head -10

echo ""
echo "🚀 Next steps:"
echo "   1. Start core services: docker-compose -f docker-compose-enhanced.yml up -d postgres redis"
echo "   2. Wait 10 seconds for DB startup"
echo "   3. Start main services: docker-compose -f docker-compose-enhanced.yml up -d api model-service worker"
echo "   4. Check status: docker-compose -f docker-compose-enhanced.yml ps"
echo "   5. Test API: curl http://localhost:8080/health"
