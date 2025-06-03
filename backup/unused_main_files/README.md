# Backup of Unused Main Files

## Purpose
This directory contains backup copies of unused main.py files that were causing confusion in the API service.

## Files Backed Up

### main.py.backup
- **Issue**: Had import errors (`from pdb import pm`) and incomplete/commented out sample data
- **Status**: Problematic, had broken imports and incomplete code
- **Reason for removal**: Causing confusion and had import errors

### main_docker.py.backup  
- **Issue**: Alternative microservices version not being used by current deployment
- **Status**: Working but not the correct version for current setup
- **Reason for removal**: Current Dockerfile calls `app.api.main_enhanced:app`, not this version

## Current Correct File
- **`main_enhanced.py`** ✅ **ACTIVE** - This is the correct file used by Dockerfile.api-enhanced
  - Comprehensive with failsafe features
  - PostgreSQL integration  
  - Proper database managers and async loading
  - Called by: `python -m uvicorn app.api.main_enhanced:app`

## Cleanup Action Taken
- Backed up unused files to this directory
- Removed original problematic files from app/api/ 
- Left only main_enhanced.py as the single source of truth

## Restoration
If you need to restore any of these files:
```bash
cp backup/unused_main_files/main.py.backup app/api/main.py
cp backup/unused_main_files/main_docker.py.backup app/api/main_docker.py
```

## Date
Backup created: $(date)
