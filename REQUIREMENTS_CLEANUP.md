# Requirements Files Cleanup Documentation

## Overview
This document describes the cleanup of redundant and obsolete requirements.txt files in the UCLA Sentiment Analysis project.

## Cleanup Date
$(date)

## Files Cleaned Up

### ✅ KEPT (Active & Essential)
**4 files remaining in root directory:**

1. **`requirements_enhanced.txt`** ⭐ **PRIMARY**
   - **Used by:** Dockerfile.api-enhanced, Dockerfile.worker
   - **Purpose:** Main comprehensive requirements with all features
   - **Includes:** FastAPI, PostgreSQL, Redis, Celery, monitoring, testing tools
   - **Status:** Currently active, most complete

2. **`requirements_model_service_enhanced.txt`** 🤖 **ML ENHANCED**
   - **Used by:** Dockerfile.model-service-enhanced
   - **Purpose:** Enhanced ML model service with full features
   - **Includes:** PyTorch, Transformers, Hugging Face ecosystem
   - **Status:** Currently active for advanced ML features

3. **`requirements_model_service_minimal.txt`** 🤖 **ML MINIMAL**
   - **Used by:** Dockerfile.model-service-minimal
   - **Purpose:** Minimal ML model service for lightweight deployments
   - **Includes:** Essential ML packages only
   - **Status:** Currently active for resource-constrained environments

4. **`requirements-dev.txt`** 🛠️ **DEVELOPMENT**
   - **Used by:** Development workflows
   - **Purpose:** Testing, linting, documentation tools
   - **Includes:** pytest, black, flake8, mypy, pre-commit
   - **Status:** Active for development

### ❌ REMOVED (Moved to backup/old_requirements/)
**7 obsolete files moved:**

1. **`requirements.txt`** - Basic version, superseded by enhanced
2. **`requirements.txt.bak`** - Backup file (exact duplicate)
3. **`requirements_ml.txt`** - Old ML version, superseded by model service enhanced
4. **`requirements_ml.txt.bak`** - Backup file (exact duplicate)
5. **`requirements_minimal.txt`** - Basic minimal, superseded by enhanced versions
6. **`requirements_model_service.txt`** - Superseded by enhanced version
7. **`requirements_docker.txt`** - Not actually referenced in any Dockerfiles

## Current Requirements Architecture

```
📦 Requirements Structure
├── requirements_enhanced.txt                    # 🚀 Main API + Worker
├── requirements_model_service_enhanced.txt      # 🤖 ML Enhanced
├── requirements_model_service_minimal.txt       # 🤖 ML Minimal
├── requirements-dev.txt                         # 🛠️  Development
└── backup/old_requirements/                     # 📦 Old files (safe to delete)
    ├── requirements.txt
    ├── requirements.txt.bak
    ├── requirements_ml.txt
    ├── requirements_ml.txt.bak
    ├── requirements_minimal.txt
    ├── requirements_model_service.txt
    └── requirements_docker.txt
```

## Usage Guide

### For Development
```bash
# Install development tools
pip install -r requirements-dev.txt

# Install main application dependencies
pip install -r requirements_enhanced.txt

# Install ML model service (choose one)
pip install -r requirements_model_service_enhanced.txt      # Full features
pip install -r requirements_model_service_minimal.txt       # Lightweight
```

### For Docker Deployment
```bash
# API and Worker containers use:
COPY requirements_enhanced.txt .
RUN pip install -r requirements_enhanced.txt

# Enhanced Model Service uses:
COPY requirements_model_service_enhanced.txt .
RUN pip install -r requirements_model_service_enhanced.txt

# Minimal Model Service uses:
COPY requirements_model_service_minimal.txt .
RUN pip install -r requirements_model_service_minimal.txt
```

## Benefits of This Cleanup

1. **🧹 Reduced Confusion** - No more wondering which requirements file to use
2. **📦 Clear Purpose** - Each file has a specific, documented purpose
3. **🔄 Easy Maintenance** - Fewer files to keep in sync
4. **⚡ Faster Development** - Clear dependency management
5. **📏 Consistent Deployment** - Dockerfiles use well-defined requirements

## Dependencies Overview

### requirements_enhanced.txt (Main)
- **Core:** FastAPI 0.104+, uvicorn, pydantic 2.4+
- **Database:** PostgreSQL (asyncpg), SQLAlchemy 2.0+
- **Background:** Celery, Redis
- **Monitoring:** Prometheus, psutil
- **Development:** pytest, black, flake8
- **Size:** ~50 packages

### requirements_model_service_enhanced.txt (ML)
- **ML Core:** PyTorch 2.0+, Transformers 4.35+
- **HuggingFace:** hub, datasets, accelerate
- **Performance:** optimum, torch optimizations
- **Size:** ~25 packages (but large due to ML libraries)

### requirements_model_service_minimal.txt (ML Lite)
- **ML Core:** PyTorch 2.0+, Transformers 4.35+
- **Essential only:** Basic tokenizers, numpy
- **Size:** ~15 packages

### requirements-dev.txt (Development)
- **Testing:** pytest, pytest-asyncio, httpx
- **Code Quality:** black, flake8, mypy
- **Documentation:** mkdocs, mkdocs-material
- **Load Testing:** locust
- **Size:** ~15 packages

## Migration Notes

If you were previously using any of the removed files:

- **`requirements.txt`** → Use `requirements_enhanced.txt`
- **`requirements_ml.txt`** → Use `requirements_model_service_enhanced.txt`
- **`requirements_minimal.txt`** → Use `requirements_model_service_minimal.txt`
- **`requirements_docker.txt`** → Use `requirements_enhanced.txt`

## Recovery

If you need to restore any removed file:
```bash
# Copy from backup
cp backup/old_requirements/[filename] ./

# Or restore all
cp backup/old_requirements/* ./
```

## Safe to Delete

The `backup/old_requirements/` directory can be safely deleted after confirming the cleanup works correctly.

---
**Cleanup completed successfully! 🎉**
