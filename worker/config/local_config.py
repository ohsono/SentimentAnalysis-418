#!/usr/bin/env python3

"""
Local development configuration for worker service
Use this when running the worker service locally (not in Docker)
"""

import os

# Redis configuration for local development
# When running locally, connect to Redis on localhost instead of 'redis' hostname
def get_redis_config():
    """Get Redis configuration based on environment"""
    
    # Check if we're running in Docker (this env var is set in docker-compose)
    if os.getenv("DOCKER_ENV") == "prod":
        # Running in Docker - use container hostnames
        return {
            "host": os.getenv("REDIS_HOST", "redis"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "password": os.getenv("REDIS_PASSWORD", "sentiment_redis")
        }
    else:
        # Running locally - use localhost
        return {
            "host": os.getenv("REDIS_HOST", "localhost"),  # Use localhost instead of redis
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "password": os.getenv("REDIS_PASSWORD", "sentiment_redis")
        }

# Database configuration for local development
def get_db_config():
    """Get database configuration based on environment"""
    
    if os.getenv("DOCKER_ENV") == "prod":
        # Running in Docker - use container hostnames
        return {
            "host": os.getenv("DB_HOST", "postgres"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER", "sentiment_user"),
            "password": os.getenv("DB_PASSWORD", "sentiment_password"),
            "database": os.getenv("DB_NAME", "sentiment_db")
        }
    else:
        # Running locally - use localhost
        return {
            "host": os.getenv("DB_HOST", "localhost"),  # Use localhost instead of postgres
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER", "sentiment_user"),
            "password": os.getenv("DB_PASSWORD", "sentiment_password"),
            "database": os.getenv("DB_NAME", "sentiment_db")
        }
