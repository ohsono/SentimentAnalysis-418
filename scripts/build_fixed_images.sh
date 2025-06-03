#!/bin/bash

# Enhanced Docker Build Script for UCLA Sentiment Analysis
# Fixes GPG signature issues and builds all images

set -e  # Exit on any error

echo "🚀 Starting Docker build process..."

# Navigate to project directory
cd ~/Project/UCLA-MASDS/SentimentAnalysis-418

echo "🧹 Cleaning up Docker to free space..."
docker system prune -a --volumes -f
docker builder prune -a -f

echo "📊 Checking available disk space..."
echo "Docker disk usage:"
docker system df
echo ""
echo "System disk usage:"
df -h | head -5

echo ""
echo "🔨 Building Docker images (this may take several minutes)..."

# Build images one by one to avoid memory issues
echo "📦 Building API service..."
docker build -f Dockerfile.api-enhanced -t ucla-sentiment-api:latest . --no-cache

echo "📦 Building Model service..."
docker build -f Dockerfile.model-service-enhanced -t ucla-sentiment-model-service:latest . --no-cache

echo "📦 Building Worker service..."
docker build -f Dockerfile.worker -t ucla-sentiment-worker:latest . --no-cache

echo ""
echo "✅ All Docker images built successfully!"
echo ""
echo "📋 Built images:"
docker images | grep ucla-sentiment

echo ""
echo "🚀 Ready to start with: docker-compose -f docker-compose-enhanced.yml up -d"
echo "   Or for core services only: docker-compose -f docker-compose-enhanced.yml up -d postgres redis api model-service worker"
