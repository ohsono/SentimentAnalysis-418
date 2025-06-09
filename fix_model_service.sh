#!/bin/bash

# Fix Model Service Permissions Script
# This script fixes permission issues with the sentiment analysis model service

echo "🔧 Fixing Model Service Permissions"
echo "=" $(printf '=%.0s' {1..40})

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found!"
    echo "💡 Please run this script from the project root directory"
    exit 1
fi

echo "📁 Creating necessary directories with correct permissions..."

# Create model cache directory with proper permissions
sudo mkdir -p ./model_cache
sudo chmod 755 ./model_cache
sudo chown -R $USER:$USER ./model_cache
echo "✅ Created ./model_cache with proper permissions"

# Create NLTK data directory
sudo mkdir -p ./nltk_data
sudo chmod 755 ./nltk_data
sudo chown -R $USER:$USER ./nltk_data
echo "✅ Created ./nltk_data directory"

# Create logs directory
sudo mkdir -p ./logs
sudo chmod 755 ./logs
sudo chown -R $USER:$USER ./logs
echo "✅ Created ./logs directory"

echo ""
echo "🐳 Stopping and rebuilding Docker containers..."

# Stop existing containers
docker-compose down

# Remove old model service container and image
docker-compose rm -f model-service
docker rmi $(docker images -q '*model-service*' 2>/dev/null) 2>/dev/null || true

echo ""
echo "🔨 Rebuilding model service with fixed permissions..."

# Rebuild the model service container
docker-compose build model-service

echo ""
echo "🚀 Starting services..."

# Start services
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🧪 Testing model service health..."

# Test model service health
if curl -s http://localhost:8081/health > /dev/null; then
    echo "✅ Model service is responding"
    
    # Check available models
    echo ""
    echo "📋 Available models:"
    curl -s http://localhost:8081/models | jq '.' 2>/dev/null || curl -s http://localhost:8081/models
    
else
    echo "❌ Model service not responding"
    echo "💡 Check logs: docker-compose logs model-service"
fi

echo ""
echo "📊 Service status:"
docker-compose ps

echo ""
echo "💡 If issues persist:"
echo "  1. Check logs: docker-compose logs model-service"
echo "  2. Try: docker-compose down && docker-compose up --build"
echo "  3. Check disk space: df -h"
echo "  4. Check Docker permissions: docker info"
