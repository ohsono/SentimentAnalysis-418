#!/bin/bash

# Quick Fix Script for Redis Connection Issue
# UCLA Sentiment Analysis - Worker Service

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Redis Connection Fix Script${NC}"
echo -e "${BLUE}============================================${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Checking current service status...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if containers are running
echo -e "${BLUE}📊 Current container status:${NC}"
docker-compose ps

echo -e "\n${YELLOW}🚀 Starting required containers (Redis and PostgreSQL)...${NC}"

# Start only the database containers
docker-compose up -d postgres redis

echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check Redis connection
echo -e "${BLUE}🔍 Testing Redis connection...${NC}"
if docker exec ucla_sentiment_redis redis-cli -a sentiment_redis ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running and accessible${NC}"
else
    echo -e "${RED}❌ Redis connection failed${NC}"
    echo -e "${YELLOW}💡 Try running: docker-compose up -d redis${NC}"
fi

# Check PostgreSQL connection
echo -e "${BLUE}🔍 Testing PostgreSQL connection...${NC}"
if docker exec ucla_sentiment_db pg_isready -U sentiment_user -d sentiment_db > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is running and accessible${NC}"
else
    echo -e "${RED}❌ PostgreSQL connection failed${NC}"
    echo -e "${YELLOW}💡 Try running: docker-compose up -d postgres${NC}"
fi

echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}  Choose how to run the worker service:${NC}"
echo -e "${BLUE}============================================${NC}"

echo -e "\n${GREEN}Option 1: Run everything in Docker (Recommended)${NC}"
echo -e "   ${YELLOW}./service_manager.sh start${NC}"
echo -e "   This will start all services in containers"

echo -e "\n${GREEN}Option 2: Run worker locally for development${NC}"
echo -e "   ${YELLOW}python run_worker_local.py${NC} (with auto-reload)"
echo -e "   ${YELLOW}python run_worker_prod.py${NC} (production mode)"
echo -e "   This will run the worker locally with proper Redis connection"

echo -e "\n${GREEN}Option 3: Manual Docker Compose${NC}"
echo -e "   ${YELLOW}docker-compose up -d${NC}"
echo -e "   This will start all services using docker-compose"

echo -e "\n${BLUE}📝 Note: If running locally, make sure Redis and PostgreSQL containers are running first!${NC}"

# Ask user what they want to do
echo -e "\n${YELLOW}What would you like to do?${NC}"
echo "1) Start all services in Docker (recommended)"
echo "2) Run worker locally (development mode with auto-reload)"
echo "3) Run worker locally (production mode)"
echo "4) Just show service status"
echo "5) Exit"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo -e "${BLUE}🚀 Starting all services in Docker...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✅ All services started. Check status with: docker-compose ps${NC}"
        ;;
    2)
        echo -e "${BLUE}🚀 Starting worker locally (development mode)...${NC}"
        python run_worker_local.py
        ;;
    3)
        echo -e "${BLUE}🚀 Starting worker locally (production mode)...${NC}"
        python run_worker_prod.py
        ;;
    4)
        echo -e "${BLUE}📊 Current service status:${NC}"
        docker-compose ps
        ;;
    5)
        echo -e "${BLUE}👋 Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting...${NC}"
        exit 1
        ;;
esac
