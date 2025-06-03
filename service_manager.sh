#!/bin/bash

# UCLA Sentiment Analysis - Service Management Script
# This script helps build, start, stop, and check status of all microservices

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  UCLA Sentiment Analysis Service Manager${NC}"
echo -e "${BLUE}============================================${NC}"

# Function to display usage information
show_usage() {
    echo -e "\nUsage: $0 [command]"
    echo -e "\nAvailable commands:"
    echo -e "  ${GREEN}build${NC}        - Build all Docker images"
    echo -e "  ${GREEN}start${NC}        - Start all services"
    echo -e "  ${GREEN}stop${NC}         - Stop all services"
    echo -e "  ${GREEN}restart${NC}      - Restart all services"
    echo -e "  ${GREEN}status${NC}       - Check status of all services"
    echo -e "  ${GREEN}logs [service]${NC} - View logs for a specific service"
    echo -e "  ${GREEN}test${NC}         - Run tests against running services"
    echo -e "  ${GREEN}clean${NC}        - Remove all containers and images"
    echo -e "  ${GREEN}help${NC}         - Display this help message"
    echo
    echo -e "Available services for logs command:"
    echo -e "  ${YELLOW}gateway-api${NC}, ${YELLOW}model-service-api${NC}, ${YELLOW}worker-scraper-api${NC}, ${YELLOW}dashboard-service${NC}, ${YELLOW}postgres${NC}, ${YELLOW}redis${NC}"
    echo
}

# Function to build all Docker images
build_services() {
    echo -e "${BLUE}Building all services...${NC}"
    find . -name '._*' -delete
    echo -e "${YELLOW}Building gateway-api...${NC}"
    docker build -t ucla/gateway-api -f Dockerfile.gateway-api .
    
    echo -e "${YELLOW}Building model-service-api...${NC}"
    docker build -t ucla/model-service-api -f Dockerfile.model-service .
    
    echo -e "${YELLOW}Building worker-scraper-api...${NC}"
    docker build -t ucla/worker-scraper-api -f Dockerfile.worker .
    
    echo -e "${YELLOW}Building dashboard-service...${NC}"
    docker build -t ucla/dashboard-service -f Dockerfile.dashboard .
    
    echo -e "${GREEN}All services built successfully!${NC}"
}

# Function to start all services
start_services() {
    echo -e "${BLUE}Starting all services...${NC}"
    docker-compose up -d
    
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 5
    
    check_services_status
}

# Function to stop all services
stop_services() {
    echo -e "${BLUE}Stopping all services...${NC}"
    docker-compose down
    echo -e "${GREEN}All services stopped.${NC}"
}

# Function to restart all services
restart_services() {
    echo -e "${BLUE}Restarting all services...${NC}"
    docker-compose restart
    
    echo -e "${YELLOW}Waiting for services to restart...${NC}"
    sleep 5
    
    check_services_status
}

# Function to check status of all services
check_services_status() {
    echo -e "${BLUE}Checking status of all services...${NC}"
    docker-compose ps
}

# Function to view logs for a specific service
view_service_logs() {
    service="$1"
    
    case "$service" in
        "gateway-api")
            container="ucla_gateway_api"
            ;;
        "model-service-api")
            container="ucla_model_service"
            ;;
        "worker-scraper-api")
            container="ucla_worker_service"
            ;;
        "dashboard-service")
            container="ucla_dashboard"
            ;;
        "postgres")
            container="ucla_sentiment_db"
            ;;
        "redis")
            container="ucla_sentiment_redis"
            ;;
        *)
            echo -e "${RED}Invalid service name: $service${NC}"
            show_usage
            return 1
            ;;
    esac
    
    echo -e "${BLUE}Viewing logs for $service...${NC}"
    docker logs -f "$container"
}

# Function to run tests
run_tests() {
    echo -e "${BLUE}Running tests against services...${NC}"
    python tests/test_services.py
}

# Function to clean up all containers and images
clean_services() {
    echo -e "${BLUE}Stopping all services...${NC}"
    docker-compose down
    
    echo -e "${YELLOW}Removing all service containers...${NC}"
    docker rm -f ucla_gateway_api ucla_model_service ucla_worker_service ucla_dashboard ucla_sentiment_db ucla_sentiment_redis 2>/dev/null || true
    
    echo -e "${YELLOW}Removing all service images...${NC}"
    docker rmi ucla/gateway-api ucla/model-service-api ucla/worker-scraper-api ucla/dashboard-service 2>/dev/null || true
    
    echo -e "${YELLOW}Pruning unused volumes...${NC}"
    docker volume prune -f
    
    echo -e "${GREEN}Clean up complete.${NC}"
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

command="$1"

case "$command" in
    "build")
        build_services
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        check_services_status
        ;;
    "logs")
        if [ $# -lt 2 ]; then
            echo -e "${RED}Error: Missing service name for logs command${NC}"
            show_usage
            exit 1
        fi
        view_service_logs "$2"
        ;;
    "test")
        run_tests
        ;;
    "clean")
        clean_services
        ;;
    "help")
        show_usage
        ;;
    *)
        echo -e "${RED}Invalid command: $command${NC}"
        show_usage
        exit 1
        ;;
esac

exit 0
