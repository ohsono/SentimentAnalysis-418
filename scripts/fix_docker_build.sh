#!/bin/bash

# Docker Build Troubleshooting Script for UCLA Sentiment Analysis
# Diagnoses and fixes common Docker build issues

set -e

echo "🔧 UCLA Sentiment Analysis - Docker Build Troubleshooting"
echo "========================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to test network connectivity
test_network() {
    print_status "Testing network connectivity..."
    
    if ping -c 1 8.8.8.8 &>/dev/null; then
        print_success "Internet connectivity: OK"
    else
        print_error "No internet connectivity"
        return 1
    fi
    
    if ping -c 1 deb.debian.org &>/dev/null; then
        print_success "Debian repositories: Reachable"
    else
        print_warning "Debian repositories: Not reachable"
    fi
}

# Function to check Docker daemon
check_docker() {
    print_status "Checking Docker daemon..."
    
    if docker info &>/dev/null; then
        print_success "Docker daemon: Running"
        
        # Check Docker version
        docker_version=$(docker --version)
        print_status "Docker version: $docker_version"
        
        # Check available space
        available_space=$(df -h . | awk 'NR==2 {print $4}')
        print_status "Available disk space: $available_space"
        
    else
        print_error "Docker daemon not running or not accessible"
        return 1
    fi
}

# Function to clean Docker cache
clean_docker_cache() {
    print_status "Cleaning Docker build cache..."
    
    docker builder prune -f &>/dev/null || true
    docker system prune -f &>/dev/null || true
    
    print_success "Docker cache cleaned"
}

# Function to try different build strategies
try_build_strategies() {
    print_status "Trying different build strategies..."
    
    strategies=(
        "minimal:Dockerfile.api-minimal:Minimal build without system packages"
        "robust:Dockerfile.api-robust:Robust build with error handling"
        "original:Dockerfile.api:Original build with fixes"
    )
    
    for strategy in "${strategies[@]}"; do
        IFS=':' read -r name dockerfile description <<< "$strategy"
        
        echo ""
        print_status "Strategy: $description"
        print_status "Using: $dockerfile"
        
        if [ ! -f "$dockerfile" ]; then
            print_warning "Dockerfile $dockerfile not found, skipping..."
            continue
        fi
        
        print_status "Building API container with $name strategy..."
        
        if docker build -f "$dockerfile" -t "ucla-sentiment-api:$name" . --no-cache 2>/dev/null; then
            print_success "✅ $description - BUILD SUCCESSFUL!"
            echo ""
            print_success "🎉 Found working build strategy: $description"
            print_status "Image tagged as: ucla-sentiment-api:$name"
            
            # Update docker-compose to use this image
            if [ -f "docker-compose.yml" ]; then
                print_status "Updating docker-compose.yml to use working image..."
                sed -i.bak "s/ucla-sentiment-api:latest/ucla-sentiment-api:$name/g" docker-compose.yml
                print_success "Updated docker-compose.yml"
            fi
            
            return 0
        else
            print_error "❌ $description - BUILD FAILED"
        fi
    done
    
    print_error "All build strategies failed"
    return 1
}

# Function to create alternative minimal Dockerfile
create_minimal_dockerfile() {
    print_status "Creating ultra-minimal Dockerfile..."
    
    cat > Dockerfile.api-ultramin << 'EOF'
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1 MODEL_SERVICE_MODE=external
COPY requirements_docker.txt .
RUN pip install --no-cache-dir -r requirements_docker.txt
RUN mkdir -p /app/app/api /app/app/ml
COPY app/ /app/app/
RUN groupadd -r appuser && useradd -r -g appuser appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "app.api.main_docker:app", "--host", "0.0.0.0", "--port", "8080"]
EOF
    
    print_success "Created ultra-minimal Dockerfile: Dockerfile.api-ultramin"
}

# Function to test a specific build
test_build() {
    local dockerfile=$1
    local tag=$2
    
    print_status "Testing build with $dockerfile..."
    
    if docker build -f "$dockerfile" -t "$tag" . --progress=plain --no-cache; then
        print_success "Build successful with $dockerfile"
        return 0
    else
        print_error "Build failed with $dockerfile"
        return 1
    fi
}

# Function to show solutions
show_solutions() {
    echo ""
    print_status "🛠️ AVAILABLE SOLUTIONS:"
    echo ""
    
    echo "1. 🚀 Use Ultra-Minimal Build (Recommended)"
    echo "   docker build -f Dockerfile.api-minimal -t ucla-sentiment-api:latest ."
    echo ""
    
    echo "2. 🔧 Use Robust Build"
    echo "   docker build -f Dockerfile.api-robust -t ucla-sentiment-api:latest ."
    echo ""
    
    echo "3. 🌐 Build with Different Network"
    echo "   docker build --network=host -f Dockerfile.api -t ucla-sentiment-api:latest ."
    echo ""
    
    echo "4. 🧹 Clean Build (No Cache)"
    echo "   docker build --no-cache -f Dockerfile.api-minimal -t ucla-sentiment-api:latest ."
    echo ""
    
    echo "5. 📦 Use Different Base Image"
    echo "   # Edit Dockerfile to use python:3.11-alpine instead of python:3.11-slim"
    echo ""
}

# Function to fix and rebuild
fix_and_rebuild() {
    print_status "Attempting automatic fix and rebuild..."
    
    # Clean Docker cache
    clean_docker_cache
    
    # Create minimal dockerfile if it doesn't exist
    if [ ! -f "Dockerfile.api-minimal" ]; then
        create_minimal_dockerfile
    fi
    
    # Try building with minimal approach
    if test_build "Dockerfile.api-minimal" "ucla-sentiment-api:latest"; then
        print_success "✅ Automatic fix successful!"
        print_success "Built API container using minimal approach"
        
        # Now try to build model service
        print_status "Building model service container..."
        if docker build -f Dockerfile.model-service -t ucla-sentiment-model-service:latest .; then
            print_success "✅ Model service container built successfully"
            
            print_status "Starting services..."
            if docker-compose up -d; then
                print_success "🎉 Services started successfully!"
                print_status "API: http://localhost:8080"
                print_status "Docs: http://localhost:8080/docs"
                return 0
            fi
        fi
    fi
    
    return 1
}

# Main troubleshooting function
main() {
    echo ""
    print_status "Starting Docker build troubleshooting..."
    
    # Step 1: Basic checks
    print_status "Step 1: Basic system checks"
    check_docker || exit 1
    test_network || print_warning "Network issues detected"
    
    # Step 2: Try automatic fix
    print_status "Step 2: Attempting automatic fix"
    if fix_and_rebuild; then
        print_success "🎉 Problem solved automatically!"
        exit 0
    fi
    
    # Step 3: Try different strategies
    print_status "Step 3: Trying different build strategies"
    if try_build_strategies; then
        print_success "🎉 Found working build strategy!"
        exit 0
    fi
    
    # Step 4: Show manual solutions
    print_status "Step 4: Manual solutions"
    show_solutions
    
    echo ""
    print_warning "Automatic fixes didn't work. Try the manual solutions above."
    print_status "For immediate testing, you can also run the API locally:"
    print_status "python -m uvicorn app.api.main_docker:app --host 0.0.0.0 --port 8080"
}

# Handle script arguments
case "${1:-auto}" in
    "auto")
        main
        ;;
    "clean")
        clean_docker_cache
        print_success "Docker cache cleaned"
        ;;
    "test")
        test_network && check_docker
        ;;
    "minimal")
        create_minimal_dockerfile
        test_build "Dockerfile.api-ultramin" "ucla-sentiment-api:minimal"
        ;;
    "solutions")
        show_solutions
        ;;
    *)
        echo "Usage: $0 [auto|clean|test|minimal|solutions]"
        echo "  auto     - Run full troubleshooting (default)"
        echo "  clean    - Clean Docker cache"
        echo "  test     - Test network and Docker"
        echo "  minimal  - Create and test minimal build"
        echo "  solutions - Show manual solutions"
        ;;
esac
