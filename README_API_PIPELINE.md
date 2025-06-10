# 🔄 API-Friendly Pipeline Worker Service

A comprehensive Reddit data collection and processing pipeline with RESTful API control.

## 🚀 Quick Start

### 1. Start the Service
```bash
# Copy configuration
cp .env.scheduler .env

# Start the enhanced worker service
python3 run_scheduled_worker.py
```

### 2. Run a Complete Pipeline
```bash
# Execute scraping → processing → cleaning → database loading
curl -X POST http://localhost:8082/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "subreddit": "UCLA",
    "post_limit": 50,
    "comment_limit": 25,
    "enable_processing": true,
    "enable_cleaning": true,
    "enable_database": true
  }'
```

### 3. Monitor Progress
```bash
# Replace with your pipeline ID from step 2
curl http://localhost:8082/pipeline/{pipeline_id}/status
```

## 📋 **API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health and status |
| `/pipeline/run` | POST | Execute complete pipeline |
| `/pipeline/{id}/status` | GET | Monitor pipeline progress |
| `/pipeline/{id}/cancel` | DELETE | Cancel running pipeline |
| `/pipeline/history` | GET | Execution history and stats |
| `/pipeline/active` | GET | Currently running pipelines |
| `/pipeline/{id}/logs` | GET | Detailed execution logs |

## 🔧 **Pipeline Steps**

1. **📊 Scraping** - Collect Reddit posts and comments
2. **⚙️ Processing** - Clean and process raw data  
3. **🧹 Cleaning** - Remove duplicates and organize
4. **💾 Database** - Store with sentiment analysis

Each step can be enabled/disabled individually via API.

## 🧪 **Testing**

```bash
# Test the API endpoints
python3 test_pipeline_api.py

# Test the enhanced Reddit scraper
python3 test_reddit_scraper.py

# Test scheduler functionality  
python3 test_scheduler.py
```

## ⚙️ **Configuration**

Edit `.env` file to configure:

```bash
# Scheduler Settings
SCHEDULER_ENABLED=true
SCRAPING_INTERVAL_MINUTES=30
AUTO_PIPELINE_ENABLED=true

# Reddit API (required)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret

# Database (optional but recommended)
POSTGRES_HOST=your_db_host
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
```

## 📊 **Monitoring**

- **Health Status**: `curl http://localhost:8082/health`
- **Active Pipelines**: `curl http://localhost:8082/pipeline/active`  
- **Execution History**: `curl http://localhost:8082/pipeline/history`
- **API Documentation**: Visit `http://localhost:8082/docs`

## 🐳 **Docker Deployment**

```bash
# Build and run with Docker
docker build -t pipeline-worker .
docker run -d -p 8082:8082 --env-file .env pipeline-worker
```

## 💡 **Use Cases**

- **On-demand data collection** for research
- **Automated content monitoring** with scheduling
- **Sentiment analysis pipeline** with database storage
- **Multi-step data processing** with progress tracking

## 📚 **Documentation**

- **Complete API Guide**: See `API-Friendly Pipeline Service - Complete Guide` artifact
- **Configuration Options**: Check `.env.scheduler` and `.env.docker` files
- **Integration Examples**: Python, JavaScript, and cURL examples included

## 🎯 **Key Features**

✅ **RESTful API** for all operations  
✅ **Real-time progress monitoring**  
✅ **Flexible step configuration**  
✅ **Automatic scheduling**  
✅ **Database integration**  
✅ **Comprehensive logging**  
✅ **Container-ready deployment**  

Perfect for automated data collection workflows and research pipelines! 🚀
