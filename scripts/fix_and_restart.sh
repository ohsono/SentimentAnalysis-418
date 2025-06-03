#!/bin/bash

# Complete Fix and Restart Script for UCLA Sentiment Analysis API
# This script will diagnose, fix, and restart your API

set -e

echo "🚀 UCLA Sentiment Analysis API - Complete Fix & Restart"
echo "=================================================================="

cd ~/Project/UCLA-MASDS/SentimentAnalysis-418

echo "Step 1: 🧹 Cleaning up Docker environment..."
echo "=================================================================="

# Stop any running containers
echo "Stopping existing containers..."
docker-compose -f docker-compose-enhanced.yml down 2>/dev/null || echo "No containers were running"

# Clean up Docker system
echo "Cleaning Docker system..."
docker system prune -f
docker builder prune -f

echo ""
echo "Step 2: 📊 Checking current disk space..."
echo "=================================================================="
df -h | head -3
echo ""
docker system df

echo ""
echo "Step 3: 🔨 Building Docker images..."
echo "=================================================================="

# Build images one by one with better error handling
echo "Building API service..."
if docker build -f Dockerfile.api-enhanced -t ucla-sentiment-api:latest . --no-cache --progress=plain; then
    echo "✅ API service built successfully"
else
    echo "❌ API service build failed"
    exit 1
fi

echo ""
echo "Building Model service..."
if docker build -f Dockerfile.model-service-enhanced -t ucla-sentiment-model-service:latest . --no-cache --progress=plain; then
    echo "✅ Model service built successfully"
else
    echo "❌ Model service build failed"
    exit 1
fi

echo ""
echo "Building Worker service..."
if docker build -f Dockerfile.worker -t ucla-sentiment-worker:latest . --no-cache --progress=plain; then
    echo "✅ Worker service built successfully"
else
    echo "❌ Worker service build failed"
    exit 1
fi

echo ""
echo "Step 4: 🚀 Starting services in order..."
echo "=================================================================="

# Start database and redis first
echo "Starting PostgreSQL and Redis..."
docker-compose -f docker-compose-enhanced.yml up -d postgres redis

echo "Waiting for database to be ready..."
sleep 15

# Check if database is ready
echo "Checking database connectivity..."
if docker-compose -f docker-compose-enhanced.yml exec postgres pg_isready -U postgres; then
    echo "✅ Database is ready"
else
    echo "⚠️  Database not ready yet, waiting longer..."
    sleep 10
fi

# Start model service
echo ""
echo "Starting Model service..."
docker-compose -f docker-compose-enhanced.yml up -d model-service

echo "Waiting for model service to initialize..."
sleep 20

# Start API and worker
echo ""
echo "Starting API and Worker services..."
docker-compose -f docker-compose-enhanced.yml up -d api worker

echo ""
echo "Step 5: 🔍 Checking service status..."
echo "=================================================================="

sleep 10

echo "Container status:"
docker-compose -f docker-compose-enhanced.yml ps

echo ""
echo "Service health checks:"

# Check each service
services=("postgres" "redis" "model-service" "api" "worker")
for service in "${services[@]}"; do
    if docker-compose -f docker-compose-enhanced.yml ps | grep -q "$service.*Up"; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running or failed"
        echo "   Logs for $service:"
        docker-compose -f docker-compose-enhanced.yml logs --tail=10 "$service" 2>/dev/null || echo "   No logs available"
    fi
done

echo ""
echo "Step 6: 🧪 Testing API connectivity..."
echo "=================================================================="

# Wait a bit more for API to be fully ready
echo "Waiting for API to be fully ready..."
sleep 15

# Test API
echo "Testing API endpoints..."

# Test health endpoint
if curl -s -f http://localhost:8080/health > /dev/null; then
    echo "✅ Health endpoint: Working"
    echo "   Response: $(curl -s http://localhost:8080/health | jq -r '.status' 2>/dev/null || echo 'Available')"
else
    echo "❌ Health endpoint: Not responding"
fi

# Test main endpoint
if curl -s -f http://localhost:8080/ > /dev/null; then
    echo "✅ Main endpoint: Working"
else
    echo "❌ Main endpoint: Not responding"
fi

# Test sentiment analysis
echo ""
echo "Testing sentiment analysis..."
response=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"UCLA is amazing!","include_probabilities":true}' \
  http://localhost:8080/predict 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$response" ]; then
    echo "✅ Sentiment analysis: Working"
    sentiment=$(echo "$response" | jq -r '.sentiment' 2>/dev/null || echo "Success")
    echo "   Test result: $sentiment"
else
    echo "❌ Sentiment analysis: Not working"
fi

echo ""
echo "Step 7: 📋 Final status and next steps..."
echo "=================================================================="

# Get final status
running_containers=$(docker-compose -f docker-compose-enhanced.yml ps | grep -c "Up" || echo "0")
total_containers=5

echo "📊 Status Summary:"
echo "   Running containers: $running_containers/$total_containers"

if [ "$running_containers" -eq "$total_containers" ]; then
    echo "   🎉 ALL SERVICES RUNNING SUCCESSFULLY!"
    echo ""
    echo "🌐 Your API is now available at:"
    echo "   • Main API: http://localhost:8080"
    echo "   • Interactive docs: http://localhost:8080/docs"
    echo "   • Health check: http://localhost:8080/health"
    echo "   • Model service: http://localhost:8081"
    echo ""
    echo "🧪 Run comprehensive tests with:"
    echo "   python3 comprehensive_api_test.py"
    echo ""
    echo "📊 Monitor with:"
    echo "   docker-compose -f docker-compose-enhanced.yml logs -f api"
    
elif [ "$running_containers" -gt 2 ]; then
    echo "   ⚠️  Most services running, but some issues detected"
    echo ""
    echo "🔍 Debug failing services:"
    echo "   docker-compose -f docker-compose-enhanced.yml logs api"
    echo "   docker-compose -f docker-compose-enhanced.yml logs model-service"
    echo ""
    echo "🔄 Restart specific service:"
    echo "   docker-compose -f docker-compose-enhanced.yml restart api"
    
else
    echo "   ❌ Multiple services failed to start"
    echo ""
    echo "🔍 Debug steps:"
    echo "   1. Check logs: docker-compose -f docker-compose-enhanced.yml logs"
    echo "   2. Check disk space: df -h"
    echo "   3. Restart everything: docker-compose -f docker-compose-enhanced.yml down && ./fix_and_restart.sh"
fi

echo ""
echo "✅ Setup complete! Check the status above for next steps."
