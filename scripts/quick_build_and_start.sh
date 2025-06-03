#!/bin/bash

# Quick Docker Compose Build Script
# Alternative method using docker-compose

set -e

echo "🚀 Building with Docker Compose..."

cd ~/Project/UCLA-MASDS/SentimentAnalysis-418

echo "🧹 Cleaning Docker cache..."
docker system prune -f
docker builder prune -f

echo "🔨 Building all services with docker-compose..."
docker-compose -f docker-compose-enhanced.yml build --no-cache

echo "✅ Build complete! Starting services..."
docker-compose -f docker-compose-enhanced.yml up -d postgres redis

echo "⏳ Waiting for database to be ready..."
sleep 10

echo "🚀 Starting main services..."
docker-compose -f docker-compose-enhanced.yml up -d api model-service worker

echo "✅ All services started!"
echo "🌐 API available at: http://localhost:8080"
echo "🤖 Model service at: http://localhost:8081"
echo "📊 Check status: docker-compose -f docker-compose-enhanced.yml ps"
