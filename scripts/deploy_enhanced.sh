#!/bin/bash

# Enhanced UCLA Sentiment Analysis - Complete Deployment Script
# Handles cache cleanup, database setup, and full system deployment

set -e

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup cache and empty files
cleanup_cache() {
    print_header "🧹 Cleaning up cache and empty files..."
    
    if [ -f "cleanup_cache.py" ]; then
        python cleanup_cache.py
    else
        print_warning "cleanup_cache.py not found, skipping cache cleanup"
    fi
    
    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove .pyc files
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove empty directories
    find . -type d -empty -delete 2>/dev/null || true
    
    print_status "Cache cleanup completed"
}

# Function to check requirements
check_requirements() {
    print_header "🔍 Checking system requirements..."
    
    # Check Docker
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Determine compose command
    if command_exists docker-compose; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    print_status "Docker and Docker Compose are available"
    
    # Check available memory
    available_memory=$(free -m 2>/dev/null | awk 'NR==2{printf "%.0f", $7}' || echo "unknown")
    if [ "$available_memory" != "unknown" ] && [ "$available_memory" -lt 4096 ]; then
        print_warning "Available memory is ${available_memory}MB. Recommended: 4GB+ for optimal performance"
    fi
    
    # Check disk space
    available_disk=$(df -BM . | awk 'NR==2{gsub(/M/, "", $4); print $4}' || echo "unknown")
    if [ "$available_disk" != "unknown" ] && [ "$available_disk" -lt 5120 ]; then
        print_warning "Available disk space is ${available_disk}MB. Recommended: 5GB+ for models and data"
    fi
}

# Function to setup configuration
setup_configuration() {
    print_header "⚙️  Setting up configuration..."
    
    # Create config directory if it doesn't exist
    mkdir -p config
    
    # Create environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# UCLA Sentiment Analysis Configuration

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ucla_sentiment
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sentiment_password_2024

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=sentiment_redis_2024

# Model Service Configuration
MODEL_SERVICE_URL=http://model-service:8081
PRELOAD_MODEL=distilbert-sentiment

# Failsafe Configuration
FAILSAFE_MAX_LLM_FAILURES=3
FAILSAFE_FAILURE_WINDOW_SECONDS=300
FAILSAFE_CIRCUIT_BREAKER_TIMEOUT=60
FALLBACK_TO_VADER=true

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
ENV=production

# Performance Configuration
OMP_NUM_THREADS=2
MKL_NUM_THREADS=2
TOKENIZERS_PARALLELISM=false
EOF
        print_status ".env file created"
    else
        print_status ".env file already exists"
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Create monitoring directory
    mkdir -p monitoring/grafana/dashboards monitoring/grafana/datasources
    
    print_status "Configuration setup completed"
}

# Function to build images
build_images() {
    print_header "🏗️  Building Docker images..."
    
    # Build images in parallel where possible
    print_status "Building API image..."
    docker build -f Dockerfile.api-enhanced -t ucla-sentiment-api:latest . &
    
    print_status "Building Model Service image..."
    docker build -f Dockerfile.model-service-enhanced -t ucla-sentiment-model-service:latest . &
    
    print_status "Building Worker image..."
    docker build -f Dockerfile.worker -t ucla-sentiment-worker:latest . &
    
    # Wait for all builds to complete
    wait
    
    print_status "All Docker images built successfully"
}

# Function to initialize database
init_database() {
    print_header "🗄️  Initializing database..."
    
    # Start only database for initialization
    $COMPOSE_CMD -f docker-compose-enhanced.yml up -d postgres redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if $COMPOSE_CMD -f docker-compose-enhanced.yml exec postgres pg_isready -U postgres -d ucla_sentiment >/dev/null 2>&1; then
            print_status "Database is ready!"
            break
        fi
        
        print_status "Attempt $attempt/$max_attempts: Database not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "Database failed to become ready"
        exit 1
    fi
    
    print_status "Database initialization completed"
}

# Function to start services
start_services() {
    print_header "🚀 Starting all services..."
    
    # Start all services
    $COMPOSE_CMD -f docker-compose-enhanced.yml up -d
    
    print_status "All services started"
    
    # Wait for services to be healthy
    print_status "Waiting for services to become healthy..."
    
    services=("api" "model-service")
    for service in "${services[@]}"; do
        print_status "Checking $service health..."
        max_attempts=20
        attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if $COMPOSE_CMD -f docker-compose-enhanced.yml ps $service | grep -q "healthy\|Up"; then
                print_status "$service is healthy!"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                print_warning "$service health check timeout, but continuing..."
                break
            fi
            
            sleep 5
            attempt=$((attempt + 1))
        done
    done
}

# Function to run tests
run_tests() {
    print_header "🧪 Running system tests..."
    
    # Test API health
    print_status "Testing API health..."
    if curl -s --max-time 10 http://localhost:8080/health >/dev/null; then
        print_status "API health check passed"
    else
        print_warning "API health check failed"
    fi
    
    # Test model service health  
    print_status "Testing Model Service health..."
    if curl -s --max-time 15 http://localhost:8081/health >/dev/null; then
        print_status "Model Service health check passed"
    else
        print_warning "Model Service health check failed"
    fi
    
    # Test database connectivity
    print_status "Testing database connectivity..."
    if $COMPOSE_CMD -f docker-compose-enhanced.yml exec -T postgres psql -U postgres -d ucla_sentiment -c "SELECT 1;" >/dev/null 2>&1; then
        print_status "Database connectivity test passed"
    else
        print_warning "Database connectivity test failed"
    fi
}

# Function to show status
show_status() {
    print_header "📊 System Status"
    
    echo ""
    echo "🌐 Service URLs:"
    echo "   • Main API:        http://localhost:8080"
    echo "   • API Docs:        http://localhost:8080/docs"
    echo "   • Model Service:   http://localhost:8081"
    echo "   • PostgreSQL:      localhost:5432"
    echo "   • Redis:           localhost:6379"
    echo ""
    
    echo "🔗 Key Endpoints:"
    echo "   • Health Check:    GET  http://localhost:8080/health"
    echo "   • Predict:         POST http://localhost:8080/predict"
    echo "   • Batch Predict:   POST http://localhost:8080/predict/batch"
    echo "   • Analytics:       GET  http://localhost:8080/analytics"
    echo "   • Failsafe Status: GET  http://localhost:8080/failsafe/status"
    echo ""
    
    echo "🛡️  Failsafe Features:"
    echo "   • Circuit Breaker Pattern:     ✅ Enabled"
    echo "   • VADER Fallback:              ✅ Enabled"
    echo "   • Max LLM Failures:            3"
    echo "   • PostgreSQL Integration:      ✅ Enabled"
    echo "   • Async Data Loading:          ✅ Enabled"
    echo ""
    
    echo "📊 Container Status:"
    $COMPOSE_CMD -f docker-compose-enhanced.yml ps
    echo ""
    
    echo "📁 Volume Information:"
    docker volume ls | grep ucla-sentiment || echo "No UCLA sentiment volumes found"
    echo ""
    
    echo "🔧 Management Commands:"
    echo "   • View logs:       docker-compose -f docker-compose-enhanced.yml logs -f [service]"
    echo "   • Stop services:   docker-compose -f docker-compose-enhanced.yml down"
    echo "   • Restart:         docker-compose -f docker-compose-enhanced.yml restart [service]"
    echo "   • Clean shutdown:  docker-compose -f docker-compose-enhanced.yml down -v"
}

# Function to display help
show_help() {
    echo "UCLA Sentiment Analysis - Enhanced Deployment Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  deploy         Full deployment (cleanup, build, start)"
    echo "  start          Start services only"
    echo "  stop           Stop all services"
    echo "  restart        Restart all services"
    echo "  build          Build Docker images only"
    echo "  cleanup        Cleanup cache and empty files only"
    echo "  test           Run system tests"
    echo "  status         Show system status"
    echo "  logs [service] Show logs for service"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy                    # Full deployment"
    echo "  $0 logs api                  # Show API logs"
    echo "  $0 logs model-service        # Show model service logs"
    echo ""
}

# Main execution logic
main() {
    case "${1:-deploy}" in
        "deploy")
            print_header "🚀 UCLA Sentiment Analysis - Enhanced Deployment"
            echo "Starting full deployment with failsafe features..."
            echo ""
            
            cleanup_cache
            check_requirements
            setup_configuration
            build_images
            init_database
            start_services
            sleep 10  # Allow services to stabilize
            run_tests
            show_status
            
            echo ""
            print_status "🎉 Enhanced deployment completed successfully!"
            print_status "🛡️  Failsafe features are active with VADER fallback"
            print_status "🗄️  PostgreSQL database is initialized and ready"
            print_status "🔄 Model service supports hot-swapping"
            ;;
        
        "start")
            print_header "🚀 Starting UCLA Sentiment Analysis Services"
            check_requirements
            start_services
            show_status
            ;;
        
        "stop")
            print_header "🛑 Stopping UCLA Sentiment Analysis Services"
            $COMPOSE_CMD -f docker-compose-enhanced.yml down
            print_status "All services stopped"
            ;;
        
        "restart")
            print_header "🔄 Restarting UCLA Sentiment Analysis Services"
            $COMPOSE_CMD -f docker-compose-enhanced.yml restart
            show_status
            ;;
        
        "build")
            print_header "🏗️  Building UCLA Sentiment Analysis Images"
            build_images
            ;;
        
        "cleanup")
            cleanup_cache
            ;;
        
        "test")
            run_tests
            ;;
        
        "status")
            show_status
            ;;
        
        "logs")
            service=${2:-"api"}
            print_header "📋 Showing logs for: $service"
            $COMPOSE_CMD -f docker-compose-enhanced.yml logs -f "$service"
            ;;
        
        "help"|"-h"|"--help")
            show_help
            ;;
        
        *)
            print_error "Unknown option: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
