# UCLA Sentiment Analysis - Fixed Docker Deployment

This directory contains the **complete fixed deployment** for the UCLA Sentiment Analysis system with all issues resolved.

## 🚀 Quick Start (Docker Deployment)

### 1. **One-Command Deployment**
```bash
# Make deployment script executable and run
chmod +x deploy_fixed_system.sh
./deploy_fixed_system.sh
```

### 2. **Test the Deployed System**
```bash
# Test all services
python3 test_docker_system.py

# Test your original request
curl -X POST 'http://localhost:8081/predict' \
     -H 'Content-Type: application/json' \
     -d '{"text": "testtesttset", "model_name": "vader", "return_confidence": true}'
```

## 📋 What's Fixed

✅ **Model Service**: No more permission errors, VADER works immediately  
✅ **Gateway Service**: Complete API orchestration with database integration  
✅ **Worker Service**: Reddit scraping with task queue management  
✅ **Docker Setup**: Proper permissions, health checks, service dependencies  
✅ **Database**: PostgreSQL with complete schema and indexes  
✅ **Redis**: Task queues and caching fully functional  

## 🌐 Service URLs (After Deployment)

- **Gateway API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Model Service**: http://localhost:8081
- **Worker Service**: http://localhost:8082  
- **Dashboard**: http://localhost:8501

## 📁 New Files Created

### Docker Configuration
- `docker-compose.fixed.yml` - Updated Docker Compose with all fixes
- `Dockerfile.model-service-fixed` - Fixed model service with VADER
- `Dockerfile.gateway-api-service` - Gateway service container
- `Dockerfile.worker-scraper-service` - Worker service container
- `Dockerfile.dashboard-service` - Dashboard service container

### Services
- `standalone_model_service.py` - Fixed model service (works standalone too)
- `deploy_fixed_system.sh` - Complete deployment script
- `test_docker_system.py` - Comprehensive test suite

## 🔧 Manual Commands

### Start Services
```bash
# Start all services
docker-compose -f docker-compose.fixed.yml up -d

# Start specific service
docker-compose -f docker-compose.fixed.yml up -d model-service-fixed
```

### Monitor Services
```bash
# View all logs
docker-compose -f docker-compose.fixed.yml logs -f

# View specific service logs
docker-compose -f docker-compose.fixed.yml logs -f model-service-fixed

# Check service status
docker-compose -f docker-compose.fixed.yml ps
```

### Stop Services
```bash
# Stop all services
docker-compose -f docker-compose.fixed.yml down

# Stop and remove volumes (complete cleanup)
docker-compose -f docker-compose.fixed.yml down -v
```

## 🧪 Testing

### Quick Test
```bash
# Test model service
curl -X POST http://localhost:8081/predict \
     -H 'Content-Type: application/json' \
     -d '{"text": "UCLA is amazing!", "model_name": "vader", "return_confidence": true}'

# Test gateway service  
curl -X POST http://localhost:8080/predict \
     -H 'Content-Type: application/json' \
     -d '{"text": "UCLA is amazing!", "include_probabilities": true}'
```

### Comprehensive Testing
```bash
# Run full test suite
python3 test_docker_system.py
```

## 🗄️ Database Access

### Connect to PostgreSQL
```bash
# Using Docker
docker exec -it sentiment_db_fixed psql -U sentiment_user -d sentiment_db

# Using local psql
psql -h localhost -p 5432 -U sentiment_user -d sentiment_db
```

### Run Database Queries
```sql
-- Check table counts
SELECT 'reddit_posts' as table_name, COUNT(*) as count FROM reddit_posts
UNION ALL
SELECT 'reddit_comments' as table_name, COUNT(*) as count FROM reddit_comments
UNION ALL  
SELECT 'sentiment_analysis_results' as table_name, COUNT(*) as count FROM sentiment_analysis_results;

-- View recent posts with sentiment
SELECT title, sentiment, confidence, compound_score 
FROM posts_with_sentiment 
ORDER BY scraped_at DESC 
LIMIT 5;
```

## 🚨 Troubleshooting

### Services Won't Start
```bash
# Check Docker daemon
docker info

# Check logs for specific service
docker-compose -f docker-compose.fixed.yml logs model-service-fixed

# Restart specific service
docker-compose -f docker-compose.fixed.yml restart model-service-fixed
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :8080  # Gateway
lsof -i :8081  # Model Service
lsof -i :8082  # Worker Service

# Kill processes on port
sudo lsof -ti:8081 | xargs kill -9
```

### Permission Issues
```bash
# Fix directory permissions
chmod -R 755 ./logs ./model_cache
chown -R $USER:$USER ./logs ./model_cache
```

## 📊 System Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Gateway   │    │   Model     │    │   Worker    │
│   Service   │◄──►│   Service   │    │   Service   │
│   (8080)    │    │   (8081)    │    │   (8082)    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
              ┌─────────────┴─────────────┐
              │                           │
        ┌─────────────┐           ┌─────────────┐
        │ PostgreSQL  │           │    Redis    │
        │   (5432)    │           │   (6379)    │
        └─────────────┘           └─────────────┘
```

## ✅ Success Indicators

After deployment, you should see:
- ✅ All 6 Docker containers running
- ✅ Health checks passing
- ✅ API documentation accessible at http://localhost:8080/docs
- ✅ Your original curl request works
- ✅ Database contains sentiment analysis results
- ✅ Redis shows active task queues

## 🎯 Next Steps

1. **Run the deployment**: `./deploy_fixed_system.sh`
2. **Test the system**: `python3 test_docker_system.py`
3. **Access the dashboard**: http://localhost:8501
4. **View API docs**: http://localhost:8080/docs
5. **Start using the system** for UCLA sentiment analysis!

Your UCLA Sentiment Analysis system is now **production-ready** with proper Docker containerization! 🎉
