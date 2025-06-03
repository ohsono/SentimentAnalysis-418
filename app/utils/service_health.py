#!/usr/bin/env python3

"""
Helper module to check service health
"""

import aiohttp
import logging
import os
import time
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Service URLs
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model-service-api:8081")
WORKER_API_URL = os.getenv("WORKER_API_URL", "http://worker-scraper-api:8082")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://dashboard-service:8501")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "sentiment_redis")

# Global HTTP client session
http_session = None

async def get_http_session():
    """Get or create HTTP client session"""
    global http_session
    if http_session is None:
        http_session = aiohttp.ClientSession()
    return http_session

async def close_http_session():
    """Close HTTP client session"""
    global http_session
    if http_session is not None:
        await http_session.close()
        http_session = None

async def check_service_health(service_url: str, endpoint: str = "/health", timeout: int = 2) -> Dict[str, Any]:
    """Check if a service is healthy"""
    try:
        url = f"{service_url}{endpoint}"
        logger.debug(f"Checking health of {url}")
        
        session = await get_http_session()
        
        start_time = time.time()
        async with session.get(url, timeout=timeout) as response:
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response.status == 200:
                try:
                    data = await response.json()
                    return {
                        "status": "operational",
                        "response_code": response.status,
                        "response_time_ms": round(response_time, 2),
                        "data": data
                    }
                except:
                    return {
                        "status": "degraded",
                        "response_code": response.status,
                        "response_time_ms": round(response_time, 2),
                        "error": "Invalid JSON response"
                    }
            else:
                return {
                    "status": "error",
                    "response_code": response.status,
                    "response_time_ms": round(response_time, 2),
                    "error": f"Unexpected status code: {response.status}"
                }
    except aiohttp.ClientConnectorError as e:
        return {
            "status": "unavailable",
            "error": f"Connection error: {str(e)}"
        }
    except aiohttp.ServerTimeoutError:
        return {
            "status": "timeout",
            "error": "Request timed out"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}"
        }

async def check_redis_health() -> Dict[str, Any]:
    """Check if Redis is healthy"""
    try:
        import redis
        
        start_time = time.time()
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            socket_timeout=2
        )
        
        ping_result = redis_client.ping()
        response_time = (time.time() - start_time) * 1000  # ms
        
        return {
            "status": "operational" if ping_result else "error",
            "response_time_ms": round(response_time, 2)
        }
    except redis.ConnectionError as e:
        return {
            "status": "unavailable",
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}"
        }

async def check_all_services() -> Dict[str, Dict[str, Any]]:
    """Check health of all services"""
    # Check Model Service
    model_service_health = await check_service_health(MODEL_SERVICE_URL)
    
    # Check Worker API
    worker_api_health = await check_service_health(WORKER_API_URL)
    
    # Check Dashboard
    dashboard_health = await check_service_health(DASHBOARD_URL, "/", 2)
    
    # Check Redis
    redis_health = await check_redis_health()
    
    return {
        "model_service": model_service_health,
        "worker_api": worker_api_health,
        "dashboard": dashboard_health,
        "redis": redis_health
    }
