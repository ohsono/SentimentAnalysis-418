# UCLA Sentiment Analysis - Docker Containers

This project uses Docker containers to run each service independently. The services are:

1. **Gateway API**: Entry point for all API requests
2. **Model Service API**: Handles ML model inference
3. **Worker Scraper API**: Handles Reddit data scraping and processing
4. **Dashboard Service**: Provides visualization and monitoring

## Quick Start

```bash
# Make the service manager executable
chmod +x service_manager.sh

# Build all services
./service_manager.sh build

# Start all services
./service_manager.sh start

# Check status
./service_manager.sh status

# Run tests
./service_manager.sh test
```

## Service Architecture

- **Gateway API**: Port 8080
  - Main entry point for all API requests
  - Handles authentication, routing, and basic sentiment analysis
  - Uses PostgreSQL for data storage
  - Communicates with Model Service for advanced sentiment analysis

- **Model Service API**: Port 8081
  - Handles ML model inference
  - Uses lightweight models for sentiment analysis
  - Provides batch prediction capabilities
  - Can be scaled independently

- **Worker Scraper API**: Port 8082
  - Handles Reddit data scraping
  - Processes and cleans scraped data
  - Stores results in PostgreSQL
  - Provides asynchronous task management

- **Dashboard Service**: Port 8501
  - Visualizes sentiment analysis results
  - Provides monitoring of system status
  - Accessible through web browser

## Management Commands

```bash
# View logs for a specific service
./service_manager.sh logs gateway-api
./service_manager.sh logs model-service-api
./service_manager.sh logs worker-scraper-api
./service_manager.sh logs dashboard-service

# Restart all services
./service_manager.sh restart

# Stop all services
./service_manager.sh stop

# Clean up (remove containers and images)
./service_manager.sh clean
```

## Testing

Run the test script to verify all services are working correctly:

```bash
./service_manager.sh test
```

This will test each service individually and their integration.
