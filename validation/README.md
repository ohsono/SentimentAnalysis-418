# 🧪 Validation Scripts for API-Friendly Pipeline Service

This directory contains comprehensive validation scripts to test and verify all components of the API-friendly Reddit sentiment analysis pipeline service.

## 📋 Available Validation Scripts

### 1. 🚀 **Master Validation** (`master_validation.py`)
**Recommended starting point** - Runs all validations in sequence and provides comprehensive reporting.

```bash
# Run all validations
python validation/master_validation.py

# Quick validation only (no service startup)
python validation/master_validation.py --quick-only

# Skip comprehensive service testing
python validation/master_validation.py --skip-comprehensive
```

**What it tests:**
- Runs all other validation scripts in sequence
- Provides consolidated reporting
- Saves detailed results to JSON file
- Gives specific recommendations for fixes

---

### 2. ⚡ **Quick Validation** (`quick_validation.py`)
Fast validation that checks basic functionality without starting services.

```bash
python validation/quick_validation.py
```

**What it tests:**
- ✅ Critical Python package imports
- ✅ Worker module imports and instantiation
- ✅ Configuration file presence and validity
- ✅ Required file and directory structure
- ✅ Data directory creation
- ✅ Basic component functionality

**Duration:** ~30 seconds

---

### 3. 💾 **Database Validation** (`database_validation.py`)
Comprehensive database connectivity and functionality testing.

```bash
python validation/database_validation.py
```

**What it tests:**
- ✅ Database configuration validation
- ✅ PostgreSQL driver availability
- ✅ Database connection establishment
- ✅ Schema and table validation
- ✅ DatabaseManager class functionality
- ✅ Basic CRUD operations

**Requirements:**
- PostgreSQL server running
- Valid database credentials in `.env.scheduler`

---

### 4. 🕷️ **Reddit Scraper Validation** (`reddit_scraper_validation.py`)
Tests Reddit API connectivity and scraping functionality.

```bash
python validation/reddit_scraper_validation.py
```

**What it tests:**
- ✅ Reddit API credentials validation
- ✅ Reddit API connectivity
- ✅ RedditScraper import and instantiation
- ✅ Small scraping operation (2 posts from r/test)
- ✅ Data file creation and validation
- ✅ Scraped data structure verification

**Requirements:**
- Valid Reddit API credentials
- Internet connectivity
- User confirmation for actual API calls

---

### 5. 🔧 **Comprehensive Validation** (`comprehensive_validation.py`)
Full system validation including service startup and API testing.

```bash
python validation/comprehensive_validation.py
```

**What it tests:**
- ✅ All quick validation checks
- ✅ Service startup and health
- ✅ All API endpoints functionality
- ✅ Pipeline submission and monitoring
- ✅ Real-time status tracking
- ✅ Service cleanup and shutdown

**Duration:** ~5-10 minutes
**Requirements:**
- All dependencies installed
- Database and Redis accessible
- Reddit API credentials configured

---

## 📊 Understanding Validation Results

### Status Indicators
- ✅ **PASS**: Test passed successfully
- ❌ **FAIL**: Test failed (needs attention)
- ⚠️ **WARN**: Test passed with warnings (non-critical)
- ⏭️ **SKIP**: Test skipped (user choice or dependency)

### Exit Codes
- `0`: All validations passed
- `1`: One or more validations failed

## 🚀 Quick Start Validation

**For first-time setup:**
```bash
# 1. Run quick validation to check basics
python validation/quick_validation.py

# 2. If quick validation passes, run master validation
python validation/master_validation.py
```

**For ongoing development:**
```bash
# Quick check during development
python validation/quick_validation.py

# Full validation before deployment
python validation/master_validation.py
```

## 🔧 Common Issues and Solutions

### ❌ Import Errors
```bash
# Install missing dependencies
pip install -r requirements.txt
pip install -r requirements_enhanced.txt
```

### ❌ Configuration Issues
```bash
# Check environment file
cat .env.scheduler

# Verify required variables are set:
# - REDDIT_CLIENT_ID
# - REDDIT_CLIENT_SECRET  
# - POSTGRES_HOST
# - POSTGRES_DB
```

### ❌ Database Connection Failed
```bash
# Check PostgreSQL status
pg_isready -h YOUR_HOST -p YOUR_PORT

# Test connection manually
psql -h YOUR_HOST -p YOUR_PORT -U YOUR_USER -d YOUR_DB
```

### ❌ Reddit API Issues
1. Verify credentials at https://www.reddit.com/prefs/apps
2. Check rate limiting and user agent string
3. Ensure internet connectivity

### ❌ Service Startup Failed
```bash
# Check for port conflicts
lsof -i :8082

# Review service logs
python run_scheduled_worker.py --config test
```

## 📁 Validation Output Files

### `validation_results.json`
Detailed JSON report from master validation containing:
- Test results for each component
- Error messages and stack traces
- Performance metrics
- Configuration summary

### `worker/data/`
Test data files created during validation:
- `*.parquet`: Sample scraped Reddit data
- `*.json`: Task and pipeline state files
- `worker_health.json`: Service health status

## 🎯 Recommended Validation Workflow

### During Development
1. **Quick validation** after code changes
2. **Component-specific validation** when working on features:
   - Database validation when changing DB code
   - Reddit validation when modifying scraper
3. **Master validation** before commits

### Before Deployment
1. **Master validation** on clean environment
2. **Comprehensive validation** with production config
3. **Manual API testing** with `test_pipeline_api.py`

### Production Health Checks
1. **Quick validation** for basic health
2. **Service health endpoint**: `curl http://localhost:8082/health`
3. **Pipeline history check**: `curl http://localhost:8082/pipeline/history`

## 🛠️ Extending Validations

To add new validation tests:

1. **Add to existing script:**
   - Edit appropriate validation script
   - Follow existing test patterns
   - Update result tracking

2. **Create new validation script:**
   - Follow naming pattern: `{component}_validation.py`
   - Use `ValidationResults` class pattern
   - Add to `master_validation.py`

3. **Test patterns:**
   ```python
   def test_component():
       try:
           # Test logic here
           results.add_test("Test Name", "PASS", "Success message")
           return True, result_data
       except Exception as e:
           results.add_test("Test Name", "FAIL", f"Error: {e}")
           return False, str(e)
   ```

## 📞 Getting Help

If validations fail:

1. **Check logs** in `worker/logs/`
2. **Review error messages** in validation output
3. **Follow recommended actions** in validation summary
4. **Check documentation** in project README files
5. **Verify system requirements** and dependencies

## 🎉 Success!

When all validations pass:
- ✅ System is ready for production use
- ✅ All components are properly configured
- ✅ API endpoints are functional
- ✅ Pipeline service is operational

Start the service:
```bash
python run_scheduled_worker.py
```

Test the API:
```bash
python test_pipeline_api.py
```

Your API-friendly pipeline service is ready! 🚀
