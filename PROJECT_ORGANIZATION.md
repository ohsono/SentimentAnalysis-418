# Project File Organization

## Overview
This document tracks the reorganization of UCLA Sentiment Analysis project files for better organization and maintenance.

## Reorganization Summary (Date: $(date))

### Shell Scripts moved to `scripts/` folder:
- ✅ build_fixed_images.sh
- ✅ check_docker_status.sh
- ✅ deploy_enhanced.sh
- ✅ docker_run.sh
- ✅ fix_and_restart.sh
- ✅ fix_docker_build.sh
- ✅ master_setup.sh
- ✅ quick_build_and_start.sh
- ✅ quick_start.sh
- ✅ robust_build.sh
- ✅ run_full_diagnostic.sh
- ✅ verify_implementation.sh

### Python test and utility files moved to `debug/` folder:
- ✅ comprehensive_api_test.py
- ✅ quick_test.py
- ✅ restart_api.py
- ✅ run_api.py
- ✅ set_permissions.py
- ✅ setup_and_test.py
- ✅ setup_docker_complete.py
- ✅ setup_ml_models.py
- ✅ start_api.py
- ✅ test_api.py
- ✅ test_docker_deployment.py
- ✅ test_endpoints.py
- ✅ test_endpoints_enhanced.py
- ✅ test_enhanced_api.py
- ✅ test_fixed_api.py
- ✅ test_ml_endpoints.py

## Current Directory Structure

### Root Directory (Clean)
```
├── .conda/                 # Conda environment
├── .env                    # Environment variables
├── .git/                   # Git repository
├── .github/                # GitHub workflows
├── .gitignore              # Git ignore rules
├── .streamlit/             # Streamlit configuration
├── app/                    # Main application code
├── backup/                 # Backup files (unused main files)
├── config/                 # Configuration files
├── data/                   # Data files
├── debug/                  # Test and debug files (NEW LOCATION)
├── docker-compose*.yml     # Docker compose files
├── Dockerfile.*            # Docker build files
├── init_scripts/           # Database initialization
├── logs/                   # Application logs
├── model_services/         # ML model services
├── monitoring/             # Monitoring configuration
├── pyproject.toml          # Python project configuration
├── requirements*.txt       # Python dependencies
├── scripts/                # Shell scripts (NEW LOCATION)
└── tests/                  # Unit tests
```

### scripts/ folder now contains:
```
scripts/
├── api-entrypoint.sh
├── api-entrypoint-fixed.sh
├── build_fixed_images.sh       # MOVED
├── check_docker_status.sh      # MOVED
├── deploy_enhanced.sh          # MOVED
├── deployment/
├── docker_run.sh               # MOVED
├── fix_and_restart.sh          # MOVED
├── fix_docker_build.sh         # MOVED
├── master_setup.sh             # MOVED
├── model-service-entrypoint.sh
├── quick_build_and_start.sh    # MOVED
├── quick_start.sh              # MOVED
├── robust_build.sh             # MOVED
├── run_full_diagnostic.sh      # MOVED
├── setup/
├── verify_implementation.sh    # MOVED
├── wait-for-it.sh
└── worker-entrypoint.sh
```

### debug/ folder now contains:
```
debug/
├── comprehensive_api_test.py   # MOVED
├── fix_port_8080.sh
├── fix_port_8888.sh
├── fix_postgres_connectivity.sh
├── quick_status.sh
├── quick_test.py               # MOVED
├── restart_api.py              # MOVED
├── run_api.py                  # MOVED
├── set_permissions.py          # MOVED
├── setup_and_test.py           # MOVED
├── setup_docker_complete.py    # MOVED
├── setup_ml_models.py          # MOVED
├── simple_fix.sh
├── start_api.py                # MOVED
├── test_api.py                 # MOVED
├── test_docker_deployment.py   # MOVED
├── test_endpoints.py           # MOVED
├── test_endpoints_enhanced.py  # MOVED
├── test_enhanced_api.py        # MOVED
├── test_fixed_api.py           # MOVED
├── test_ml_endpoints.py        # MOVED
└── test_port_8888.sh
```

## Quick Access Commands

### Run scripts:
```bash
# Setup and deployment
./scripts/quick_start.sh
./scripts/master_setup.sh
./scripts/deploy_enhanced.sh

# Testing and diagnostics
./debug/test_port_8888.sh
./debug/comprehensive_api_test.py
./scripts/check_docker_status.sh

# Development utilities
./scripts/build_fixed_images.sh
./scripts/fix_and_restart.sh
```

### Make scripts executable:
```bash
chmod +x scripts/*.sh
chmod +x debug/*.sh
```

## Benefits of This Organization

1. **Clean root directory** - Only essential configuration files and directories
2. **Logical grouping** - Scripts in scripts/, tests in debug/
3. **Easy maintenance** - Clear separation of concerns
4. **Better navigation** - No more scrolling through dozens of files
5. **Version control friendly** - Cleaner git status and diffs

## Previous vs Current

**Before:** 40+ files scattered in root directory
**After:** Clean root with organized subdirectories

## Notes
- All script functionality remains the same
- Paths in documentation may need updating
- Consider updating any hardcoded script paths in other files
