#!/bin/bash

# UCLA Sentiment Analysis - Service Management Script
# This script helps build, start, stop, and check status of all microservices

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  STAT-418: UCLA Sentiment Analysis Service Manager${NC}"
echo -e "${BLUE}================================================${NC}"

# Function to display usage information
show_usage() {
    echo -e "\nUsage: $0 [command]"
    echo -e "\nAvailable commands:"
    echo -e "  ${GREEN}build-all${NC}    - Build all Docker images"
    echo -e "  ${GREEN}start${NC}        - Start all services"
    echo -e "  ${GREEN}stop${NC}         - Stop all services"
    echo -e "  ${GREEN}restart${NC}      - Restart all services"
    echo -e "  ${GREEN}status${NC}       - Check status of all services"
    echo -e "  ${GREEN}push-all${NC}     - push all services to the github repo"
    echo -e "  ${GREEN}logs [service]${NC} - View logs for a specific service"
    echo -e "  ${GREEN}test${NC}         - Run tests against running services"
    echo -e "  ${GREEN}clean${NC}        - Remove all containers and images"
    echo -e "  ${GREEN}help${NC}         - Display this help message"
    echo
    echo -e "Available services for logs command:"
    echo -e "  ${YELLOW}gateway-api-service${NC}, ${YELLOW}model-service${NC}, ${YELLOW}worker-scraper-service${NC}, ${YELLOW}dashboard-service${NC}, ${YELLOW}postgres${NC}, ${YELLOW}redis${NC}"
    echo
}


cleanup() {
    # Clean up the foler with ._* and temp files
    echo -e "Cleanup started!"
    find . -name '._*' -delete
    echo -e "Cleanup ended!"
}

# Function to build all Docker images
build_all_services() {
    echo -e "${BLUE}Building all services...${NC}"
    cleanup
    echo -e "${YELLOW}Building gateway-api-service...${NC}"
    docker build -t ohsonoresearch/gateway-api-service -f Dockerfile.gateway-api-service .
    docker tag gateway-api-service ohsonoresearch/gateway-api-service:latest

    # act workflow_dispatch \
    #     --secret-file .secrets \
    #     -P ubuntu-latest=catthehacker/ubuntu:act-latest \
    #     --input dockerfile=Dockerfile.gateway-api-service \
    #     --input image_name=gateway-api-service 

    
    echo -e "${YELLOW}Building model-service...${NC}"
    cleanup
    docker build -t ohsonoresearch/model-service -f Dockerfile.model-service .
    docker tag model-service ohsonoresearch/model-service:latest

    # act workflow_dispatch \
    #     --secret-file .secrets \
    #     -P ubuntu-latest=catthehacker/ubuntu:act-latest \
    #     --input dockerfile=Dockerfile.model-service \
    #     --input image_name=model-service

    echo -e "${YELLOW}Building model-service-distilbert...${NC}"
    cleanup
    docker build -t ohsonoresearch/model-service-distilbert -f Dockerfile.model-service-distilbert .
    docker tag dashboard-service ohsonoresearch/model-service-distilbert:latest
    # act workflow_dispatch \
    #     --secret-file .secrets \
    #     -P ubuntu-latest=catthehacker/ubuntu:act-latest \
    #     --input dockerfile=Dockerfile.model-service \
    #     --input image_name=model-service



    echo -e "${YELLOW}Building worker-scraper-service...${NC}"
    cleanup
    docker build -t ohsonoresearch/worker-scraper-service -f Dockerfile.worker-scraper-service .
    docker tag worker-scraper-service ohsonoresearch/worker-scraper-service:latest

    # act workflow_dispatch \
    #     --secret-file .secrets \
    #     -P ubuntu-latest=catthehacker/ubuntu:act-latest \
    #     --input dockerfile=Dockerfile.worker-scraper-service \
    #     --input image_name=worker-scraper-service

    echo -e "${YELLOW}Building dashboard-service...${NC}"
    cleanup
    docker build -t ohsonoresearch/dashboard-service -f Dockerfile.dashboard-service .
    docker tag dashboard-service ohsonoresearch/dashboard-service:latest

    # act workflow_dispatch \
    #     --secret-file .secrets \
    #     -P ubuntu-latest=catthehacker/ubuntu:act-latest \
    #     --input dockerfile=Dockerfile.dashboard-service \
    #     --input image_name=dashboard-service
    
    echo -e "${GREEN}All services built successfully!${NC}"
}

# Function to build all Docker images
build_test_services() {
    echo -e "${BLUE}Testing all docker build for services...${NC}"
    cleanup
    echo -e "${YELLOW}Test Building gateway-api-service...${NC}"
    #docker build -t ohsonoresearch/gateway-api-service -f Dockerfile.gateway-api .
    act workflow_dispatch \
        --secret-file .secrets \
        -P ubuntu-latest=catthehacker/ubuntu:act-latest \
        --input dockerfile=Dockerfile.gateway-api-service \
        --input image_name=gateway-api-service \
        --input test_mode=build-test

    #docker tag gateway-api-service ohsonoresearch/gateway-api-service:latest
    
    echo -e "${YELLOW}Test Building model-service...${NC}"
    cleanup
    #docker build -t ohsonoresearch/model-service -f Dockerfile.model-service .
    
    act workflow_dispatch \
        --secret-file .secrets \
        -P ubuntu-latest=catthehacker/ubuntu:act-latest \
        --input dockerfile=Dockerfile.model-service \
        --input image_name=model-service \
        --input test_mode=build-test

    #docker tag model-service ohsonoresearch/model-service:latest

    echo -e "${YELLOW}Test Building model-service-bert...${NC}"
    cleanup
    #docker build -t ohsonoresearch/model-service -f Dockerfile.model-service .
    
    act workflow_dispatch \
        --secret-file .secrets \
        -P ubuntu-latest=catthehacker/ubuntu:act-latest \
        --input dockerfile=Dockerfile.model-service-distrilbert \
        --input image_name=model-service-distilbert \
        --input test_mode=build-test

    #docker tag model-service ohsonoresearch/model-service:latest



    echo -e "${YELLOW}Test Building worker-scraper-service...${NC}"
    cleanup
    #docker build -t ohsonoresearch/worker-scraper-service -f Dockerfile.worker-scraper-service .

    act workflow_dispatch \
        --secret-file .secrets \
        -P ubuntu-latest=catthehacker/ubuntu:act-latest \
        --input dockerfile=Dockerfile.worker-scraper-service \
        --input image_name=worker-scraper-service \
        --input test_mode=build-test


    #docker tag worker-scraper-service ohsonoresearch/worker-scraper-service:latest

    echo -e "${YELLOW}Test Building dashboard-service...${NC}"
    cleanup
    #docker build -t ohsonoresearch/dashboard-service -f Dockerfile.dashboard-service .
    act workflow_dispatch \
        --secret-file .secrets \
        -P ubuntu-latest=catthehacker/ubuntu:act-latest \
        --input dockerfile=Dockerfile.dashboard-service \
        --input image_name=dashboard-service \
        --input test_mode=build-test

    
    #docker tag dashboard-service ohsonoresearch/dashboard-service:latest
    
    echo -e "${GREEN}All services test built successfully!${NC}"
}

# Function to start all services
start_services() {
    echo -e "${BLUE}Starting all services...${NC}"
    cleanup
    docker-compose up -d
    
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 5
    
    check_services_status
}

# Function to stop all services
stop_services() {
    echo -e "${BLUE}Stopping all services...${NC}"
    cleanup
    docker-compose down -v
    echo -e "${GREEN}All services stopped.${NC}"
}

# Function to restart all services
restart_services() {
    echo -e "${BLUE}Restarting all services...${NC}"
    cleanup
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

push_all_services() {
    echo -e "${BLUE}push to github for all services...${NC}"
    cleanup
    docker push ohsonoresearch/dashboard-service:latest
    cleanup
    docker push ohsonoresearch/gateway-api-service:latest
    cleanup
    docker push ohsonoresearch/worker-scraper-service:latest
    cleanup
    docker push ohsonoresearch/model-service:latest
    cleanup
    docker push ohsonoresearch/model-service-distilbert:latest
    cleanup

    echo -e "${YELLOW}push for all services ...${NC}"
    sleep 5
}


# Function to view logs for a specific service
view_service_logs() {
    service="$1"
    
    case "$service" in
        "gateway-api-service")
            container="gateway_api_service"
            ;;
        "model-service")
            container="model_service"
            ;;
        "model-service-distilbert")
            container="model_service_distilbert"
            ;;
        "worker-scraper-service")
            container="worker_scraper_service"
            ;;
        "dashboard-service")
            container="dashboard_service"
            ;;
        "postgres")
            container="sentiment_db"
            ;;
        "redis")
            container="sentiment_redis"
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
    docker rm -f gateway_api_service model_service worker_scraper_service dashboard_sevice sentiment_db sentiment_redis 2>/dev/null
    
    echo -e "${YELLOW}Removing all service images...${NC}"
    docker rmi gateway-api-service model-service-api-service worker-scraper-servoce dashboard-service 2>/dev/null || true
    
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
    "build-all")
        build_all_services
        ;;
    "build-test")
        build_test_services # test docker build locally
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
    "push-all")
        push_all_services
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
