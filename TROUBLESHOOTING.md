# Troubleshooting Docker Services

This guide provides solutions to common issues encountered with the Docker containers in this project.

## General Troubleshooting Steps

1. **Check container logs**:
   ```bash
   docker logs ucla_gateway_api
   docker logs ucla_model_service
   docker logs ucla_worker_service
   docker logs ucla_dashboard
   ```

2. **Check container status**:
   ```bash
   docker ps -a
   ```

3. **Restart individual services**:
   ```bash
   docker-compose restart gateway-api
   docker-compose restart model-service-api
   docker-compose restart worker-scraper-api
   docker-compose restart dashboard-service
   ```

4. **Rebuild specific service**:
   ```bash
   docker-compose build gateway-api
   docker-compose up -d gateway-api
   ```

## Common Issues and Solutions

### Permission Denied Errors

**Issue**: Permission denied errors when containers try to write to directories or files.

**Solution**:
1. Make sure volumes are properly defined in docker-compose.yml
2. Ensure the container user has write permissions to mounted volumes
3. Fix with:
   ```bash
   docker-compose down
   docker volume rm streamlit_data worker_data model_cache
   docker-compose up -d
   ```

### Missing Imports or Module Not Found

**Issue**: Python errors about missing imports or modules not found.

**Solution**:
1. Check the requirements files for missing dependencies
2. Ensure the correct Python module is being referenced in the CMD line
3. Fix with:
   ```bash
   docker-compose build --no-cache service-name
   docker-compose up -d service-name
   ```

### Connection Refused Between Services

**Issue**: Services cannot connect to each other (e.g., gateway cannot reach model service).

**Solution**:
1. Ensure all services are on the same Docker network
2. Use service names as hostnames, not localhost
3. Check health checks are passing
4. Fix with:
   ```bash
   docker network inspect sentiment_network
   docker-compose restart
   ```

### Dashboard Service Issues

**Issue**: Streamlit dashboard fails to start with permission errors.

**Solution**:
1. Set the STREAMLIT_HOME_PATH environment variable to a writable location
2. Ensure the streamlit_data volume is properly mounted
3. Fix with:
   ```bash
   docker-compose down
   docker volume rm streamlit_data
   docker-compose up -d dashboard-service
   ```

### Database Connection Issues

**Issue**: Services cannot connect to PostgreSQL database.

**Solution**:
1. Ensure PostgreSQL is running and healthy
2. Check database credentials in environment variables
3. Wait for PostgreSQL to fully initialize
4. Fix with:
   ```bash
   docker-compose restart postgres
   docker-compose restart gateway-api worker-scraper-api
   ```

## Complete Reset

If you encounter persistent issues, perform a complete reset:

```bash
# Stop all services
docker-compose down

# Remove all volumes
docker volume rm postgres_data model_cache gateway_logs model_logs worker_data worker_logs streamlit_data

# Rebuild all services from scratch
docker-compose build --no-cache

# Start all services
docker-compose up -d
```

## Check Resource Usage

If containers are crashing due to resource limitations:

```bash
docker stats
```

You may need to allocate more resources to Docker in your Docker Desktop settings.
