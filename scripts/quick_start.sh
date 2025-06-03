#!/bin/bash

# Quick Start Script for UCLA Sentiment Analysis Docker Deployment
# One-command setup for the entire microservices architecture

set -e

echo "🚀 UCLA Sentiment Analysis - Quick Start"
echo "========================================"

# Colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop first."
        echo "Visit: https://www.docker.com/products/docker-desktop/"
        exit 1
    fi
    
    if ! docker ps &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    fi
    
    print_success "Docker is available and running"
}

# Check Docker Compose
check_compose() {
    print_status "Checking Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        print_success "Using docker-compose"
    elif command -v docker compose &> /dev/null; then
        COMPOSE_CMD="docker compose"
        print_success "Using docker compose"
    else
        print_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
}

# Make scripts executable
make_executable() {
    print_status "Making scripts executable..."
    chmod +x docker_build.sh 2>/dev/null || true
    chmod +x docker_run.sh 2>/dev/null || true
    print_success "Scripts made executable"
}

# Build containers
build_containers() {
    print_status "Building Docker containers..."
    print_warning "This may take a few minutes for the first build..."
    
    # Build API container (lightweight)
    print_status "Building API container (lightweight)..."
    if docker build -f Dockerfile.api -t ucla-sentiment-api:latest . --quiet; then
        print_success "API container built successfully"
    else
        print_error "Failed to build API container"
        exit 1
    fi
    
    # Build Model Service container
    print_status "Building Model Service container..."
    if docker build -f Dockerfile.model-service -t ucla-sentiment-model-service:latest . --quiet; then
        print_success "Model Service container built successfully"
    else
        print_error "Failed to build Model Service container"
        exit 1
    fi
}

# Start services
start_services() {
    print_status "Starting microservices..."
    
    if $COMPOSE_CMD up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        # Check API
        if curl -f http://localhost:8080/health &>/dev/null; then
            print_success "API service is ready!"
            break
        fi
        
        print_status "Waiting for API service... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_warning "API service took longer than expected to start"
    fi
    
    # Check Model Service (may take longer)
    print_status "Checking Model Service (may take 1-2 minutes to download models)..."
    local model_attempt=1
    local model_max_attempts=60
    
    while [ $model_attempt -le $model_max_attempts ]; do
        if curl -f http://localhost:8081/health &>/dev/null; then
            print_success "Model Service is ready!"
            break
        fi
        
        if [ $((model_attempt % 10)) -eq 0 ]; then
            print_status "Model Service still starting... (downloading models, attempt $model_attempt/$model_max_attempts)"
        fi
        
        sleep 2
        ((model_attempt++))
    done
    
    if [ $model_attempt -gt $model_max_attempts ]; then
        print_warning "Model Service is taking longer to start (this is normal for first run)"
    fi
}

# Test the deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Test API health
    if curl -f http://localhost:8080/health &>/dev/null; then
        print_success "✅ API health check passed"
    else
        print_warning "❌ API health check failed"
    fi
    
    # Test simple prediction
    if curl -X POST http://localhost:8080/predict \
        -H "Content-Type: application/json" \
        -d '{"text": "UCLA is amazing!"}' \
        -f &>/dev/null; then
        print_success "✅ Simple sentiment analysis working"
    else
        print_warning "❌ Simple sentiment analysis failed"
    fi
    
    # Test ML prediction (may not be ready immediately)
    if curl -X POST http://localhost:8080/predict/llm \
        -H "Content-Type: application/json" \
        -d '{"text": "UCLA is amazing!", "model": "distilbert-sentiment"}' \
        -f &>/dev/null; then
        print_success "✅ ML sentiment analysis working"
    else
        print_warning "⚠️  ML sentiment analysis not ready yet (using fallback)"
    fi
}

# Show status
show_status() {
    echo ""
    echo "🐳 Container Status:"
    $COMPOSE_CMD ps
    
    echo ""
    echo "🌐 Access Points:"
    echo "• Main API: http://localhost:8080"
    echo "• API Documentation: http://localhost:8080/docs"
    echo "• Model Service: http://localhost:8081"
    echo "• Model Service Docs: http://localhost:8081/docs"
    
    echo ""
    echo "💡 Management Commands:"
    echo "• View logs: $COMPOSE_CMD logs -f"
    echo "• Stop services: $COMPOSE_CMD down"
    echo "• Restart: $COMPOSE_CMD restart"
    echo "• Full test: python test_docker_deployment.py"
}

# Main execution
main() {
    echo ""
    print_status "Starting quick setup for UCLA Sentiment Analysis..."
    
    # Step 1: Check prerequisites
    check_docker
    check_compose
    
    # Step 2: Prepare environment
    make_executable
    
    # Step 3: Build containers
    build_containers
    
    # Step 4: Start services
    start_services
    
    # Step 5: Wait for readiness
    wait_for_services
    
    # Step 6: Test deployment
    test_deployment
    
    # Step 7: Show status and next steps
    show_status
    
    echo ""
    print_success "🎉 Quick start completed!"
    echo ""
    echo "🎯 Your UCLA Sentiment Analysis API is now running!"
    echo "📊 Both simple and ML-powered sentiment analysis available"
    echo "🔄 Automatic fallback system ensures high availability"
    echo ""
    echo "⚡ Ready for:"
    echo "• Real-time sentiment analysis"
    echo "• Batch processing"
    echo "• UCLA social media monitoring"
    echo "• Dashboard integration"
    echo ""
    echo "🚀 Happy analyzing! 🎓"
}

# Handle script interruption
trap 'echo ""; print_warning "Setup interrupted by user"; exit 1' INT

# Run main function
main "$@"
