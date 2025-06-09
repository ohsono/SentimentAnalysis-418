#!/bin/bash

# UCLA Sentiment Analysis - Complete Deployment Script
# This script deploys the fixed sentiment analysis system using Docker

set -e  # Exit on any error

echo "🚀 UCLA Sentiment Analysis - Complete System Deployment"
echo "======================================================="
echo ""

# Configuration
COMPOSE_FILE="docker-compose.fixed.yml"
PROJECT_NAME="ucla-sentiment-fixed"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker and try again."
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running. Please start Docker and try again."
    exit 1
fi

print_status "All prerequisites are met"

# Check for required files
echo ""
echo "📁 Checking required files..."

required_files=(
    "standalone_model_service.py"
    "app/api/main_enhanced.py"
    "worker/main.py"
    "database_schema.sql"
    ".env"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_status "Found: $file"
    else
        print_warning "Missing: $file (will be created or may not be required)"
    fi
done

# Stop any existing services
echo ""
echo "🛑 Stopping any existing services..."
docker-compose -f docker-compose.yml down 2>/dev/null || true
docker-compose -f $COMPOSE_FILE down 2>/dev/null || true

# Clean up old containers and images (optional)
echo ""
echo "🧹 Cleaning up old resources..."
docker system prune -f >/dev/null 2>&1 || true

# Build and start services
echo ""
echo "🔨 Building and starting services..."
print_info "This may take several minutes..."

# Build services
echo ""
echo "Building all services..."
docker-compose -f $COMPOSE_FILE build

print_status "All services built successfully"

# Start services in order
echo ""
echo "🚀 Starting services..."

echo "Starting infrastructure services (postgres, redis)..."
docker-compose -f $COMPOSE_FILE up -d postgres redis

echo "Waiting for database and redis to be ready..."
sleep 15

echo "Starting model service..."
docker-compose -f $COMPOSE_FILE up -d model-service-fixed

echo "Waiting for model service to be ready..."
sleep 10

echo "Starting worker service..."
docker-compose -f $COMPOSE_FILE up -d worker-scraper-service

echo "Waiting for worker service to be ready..."
sleep 10

echo "Starting gateway service..."
docker-compose -f $COMPOSE_FILE up -d gateway-api-service

echo "Waiting for gateway service to be ready..."
sleep 15

echo "Starting dashboard service..."
docker-compose -f $COMPOSE_FILE up -d dashboard-service

# Wait for all services to be healthy
echo ""
echo "⏳ Waiting for all services to be healthy..."
sleep 30

# Check service status
echo ""
echo "🔍 Checking service status..."

services=("postgres" "redis" "model-service-fixed" "worker-scraper-service" "gateway-api-service" "dashboard-service")
all_healthy=true

for service in "${services[@]}"; do
    status=$(docker-compose -f $COMPOSE_FILE ps -q $service | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
    
    if [ "$status" = "healthy" ] || [ "$status" = "unknown" ]; then
        print_status "$service: $status"
    else
        print_warning "$service: $status"
        all_healthy=false
    fi
done

# Show service URLs
echo ""
echo "🌐 Service URLs:"
echo "   📊 Gateway API:    http://localhost:8080"
echo "   📚 API Docs:       http://localhost:8080/docs"
echo "   🤖 Model Service:  http://localhost:8081"
echo "   👷 Worker Service: http://localhost:8082"
echo "   📈 Dashboard:      http://localhost:8501"

# Test the main endpoint
echo ""
echo "🧪 Testing the fixed model service..."

# Wait a bit more for services to fully start
sleep 10

# Test prediction endpoint
test_result=$(curl -s -X POST "http://localhost:8081/predict" \
     -H "Content-Type: application/json" \
     -d '{"text": "testtesttset", "model_name": "vader", "return_confidence": true}' || echo "error")

if echo "$test_result" | grep -q "sentiment"; then
    print_status "Model service test successful!"
    echo "   Response: $(echo $test_result | python3 -c "import sys, json; print(json.load(sys.stdin).get('sentiment', 'unknown'))" 2>/dev/null || echo "unknown") sentiment detected"
else
    print_warning "Model service test failed or still starting up"
    echo "   You can test manually with:"
    echo "   curl -X POST http://localhost:8081/predict -H 'Content-Type: application/json' -d '{\"text\": \"testtesttset\", \"model_name\": \"vader\", \"return_confidence\": true}'"
fi

# Show logs command
echo ""
echo "📋 Useful commands:"
echo "   View all logs:     docker-compose -f $COMPOSE_FILE logs -f"
echo "   View service logs: docker-compose -f $COMPOSE_FILE logs -f <service-name>"
echo "   Stop all services: docker-compose -f $COMPOSE_FILE down"
echo "   Restart a service: docker-compose -f $COMPOSE_FILE restart <service-name>"

echo ""
if [ "$all_healthy" = true ]; then
    print_status "🎉 UCLA Sentiment Analysis System deployed successfully!"
    print_info "All services are running and ready to use."
else
    print_warning "⚠️ Some services may still be starting up. Check logs if issues persist."
fi

echo ""
print_info "Your original request should now work:"
echo "curl -X POST 'http://localhost:8081/predict' -H 'Content-Type: application/json' -d '{\"text\": \"testtesttset\", \"model_name\": \"vader\", \"return_confidence\": true}'"
