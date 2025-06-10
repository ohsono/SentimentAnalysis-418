#!/bin/bash

# UCLA Sentiment Analysis - External Drive Deployment
# Fixed for external drive compatibility

set -e

echo "🚀 UCLA Sentiment Analysis - External Drive Deployment"
echo "======================================================="

# Use external drive compatible compose file
COMPOSE_FILE="docker-compose.external-fixed.yml"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose -f docker-compose.yml down 2>/dev/null || true
docker-compose -f docker-compose.fixed.yml down 2>/dev/null || true
docker-compose -f $COMPOSE_FILE down 2>/dev/null || true

# Clean up problematic files
echo "🧹 Cleaning up external drive files..."
find . -name "._*" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true

# Set Docker environment for external drives
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0

echo "🔨 Building services (external drive compatible)..."

# Build services individually to handle any issues
echo "Building database initializer..."
docker build -f Dockerfile.db-init -t db-init .

echo "Building model service..."
docker build --no-cache -f Dockerfile.model-service-fixed -t model-service-fixed .

echo "Building gateway service..."
docker build --no-cache -f Dockerfile.gateway-api-service -t gateway-api-service .

echo "Building worker service..."
docker build --no-cache -f Dockerfile.worker-scraper-service -t worker-scraper-service .

echo "Building dashboard service..."
docker build --no-cache -f Dockerfile.dashboard-service -t dashboard-service .

print_status "All services built successfully"

# Start services
echo "🚀 Starting services..."

echo "Starting infrastructure..."
docker-compose -f $COMPOSE_FILE up -d postgres redis

echo "Waiting for infrastructure..."
sleep 20

echo "Initializing database..."
docker-compose -f $COMPOSE_FILE up --no-deps db-init

echo "Starting application services..."
docker-compose -f $COMPOSE_FILE up -d model-service-fixed worker-scraper-service

echo "Waiting for services..."
sleep 15

echo "Starting gateway..."
docker-compose -f $COMPOSE_FILE up -d gateway-api-service

echo "Starting dashboard..."
docker-compose -f $COMPOSE_FILE up -d dashboard-service

echo "⏳ Waiting for all services to be ready..."
sleep 30

# Test the system
echo "🧪 Testing system..."

# Test model service
test_result=$(curl -s -X POST "http://localhost:8081/predict" \
     -H "Content-Type: application/json" \
     -d '{"text": "testtesttset", "model_name": "vader", "return_confidence": true}' || echo "error")

if echo "$test_result" | grep -q "sentiment"; then
    print_status "System test successful!"
else
    print_warning "System may still be starting up"
fi

echo ""
echo "🌐 Service URLs:"
echo "   📊 Gateway API:    http://localhost:8080"
echo "   📚 API Docs:       http://localhost:8080/docs"
echo "   🤖 Model Service:  http://localhost:8081"
echo "   👷 Worker Service: http://localhost:8082"
echo "   📈 Dashboard:      http://localhost:8501"

echo ""
echo "📋 Commands:"
echo "   View logs:         docker-compose -f $COMPOSE_FILE logs -f"
echo "   Stop services:     docker-compose -f $COMPOSE_FILE down"

echo ""
print_status "External drive deployment complete!"
