# Docker Files Cleanup & Organization Documentation

## Overview
This document describes the cleanup and reorganization of Docker-related files in the UCLA Sentiment Analysis project.

## Cleanup Date
$(date)

## 🐳 Docker Container Cleanup

### Buildkit Containers Removed
Multiple old Docker buildkit containers were accumulating from repeated builds:
- ✅ **Removed 8+ buildkit containers** older than 4 hours
- ✅ **Cleaned build cache** and dangling images
- ✅ **Added cleanup scripts** for future maintenance

### Cleanup Scripts Added
- `scripts/cleanup_docker_containers.sh` - Comprehensive Docker cleanup
- `debug/quick_docker_cleanup.sh` - Quick buildkit container cleanup

## 📂 Docker Files Organization

### ✅ CURRENT STRUCTURE (Clean & Organized)

#### **Main Compose Files** (4 files)
```
docker-compose.yml              # 🚀 PRIMARY - Main production setup
docker-compose-enhanced.yml     # 📈 ENHANCED - With optional services  
docker-compose.dev.yml          # 🛠️  DEVELOPMENT - Minimal dev setup
docker-compose.monitoring.yml   # 📊 MONITORING - Grafana + Prometheus
```

#### **Dockerfiles** (4 files)
```
Dockerfile.api-enhanced         # 🚀 Main API service
Dockerfile.model-service-enhanced  # 🤖 ML service (full features)
Dockerfile.model-service-minimal   # 🤖 ML service (lightweight)
Dockerfile.worker              # ⚙️  Background worker service
```

### ❌ MOVED TO BACKUP (2 obsolete files)

#### **backup/docker_files/**
```
docker-compose-fixed.yml       # Debugging version (used pre-built image)
Dockerfile.api-fixed          # Debugging version (old port 8080)
```

## 🎯 Docker Compose Architecture

### 1. **docker-compose.yml** 🚀 **PRIMARY**
- **Purpose:** Main production deployment
- **Services:** API, Model Service, Worker, PostgreSQL, Redis
- **Port:** 8888 (API), 8081 (Model Service)
- **Usage:** `docker-compose up`

### 2. **docker-compose-enhanced.yml** 📈 **FULL FEATURED**
- **Purpose:** Complete setup with all optional services
- **Services:** All main services + Dashboard, Prometheus, Grafana
- **Profiles:** `dashboard`, `monitoring` (optional)
- **Usage:** `docker-compose -f docker-compose-enhanced.yml up`

### 3. **docker-compose.dev.yml** 🛠️ **DEVELOPMENT**
- **Purpose:** Lightweight development setup
- **Services:** API, Minimal Model Service, PostgreSQL, Redis
- **Features:** Live code reload, development credentials
- **Usage:** `docker-compose -f docker-compose.dev.yml up`

### 4. **docker-compose.monitoring.yml** 📊 **MONITORING ONLY**
- **Purpose:** Add monitoring to existing setup
- **Services:** Prometheus, Grafana, Dashboard
- **Usage:** `docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up`

## 🏗️ Dockerfile Architecture

### **Dockerfile.api-enhanced** 🚀
- **Purpose:** Main API service with all features
- **Requirements:** `requirements_enhanced.txt`
- **Features:** PostgreSQL, Redis, Failsafe LLM, Background tasks
- **Port:** 8888
- **Size:** ~500MB

### **Dockerfile.model-service-enhanced** 🤖
- **Purpose:** Full-featured ML model service
- **Requirements:** `requirements_model_service_enhanced.txt`
- **Features:** PyTorch, Transformers, Hugging Face ecosystem
- **Port:** 8081
- **Size:** ~2GB (includes ML libraries)

### **Dockerfile.model-service-minimal** 🤖
- **Purpose:** Lightweight ML model service
- **Requirements:** `requirements_model_service_minimal.txt`
- **Features:** Essential ML packages only
- **Port:** 8081
- **Size:** ~1GB (optimized)

### **Dockerfile.worker** ⚙️
- **Purpose:** Background task processing
- **Requirements:** `requirements_enhanced.txt`
- **Features:** Celery, Redis, Database integration
- **Size:** ~400MB

## 🚀 Usage Examples

### Quick Start (Production)
```bash
# Main production setup
docker-compose up -d

# Check status
curl http://localhost:8888/health
```

### Development Setup
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# With live reload for API development
docker-compose -f docker-compose.dev.yml up api
```

### Full Featured Setup
```bash
# Start with all optional services
docker-compose -f docker-compose-enhanced.yml up -d

# Or start with monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Monitoring Only
```bash
# Add monitoring to existing setup
docker-compose -f docker-compose.monitoring.yml up -d
```

## 🧹 Maintenance Commands

### Container Cleanup
```bash
# Quick buildkit cleanup
./debug/quick_docker_cleanup.sh

# Comprehensive cleanup
./scripts/cleanup_docker_containers.sh

# Manual cleanup
docker system prune -f
docker builder prune -f
```

### Image Management
```bash
# Build specific service
docker-compose build api
docker-compose build model-service

# Rebuild with no cache
docker-compose build --no-cache

# Remove old images
docker image prune -f
```

## 📊 Service Overview

| Service | Port | Purpose | Dockerfile | Requirements |
|---------|------|---------|------------|--------------|
| API | 8888 | Main REST API | Dockerfile.api-enhanced | requirements_enhanced.txt |
| Model Service | 8081 | ML Inference | Dockerfile.model-service-enhanced | requirements_model_service_enhanced.txt |
| Worker | - | Background Tasks | Dockerfile.worker | requirements_enhanced.txt |
| PostgreSQL | 5432 | Database | postgres:15-alpine | - |
| Redis | 6379 | Cache/Queue | redis:7-alpine | - |
| Prometheus | 9090 | Metrics | prom/prometheus | - |
| Grafana | 3000 | Visualization | grafana/grafana | - |
| Dashboard | 8501 | Streamlit UI | Dockerfile.dashboard | - |

## 🔐 Environment Variables

### Common Variables (All Compose Files)
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ucla_sentiment
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sentiment_password_2024

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=sentiment_redis_2024

API_HOST=0.0.0.0
API_PORT=8888
MODEL_SERVICE_URL=http://model-service:8081
```

### Development Overrides
```bash
POSTGRES_DB=ucla_sentiment_dev
POSTGRES_PASSWORD=dev_password_123
REDIS_PASSWORD=dev_redis_123
ENV=development
```

## 🛠️ Benefits of This Organization

1. **🎯 Clear Purpose** - Each compose file has a specific use case
2. **🚀 Easy Development** - Separate dev environment with live reload
3. **📈 Scalable Production** - Full-featured production setup
4. **📊 Optional Monitoring** - Add monitoring without affecting core services
5. **🧹 Clean Maintenance** - Automated cleanup scripts
6. **🔄 Flexible Deployment** - Mix and match compose files
7. **📋 Consistent Naming** - Clear, descriptive file names

## 🔄 Migration Guide

### Old Commands → New Commands
```bash
# OLD: docker-compose -f docker-compose-enhanced.yml up
# NEW: docker-compose up                              # Main setup
# NEW: docker-compose -f docker-compose-enhanced.yml up  # Full setup

# OLD: docker-compose -f docker-compose-fixed.yml up
# NEW: docker-compose -f docker-compose.dev.yml up   # Development

# OLD: Manual container cleanup
# NEW: ./debug/quick_docker_cleanup.sh               # Automated cleanup
```

## 🎉 Status: COMPLETE

✅ **2 obsolete Docker files moved to backup**  
✅ **4 organized compose files for different scenarios**  
✅ **4 clean Dockerfiles with specific purposes**  
✅ **Automated Docker container cleanup**  
✅ **Comprehensive documentation**  

---

**Your Docker environment is now clean, organized, and production-ready! 🐳**

### Quick Commands:
```bash
# Start main system
docker-compose up -d

# Development mode
docker-compose -f docker-compose.dev.yml up -d

# With monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Cleanup old containers
./debug/quick_docker_cleanup.sh
```
