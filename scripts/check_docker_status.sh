#!/bin/bash

# Docker Status and Diagnostics Script
# Checks container status and provides debugging info

echo "🔍 Checking Docker container status..."

cd ~/Project/UCLA-MASDS/SentimentAnalysis-418

echo "📊 Current running containers:"
docker ps -a

echo ""
echo "📋 Docker Compose services status:"
if [ -f docker-compose-enhanced.yml ]; then
    docker-compose -f docker-compose-enhanced.yml ps
else
    echo "❌ docker-compose-enhanced.yml not found"
fi

echo ""
echo "🔍 Checking specific service logs..."

echo "--- API Service Logs (last 50 lines) ---"
docker-compose -f docker-compose-enhanced.yml logs --tail=50 api 2>/dev/null || echo "❌ API service not found or not running"

echo ""
echo "--- Model Service Logs (last 50 lines) ---"
docker-compose -f docker-compose-enhanced.yml logs --tail=50 model-service 2>/dev/null || echo "❌ Model service not found or not running"

echo ""
echo "--- Worker Service Logs (last 50 lines) ---"
docker-compose -f docker-compose-enhanced.yml logs --tail=50 worker 2>/dev/null || echo "❌ Worker service not found or not running"

echo ""
echo "--- PostgreSQL Logs (last 20 lines) ---"
docker-compose -f docker-compose-enhanced.yml logs --tail=20 postgres 2>/dev/null || echo "❌ PostgreSQL service not found or not running"

echo ""
echo "--- Redis Logs (last 20 lines) ---"
docker-compose -f docker-compose-enhanced.yml logs --tail=20 redis 2>/dev/null || echo "❌ Redis service not found or not running"

echo ""
echo "🌐 Network connectivity tests:"
echo "Testing localhost ports..."

# Check if ports are responding
for port in 8080 8081 5432 6379; do
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ Port $port is open"
    else
        echo "❌ Port $port is not responding"
    fi
done

echo ""
echo "🔍 Docker network inspection:"
docker network ls | grep sentiment 2>/dev/null || echo "❌ No sentiment network found"

echo ""
echo "💾 Available disk space:"
df -h | head -3

echo ""
echo "🚀 Quick fix commands:"
echo "1. Restart all services: docker-compose -f docker-compose-enhanced.yml down && docker-compose -f docker-compose-enhanced.yml up -d"
echo "2. Rebuild and restart: docker-compose -f docker-compose-enhanced.yml down && docker-compose -f docker-compose-enhanced.yml build --no-cache && docker-compose -f docker-compose-enhanced.yml up -d"
echo "3. Check individual service: docker-compose -f docker-compose-enhanced.yml logs -f api"
