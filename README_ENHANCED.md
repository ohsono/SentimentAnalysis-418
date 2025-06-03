# UCLA Sentiment Analysis API - Enhanced with Failsafe Features

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/your-repo/ucla-sentiment)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://docker.com)

🛡️ **Production-ready sentiment analysis API with robust failsafe mechanisms, PostgreSQL integration, and swappable ML models.**

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM (recommended)
- 5GB+ disk space for models and data

### One-Command Deployment
```bash
# Clone and deploy with all enhanced features
git clone <repository-url>
cd SentimentAnalysis-418
chmod +x deploy_enhanced.sh
./deploy_enhanced.sh deploy
```

### Manual Deployment
```bash
# 1. Cleanup cache and prepare environment
python cleanup_cache.py

# 2. Start with Docker Compose
docker-compose -f docker-compose-enhanced.yml up -d

# 3. Verify deployment
curl http://localhost:8080/health
```

## 🌟 Enhanced Features

### 🛡️ Failsafe Architecture
- **Circuit Breaker Pattern**: Automatic LLM service failure detection
- **VADER Fallback**: Instant fallback to VADER when LLM fails 3+ times
- **Graceful Degradation**: Service remains operational during failures
- **Self-Healing**: Automatic recovery when services restore

### 🗄️ PostgreSQL Integration
- **Async Data Loading**: Non-blocking database operations
- **Comprehensive Schemas**: Optimized tables for sentiment data, alerts, analytics
- **Automatic Cleanup**: Background tasks for data management
- **Performance Optimization**: Indexed queries and materialized views

### 🔄 Swappable Model Architecture
- **Hot-Swappable Models**: Change ML models without downtime
- **Isolated Model Service**: Dedicated microservice for ML inference
- **Model Caching**: Efficient model loading and memory management
- **Easy Upgrades**: Replace models as new versions become available

### 📊 Advanced Analytics
- **Real-time Dashboards**: Live sentiment analytics and trends
- **Alert Management**: Automated mental health and stress detection
- **Performance Metrics**: Service health and response time monitoring
- **Background Processing**: Async analytics computation

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main API      │    │  Model Service  │    │   PostgreSQL    │
│  (Failsafe)     │◄──►│  (Swappable)    │    │   Database      │
│                 │    │                 │    │                 │
│ • Circuit       │    │ • Hot-swap      │    │ • Async ops     │
│   Breaker       │    │ • Caching       │    │ • Optimized     │
│ • VADER         │    │ • Isolation     │    │ • Auto-cleanup  │
│   Fallback      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                ┌─────────────────▼─────────────────┐
                │         Background Worker          │
                │                                   │
                │ • Analytics computation           │
                │ • Database maintenance            │
                │ • System monitoring               │
                │ • Alert processing                │
                └───────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_DB=ucla_sentiment
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sentiment_password_2024

# Failsafe Configuration
FAILSAFE_MAX_LLM_FAILURES=3
FAILSAFE_FAILURE_WINDOW_SECONDS=300
FAILSAFE_CIRCUIT_BREAKER_TIMEOUT=60
FALLBACK_TO_VADER=true

# Model Service
MODEL_SERVICE_URL=http://model-service:8081
PRELOAD_MODEL=distilbert-sentiment
```

### Model Configuration
The system supports multiple swappable models:

- **distilbert-sentiment**: Fast, efficient (default)
- **twitter-roberta**: Optimized for social media
- **bert-sentiment**: Multilingual support

Change models without downtime:
```bash
curl -X POST http://localhost:8081/models/download \
  -H "Content-Type: application/json" \
  -d '{"model": "twitter-roberta"}'
```

## 📡 API Endpoints

### Core Sentiment Analysis
```bash
# Single prediction with failsafe
POST /predict
{
  "text": "UCLA is amazing!",
  "include_probabilities": true
}

# Batch processing
POST /predict/batch
["Text 1", "Text 2", "Text 3"]
```

### Failsafe Monitoring
```bash
# Get failsafe system status
GET /failsafe/status

# System health with failsafe info
GET /health

# Detailed system metrics
GET /status
```

### Analytics & Alerts
```bash
# Real-time analytics dashboard
GET /analytics

# Active alerts management
GET /alerts

# Update alert status
POST /alerts/{alert_id}/status
{
  "status": "resolved",
  "notes": "Contacted student support"
}
```

### Model Management
```bash
# List available models
GET http://localhost:8081/models

# Download/cache new model
POST http://localhost:8081/models/download
{"model": "twitter-roberta"}

# Model service health
GET http://localhost:8081/health
```

## 🔍 Monitoring & Observability

### Service URLs
- **Main API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Model Service**: http://localhost:8081
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Health Checks
```bash
# Check all services
./deploy_enhanced.sh status

# Monitor logs
./deploy_enhanced.sh logs api
./deploy_enhanced.sh logs model-service

# View failsafe metrics
curl http://localhost:8080/failsafe/status | jq
```

### Key Metrics
- **Circuit Breaker Status**: Open/Closed/Half-Open
- **Success Rate**: LLM service reliability
- **Fallback Usage**: Percentage using VADER
- **Response Times**: API performance
- **Alert Volume**: Mental health monitoring

## 🧪 Testing

### Run Test Suite
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run comprehensive tests
python test_enhanced_api.py

# Run specific test categories
pytest test_enhanced_api.py::TestFailsafeLLMClient -v
pytest test_enhanced_api.py::TestIntegrationScenarios -v
```

### Test Failsafe Features
```bash
# Test circuit breaker by stopping model service
docker-compose -f docker-compose-enhanced.yml stop model-service

# Make predictions (should use VADER fallback)
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Test failsafe mechanism"}'

# Check failsafe status
curl http://localhost:8080/failsafe/status

# Restart model service to test recovery
docker-compose -f docker-compose-enhanced.yml start model-service
```

## 📈 Performance Benchmarks

### Typical Performance
- **VADER Fallback**: 10-50ms per request
- **LLM Service**: 50-200ms per request  
- **Batch Processing**: 1000+ texts/minute
- **Database Operations**: <10ms for queries
- **Failover Time**: <1 second

### Scalability
- **Horizontal Scaling**: Add more model service replicas
- **Vertical Scaling**: Increase memory for larger models
- **Database Scaling**: PostgreSQL read replicas
- **Caching**: Redis for analytics and model caching

## 🔧 Management Commands

### Deployment Management
```bash
# Full deployment
./deploy_enhanced.sh deploy

# Start/stop services
./deploy_enhanced.sh start
./deploy_enhanced.sh stop
./deploy_enhanced.sh restart

# Build only
./deploy_enhanced.sh build

# View system status
./deploy_enhanced.sh status

# Cleanup cache
./deploy_enhanced.sh cleanup
```

### Docker Compose Commands
```bash
# Start with specific profiles
docker-compose -f docker-compose-enhanced.yml --profile dashboard up -d
docker-compose -f docker-compose-enhanced.yml --profile monitoring up -d

# Scale model service
docker-compose -f docker-compose-enhanced.yml up -d --scale model-service=3

# View logs
docker-compose -f docker-compose-enhanced.yml logs -f api
docker-compose -f docker-compose-enhanced.yml logs -f model-service

# Complete cleanup
docker-compose -f docker-compose-enhanced.yml down -v
```

## 🛠️ Development

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements_enhanced.txt

# Setup PostgreSQL locally
createdb ucla_sentiment
psql ucla_sentiment < init_scripts/01_initialize_database.sql

# Run API locally
export POSTGRES_HOST=localhost
export MODEL_SERVICE_URL=http://localhost:8081
python -m uvicorn app.api.main_enhanced:app --reload

# Run model service locally
python model_services/lightweight_model_service.py
```

### Adding New Models
1. **Add to Model Registry** (in `lightweight_model_manager.py`):
```python
"new-model": {
    "name": "New Model",
    "model_name": "huggingface/model-name",
    "description": "Model description",
    "size": "medium",
    "speed": "fast",
    "accuracy": "excellent"
}
```

2. **Test Model Loading**:
```bash
curl -X POST http://localhost:8081/models/download \
  -d '{"model": "new-model"}'
```

3. **Update Documentation** and deployment configs

### Custom Failsafe Logic
Modify failsafe behavior in `failsafe_llm_client.py`:
```python
# Adjust failure thresholds
self.max_failures = 5  # Allow more failures
self.failure_window = 600  # Longer window

# Custom circuit breaker logic
def _should_attempt_llm(self) -> bool:
    # Your custom logic here
    return True
```

## 🚨 Troubleshooting

### Common Issues

#### Model Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose-enhanced.yml logs model-service

# Common causes:
# - Insufficient memory (need 2GB+)
# - Network issues downloading models
# - Permission issues in container

# Solutions:
docker-compose -f docker-compose-enhanced.yml restart model-service
# Or increase memory limits in docker-compose-enhanced.yml
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose -f docker-compose-enhanced.yml ps postgres

# Test connection
docker-compose -f docker-compose-enhanced.yml exec postgres \
  psql -U postgres -d ucla_sentiment -c "SELECT 1;"

# Reset database
docker-compose -f docker-compose-enhanced.yml down -v
docker-compose -f docker-compose-enhanced.yml up -d postgres
```

#### Circuit Breaker Stuck Open
```bash
# Check failsafe status
curl http://localhost:8080/failsafe/status

# Manual reset (if needed - implement reset endpoint)
# Or restart API service
docker-compose -f docker-compose-enhanced.yml restart api
```

#### Performance Issues
```bash
# Check system resources
docker stats

# Monitor API performance
curl http://localhost:8080/status

# Check model service metrics
curl http://localhost:8081/metrics

# Optimize:
# - Scale model service replicas
# - Use smaller/faster models
# - Increase container memory limits
```

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Run with development settings
export ENV=development

# Trace database queries
export DB_ECHO=true
```

## 📞 Support & Contributing

### Getting Help
- **Documentation**: Check `/docs` endpoint for interactive API docs
- **Health Checks**: Use `/health` and `/status` endpoints
- **Logs**: Use `./deploy_enhanced.sh logs [service]`

### Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python test_enhanced_api.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

### Security
- Report security issues privately
- Use environment variables for sensitive config
- Regular dependency updates via `pip-audit`
- Container scanning for vulnerabilities

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **UCLA MASDS Program**: Course framework and requirements
- **Hugging Face**: Pre-trained models and transformers library  
- **VADER Sentiment**: Reliable fallback sentiment analysis
- **FastAPI**: Modern async web framework
- **PostgreSQL**: Robust database platform
- **Docker**: Containerization and deployment

---

**Enhanced UCLA Sentiment Analysis API v2.0.0** - Production-ready with failsafe mechanisms, PostgreSQL integration, and swappable ML models for reliable sentiment analysis at scale.
