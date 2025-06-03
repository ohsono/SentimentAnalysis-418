#!/bin/bash

# UCLA Sentiment Analysis - Docker Run Script
# Starts the microservices with proper networking

set -e

echo "🚀 UCLA Sentiment Analysis - Docker Run Script"
echo "==============================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Docker Compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo -e "${BLUE}Using: ${COMPOSE_CMD}${NC}"

# Function to show container status
show_status() {
    echo -e "${BLUE}Container Status:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}Recent logs:${NC}"
    ${COMPOSE_CMD} logs --tail=10
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    ${COMPOSE_CMD} down
}

# Function to clean up
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    ${COMPOSE_CMD} down --volumes --remove-orphans
}

# Parse command line arguments
case "${1:-up}" in
    "up"|"start")
        echo -e "${GREEN}Starting UCLA Sentiment Analysis services...${NC}"
        ${COMPOSE_CMD} up -d
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Services started successfully!${NC}"
            echo ""
            show_status
            echo ""
            echo -e "${GREEN}🌐 Access Points:${NC}"
            echo "• Main API: http://localhost:8080"
            echo "• API Documentation: http://localhost:8080/docs"
            echo "• Model Service: http://localhost:8081"
            echo "• Model Service Docs: http://localhost:8081/docs"
            echo ""
            echo -e "${BLUE}💡 Commands:${NC}"
            echo "• View logs: ${COMPOSE_CMD} logs -f"
            echo "• Stop services: ./docker_run.sh stop"
            echo "• View status: ./docker_run.sh status"
        else
            echo -e "${RED}❌ Failed to start services${NC}"
            exit 1
        fi
        ;;
    
    "stop")
        stop_services
        echo -e "${GREEN}✅ Services stopped${NC}"
        ;;
    
    "restart")
        echo -e "${YELLOW}Restarting services...${NC}"
        stop_services
        sleep 2
        ${COMPOSE_CMD} up -d
        echo -e "${GREEN}✅ Services restarted${NC}"
        show_status
        ;;
    
    "status")
        show_status
        ;;
    
    "logs")
        ${COMPOSE_CMD} logs -f
        ;;
    
    "clean")
        cleanup
        echo -e "${GREEN}✅ Cleanup complete${NC}"
        ;;
    
    "build")
        echo -e "${BLUE}Building and starting services...${NC}"
        ${COMPOSE_CMD} up --build -d
        show_status
        ;;
    
    "test")
        echo -e "${BLUE}Testing API endpoints...${NC}"
        sleep 5  # Wait for services to be ready
        
        echo "Testing API health..."
        curl -f http://localhost:8080/health || echo "API health check failed"
        
        echo "Testing Model Service health..."
        curl -f http://localhost:8081/health || echo "Model service health check failed"
        
        echo "Testing sentiment prediction..."
        curl -X POST http://localhost:8080/predict \
            -H "Content-Type: application/json" \
            -d '{"text": "UCLA is amazing!"}' || echo "Prediction test failed"
        ;;
    
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  up|start  - Start all services (default)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show container status"
        echo "  logs      - Follow logs"
        echo "  clean     - Stop and remove containers/volumes"
        echo "  build     - Build and start services"
        echo "  test      - Test API endpoints"
        echo "  help      - Show this help"
        ;;
    
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
