#!/usr/bin/env python3

"""
Quick fix script for running worker service locally
This patches the Redis connection to work with localhost
"""

import os
import sys
from pathlib import Path
import uvicorn

# Add current directory to Python path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

def patch_redis_config():
    """Patch Redis configuration for local development"""
    
    # Set environment variables for local development
    os.environ.setdefault("REDIS_HOST", "localhost")
    os.environ.setdefault("REDIS_PORT", "6379")
    os.environ.setdefault("REDIS_PASSWORD", "sentiment_redis")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5432")
    
    print("🔧 Patched configuration for local development")
    print(f"   Redis Host: {os.environ.get('REDIS_HOST')}")
    print(f"   Database Host: {os.environ.get('DB_HOST')}")

if __name__ == "__main__":
    patch_redis_config()
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8082))
    
    print(f"🚀 Starting Worker Service locally on {host}:{port}")
    print("🔍 Make sure Redis and PostgreSQL containers are running!")
    
    # Use import string for reload to work properly
    uvicorn.run(
        "worker.main:app",  # Import string instead of app object
        host=host,
        port=port,
        reload=True,  # Enable reload for development
        log_level="info",
        access_log=True
    )
