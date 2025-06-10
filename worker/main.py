#!/usr/bin/env python3

"""
Worker Service for Reddit Scraping and Data Processing
"""

import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from threading import local
from typing import Dict, Any, List, Optional
import asyncio
# Import worker utilities
try:
    # Try relative imports first (when running as module)
    from .utils.task_interface import TaskInterface
    from .worker_orchestrator import WorkerOrchestrator  
    from .pydantic_models import (WorkerScrapeRequest, TaskStatusResponse, 
                                     PipelineRequest, PipelineStatusResponse, 
                                     PipelineHistoryResponse, WorkerHealthResponse)
    from .config.local_config import *
    from .config.worker_config import WorkerConfig
except ImportError:
    # Fall back to absolute imports (when running directly)
    from worker.utils.task_interface import TaskInterface
    from worker.worker_orchestrator import WorkerOrchestrator  
    from worker.pydantic_models import (WorkerScrapeRequest, TaskStatusResponse, 
                                       PipelineRequest, PipelineStatusResponse, 
                                       PipelineHistoryResponse, WorkerHealthResponse)
    from worker.config.local_config import *
    from worker.config.worker_config import WorkerConfig

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
#from pydantic import BaseModel, Field

import uvicorn
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path if needed
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))


# Initialize task interface
task_interface = TaskInterface('data/')

# Configure Redis using local_config
from worker.config.local_config import get_redis_config
redis_config = get_redis_config()
REDIS_HOST = redis_config["host"]
REDIS_PORT = redis_config["port"]
REDIS_PASSWORD = redis_config["password"]

# localconfig['postgres'] = get_db_config()
# localconfig['redis'] = get_redis_config()
# wc = WorkerConfig()
# DB_CONFIG = wc.get_database_config()
# SC_CONFIG = wc.get_scraping_config()
# PR_CONFIG = wc.get_processing_config()
# RC_CONFIG = wc.get_reddit_config()

# Redis client for tasks queue
redis_client = None
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    # Check connection
    redis_client.ping()
    logger.info("✅ Connected to Redis successfully")
except Exception as e:
    logger.error(f"❌ Failed to connect to Redis: {e}")
    redis_client = None
# =======================================================
# REDIS DEPENDENCIES
# =======================================================

async def get_redis():
    """Dependency to get Redis client"""
    if redis_client and redis_client.ping():
        return redis_client
    else:
        logger.warning("⚠️ Redis connection not available")
        return None

# =======================================================
# FASTAPI APP
# =======================================================

app = FastAPI(
    title="UCLA Sentiment Analysis - Enhanced Worker Service",
    description="Enhanced worker service with scheduled Reddit data scraping and processing pipeline",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
asyn_worker = WorkerOrchestrator() 

# =======================================================
# API ENDPOINTS
# =======================================================

@app.get("/")
async def root():
    """Enhanced worker service information"""
    scheduler_config = asyn_worker.scheduler_config if hasattr(asyn_worker, 'scheduler_config') else {}
    
    return {
        "service": "UCLA Sentiment Analysis - Enhanced Worker Service",
        "version": "2.0.0",
        "description": "Enhanced worker service with scheduled scraping and data pipeline",
        "features": {
            "scheduled_scraping": scheduler_config.get('enabled', False),
            "auto_pipeline": scheduler_config.get('auto_pipeline_enabled', False),
            "scraping_interval_minutes": scheduler_config.get('scraping_interval_minutes', 30),
            "database_integration": True,
            "error_retry": scheduler_config.get('retry_failed_tasks', False)
        },
        "endpoints": {
            "health": "GET /health",
            "scrape_info": "GET /scrape",
            "scrape_submit": "POST /scrape",
            "pipeline_run": "POST /pipeline/run",
            "pipeline_status": "GET /pipeline/{id}/status",
            "pipeline_cancel": "DELETE /pipeline/{id}/cancel",
            "pipeline_history": "GET /pipeline/history",
            "pipeline_active": "GET /pipeline/active",
            "tasks": "GET /tasks",
            "task_status": "GET /tasks/{task_id}",
            "api_docs": "GET /docs"
        },
        "status": {
            "redis_connected": redis_client is not None and redis_client.ping() if redis_client else False,
            "scheduler_running": scheduler_config.get('enabled', False),
            "pipeline_active": getattr(asyn_worker, 'pipeline_running', False)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health", response_model=WorkerHealthResponse)
async def health_check():
    """Enhanced health check for worker service"""
    worker_health = task_interface.get_worker_health()
    redis_status = "connected" if redis_client and redis_client.ping() else "disconnected"
    
    # Get enhanced orchestrator information
    scheduler_config = asyn_worker.scheduler_config if hasattr(asyn_worker, 'scheduler_config') else {}
    
    return WorkerHealthResponse(
        status="healthy",
        service="enhanced-worker-service",
        version="2.0.0",
        scheduler_enabled=scheduler_config.get('enabled', False),
        pipeline_running=getattr(asyn_worker, 'pipeline_running', False),
        database_connected=getattr(asyn_worker, 'db_manager', None) is not None,
        redis_connected=redis_status == "connected",
        active_pipelines=len(getattr(asyn_worker, 'active_pipelines', {})),
        queue_size=worker_health.get("active_tasks", 0),
        uptime_seconds=0.0,  # TODO: Implement uptime tracking
        task_stats=getattr(asyn_worker, 'task_stats', {}),
        next_scheduled_scrape=asyn_worker._get_next_scheduled_scrape().isoformat() if scheduler_config.get('enabled', False) and hasattr(asyn_worker, '_get_next_scheduled_scrape') else None,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.get("/scrape/info")
async def scrape_info():
    """
    GET /scrape - Information about how to use the scraping endpoint
    """
    return {
        "message": "Reddit Scraping Endpoint",
        "method": "POST",
        "endpoint": "/scrape/info",
        "description": "Submit a Reddit scraping task",
        "required_fields": {
            "subreddit": "Name of the subreddit to scrape (without r/)",
            "post_limit": "Number of posts to scrape (default: 10)",
            "comment_limit": "Number of comments per post (default: 5)"
        },
        "optional_fields": {
            "sort_by": "Sort method: hot, new, top, rising (default: hot)",
            "time_filter": "Time filter: all, day, week, month, year (default: all)",
            "search_query": "Search query within the subreddit (optional)"
        },
        "example_curl": {
            "basic": "curl -X POST http://localhost:8082/scrape -H 'Content-Type: application/json' -d '{\"subreddit\": \"python\", \"post_limit\": 5}'",
            "advanced": "curl -X POST http://localhost:8082/scrape -H 'Content-Type: application/json' -d '{\"subreddit\": \"MachineLearning\", \"post_limit\": 10, \"comment_limit\": 3, \"sort_by\": \"hot\"}'"
        },
        "example_python": {
            "requests": "import requests\nresponse = requests.post('http://localhost:8082/scrape', json={'subreddit': 'python', 'post_limit': 5})\nprint(response.json())"
        },
        "swagger_docs": "Visit http://localhost:8082/docs for interactive API documentation",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/scrape")
async def scrape_reddit(request: WorkerScrapeRequest):
    """
    Submit Reddit scraping task
    
    This endpoint submits a scraping task and returns immediately.
    Use /tasks/{task_id} to check progress and get results.
    """

    try:
        logger.info(f"Submitting scraping task for r/{request.subreddit}")
        
        # Prepare task data
        task_data = {
            'subreddit': request.subreddit,
            'post_limit': request.post_limit,
            'comment_limit': request.comment_limit,
            'sort_by': request.sort_by,
            'time_filter': request.time_filter,
            'search_query': request.search_query,
            'requested_by': 'worker_api',
            'api_endpoint': '/scrape'
        }
        # Submit task to worker
        task_id = task_interface.submit_task('scrape_reddit', task_data)
        
        # Note: Actual scraping is handled asynchronously by the worker orchestrator
        # The task is queued and will be processed in the background
        # Store task in Redis for tracking
        if redis_client:
            task_info = {
                "task_id": task_id,
                "type": "scrape_reddit",
                "status": "submitted",
                "data": json.dumps(task_data),
                "submitted_at": datetime.now(timezone.utc).isoformat()
            }
            try:
                redis_client.hmset(f"task:{task_id}", task_info)
                redis_client.sadd("active_tasks", task_id)
                redis_client.expire(f"task:{task_id}", 86400)  # 24 hour expiration
                logger.info(f"Task {task_id} stored in Redis")
            except Exception as e:
                logger.error(f"Failed to store task in Redis: {e}")
        
        # Get worker health status
        worker_health = task_interface.get_worker_health()
        
        response = {
            "status": "accepted",
            "message": f"Scraping task submitted for r/{request.subreddit}",
            "task_id": task_id,
            "task_type": "scrape_reddit",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "estimated_completion": "2-5 minutes (depending on data volume)",
            "worker_status": worker_health.get('status', 'unknown'),
            "data": {
                "subreddit": request.subreddit,
                "post_limit": request.post_limit,
                "comment_limit": request.comment_limit,
                "sort_method": request.sort_by
            },
            "endpoints": {
                "check_status": f"/tasks/{task_id}",
                "list_tasks": "/tasks"
            }
        }
        
        logger.info(f"Submitted scraping task {task_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error submitting scraping task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit scraping task: {str(e)}")

@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, redis=Depends(get_redis)):
    """Get the status and results of a task"""
    try:
        # First check Redis for task info
        if redis:
            task_info = redis.hgetall(f"task:{task_id}")
            if task_info and "status" in task_info:
                logger.info(f"Found task {task_id} in Redis")
                
                response_data = {
                    'task_id': task_id,
                    'status': task_info.get('status', 'unknown'),
                    'submitted_at': task_info.get('submitted_at', ''),
                    'message': task_info.get('message', f'Task is {task_info.get("status")}')
                }
                
                # Add result data if completed
                if task_info.get('status') == 'completed' and 'result' in task_info:
                    try:
                        result_data = json.loads(task_info.get('result', '{}'))
                        response_data['result'] = result_data
                    except:
                        response_data['result'] = {'error': 'Failed to parse result data'}
                
                return response_data
        
        # Fall back to file-based task interface
        result = task_interface.get_task_result(task_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        status = result.get('status', 'unknown')
        
        response_data = {
            'task_id': task_id,
            'status': status,
            'submitted_at': result.get('created_at', ''),
            'message': result.get('message', f'Task is {status}')
        }
        
        # Add result data if completed
        if status == 'completed':
            response_data['result'] = {
                'stats': result.get('stats', {}),
                'completed_at': result.get('timestamp'),
                'data_location': 'Stored in worker data directory',
                'database_updated': 'Results stored in database via worker process'
            }
        elif status == 'error':
            response_data['result'] = {
                'error': result.get('error', 'Unknown error'),
                'error_time': result.get('timestamp')
            }
        elif status == 'processing':
            response_data['message'] = 'Task is currently being processed by worker'
        elif status == 'queued':
            response_data['message'] = 'Task is queued and waiting for worker to process'
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving task status: {str(e)}")

@app.get("/tasks")
async def list_tasks(limit: int = 20, redis=Depends(get_redis)):
    """List recent tasks and their statuses"""
    try:
        tasks = []
        
        # First try to get tasks from Redis
        if redis:
            try:
                # Get all active task IDs
                task_ids = redis.smembers("active_tasks")
                if task_ids:
                    for task_id in list(task_ids)[:limit]:
                        task_info = redis.hgetall(f"task:{task_id}")
                        if task_info:
                            # Parse JSON data if available
                            if 'data' in task_info:
                                try:
                                    task_info['data'] = json.loads(task_info['data'])
                                except:
                                    pass
                            
                            if 'result' in task_info:
                                try:
                                    task_info['result'] = json.loads(task_info['result'])
                                except:
                                    pass
                                
                            tasks.append(task_info)
                
                logger.info(f"Retrieved {len(tasks)} tasks from Redis")
                
                # If we didn't get enough tasks from Redis, supplement with file-based tasks
                if len(tasks) < limit:
                    file_tasks = task_interface.list_tasks(limit=limit - len(tasks))
                    if file_tasks:
                        tasks.extend(file_tasks)
            except Exception as e:
                logger.error(f"Error getting tasks from Redis: {e}")
        
        # If no tasks from Redis, fall back to file-based tasks
        if not tasks:
            tasks = task_interface.list_tasks(limit=limit)
        
        response = {
            "tasks": tasks,
            "total_shown": len(tasks),
            "limit": limit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "redis_connected": redis is not None,
            "worker_health": task_interface.get_worker_health()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing tasks: {str(e)}")

@app.post("/tasks/cleanup")
async def cleanup_tasks(max_age_hours: int = 24, redis=Depends(get_redis)):
    """Clean up old task files"""
    try:
        cleaned_count = task_interface.cleanup_old_tasks(max_age_hours)
        redis_cleaned = 0
        
        # Also clean up old tasks in Redis
        if redis:
            try:
                # Get all active task IDs
                task_ids = redis.smembers("active_tasks")
                now = datetime.now(timezone.utc)
                
                for task_id in task_ids:
                    task_info = redis.hgetall(f"task:{task_id}")
                    if task_info and 'submitted_at' in task_info:
                        try:
                            submitted_at = datetime.fromisoformat(task_info['submitted_at'])
                            age_hours = (now - submitted_at).total_seconds() / 3600
                            
                            if age_hours > max_age_hours:
                                redis.delete(f"task:{task_id}")
                                redis.srem("active_tasks", task_id)
                                redis_cleaned += 1
                        except:
                            # If we can't parse the date, assume it's old
                            redis.delete(f"task:{task_id}")
                            redis.srem("active_tasks", task_id)
                            redis_cleaned += 1
                
                logger.info(f"Cleaned up {redis_cleaned} old tasks from Redis")
            except Exception as e:
                logger.error(f"Error cleaning up tasks from Redis: {e}")
        
        return {
            "status": "success",
            "message": f"Cleaned up {cleaned_count} old task files and {redis_cleaned} Redis tasks",
            "cleaned_count_files": cleaned_count,
            "cleaned_count_redis": redis_cleaned,
            "max_age_hours": max_age_hours,
            "redis_connected": redis is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up tasks: {str(e)}")

# =======================================================
# PIPELINE API ENDPOINTS
# =======================================================

@app.post("/pipeline/run", response_model=dict)
async def run_pipeline(request: PipelineRequest):
    """
    Execute the complete data pipeline: scraping → processing → cleaning → database loading
    
    This endpoint triggers the full pipeline and returns immediately with a pipeline ID.
    Use /pipeline/{pipeline_id}/status to monitor progress.
    """
    try:
        logger.info(f"Executing pipeline for r/{request.subreddit}")
        
        # Convert Pydantic model to dict
        pipeline_request = {
            'subreddit': request.subreddit,
            'post_limit': request.post_limit,
            'comment_limit': request.comment_limit,
            'enable_processing': request.enable_processing,
            'enable_cleaning': request.enable_cleaning,
            'enable_database': request.enable_database,
            'priority': request.priority,
            'scheduled_time': request.scheduled_time,
            'notify_webhook': request.notify_webhook
        }
        
        # Execute pipeline via orchestrator
        pipeline_id = await asyn_worker.execute_pipeline_api(pipeline_request)
        
        return {
            "status": "accepted",
            "message": f"Pipeline started for r/{request.subreddit}",
            "pipeline_id": pipeline_id,
            "estimated_duration": "3-10 minutes",
            "steps": {
                "scraping": True,
                "processing": request.enable_processing,
                "cleaning": request.enable_cleaning,
                "database": request.enable_database
            },
            "endpoints": {
                "status": f"/pipeline/{pipeline_id}/status",
                "cancel": f"/pipeline/{pipeline_id}/cancel",
                "logs": f"/pipeline/{pipeline_id}/logs"
            },
            "submitted_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")

@app.get("/pipeline/{pipeline_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(pipeline_id: str):
    """
    Get the current status and progress of a pipeline execution
    
    Returns detailed information about pipeline progress, current step,
    completed steps, and any errors that occurred.
    """
    try:
        pipeline_status = asyn_worker.get_pipeline_status(pipeline_id)
        
        if not pipeline_status:
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
        
        return PipelineStatusResponse(
            pipeline_id=pipeline_status['pipeline_id'],
            status=pipeline_status['status'],
            current_step=pipeline_status.get('current_step'),
            progress=pipeline_status.get('progress', 0.0),
            steps_completed=pipeline_status.get('steps_completed', []),
            steps_failed=pipeline_status.get('steps_failed', []),
            started_at=pipeline_status.get('started_at'),
            completed_at=pipeline_status.get('completed_at'),
            estimated_completion=pipeline_status.get('estimated_completion'),
            result=pipeline_status.get('result'),
            error=pipeline_status.get('error'),
            logs=pipeline_status.get('logs', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving pipeline status: {str(e)}")

@app.delete("/pipeline/{pipeline_id}/cancel")
async def cancel_pipeline(pipeline_id: str):
    """
    Cancel a running or queued pipeline
    
    If the pipeline is currently running, it will be stopped gracefully.
    If it's queued, it will be removed from the queue.
    """
    try:
        success = asyn_worker.cancel_pipeline(pipeline_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Pipeline {pipeline_id} has been cancelled",
                "pipeline_id": pipeline_id,
                "cancelled_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found or cannot be cancelled")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling pipeline: {str(e)}")

@app.get("/pipeline/history", response_model=PipelineHistoryResponse)
async def get_pipeline_history(limit: int = 20):
    """
    Get pipeline execution history and statistics
    
    Returns information about recent pipeline executions, success rates,
    and performance statistics.
    """
    try:
        history = asyn_worker.get_pipeline_history(limit=limit)
        
        return PipelineHistoryResponse(
            total_executions=history['total_executions'],
            successful_executions=history['successful_executions'],
            failed_executions=history['failed_executions'],
            average_duration_minutes=history['average_duration_minutes'],
            recent_executions=history['recent_executions'],
            next_scheduled=history.get('next_scheduled')
        )
        
    except Exception as e:
        logger.error(f"Error getting pipeline history: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving pipeline history: {str(e)}")

@app.get("/pipeline/active")
async def get_active_pipelines():
    """
    Get all currently active (running or queued) pipelines
    
    Returns a list of pipelines that are currently executing or waiting to execute.
    """
    try:
        active_pipelines = asyn_worker.get_active_pipelines()
        
        return {
            "active_pipelines": len(active_pipelines),
            "pipelines": [
                {
                    "pipeline_id": pid,
                    "status": state['status'],
                    "current_step": state.get('current_step'),
                    "progress": state.get('progress', 0.0),
                    "started_at": state.get('started_at'),
                    "subreddit": state.get('request', {}).get('subreddit', 'unknown')
                }
                for pid, state in active_pipelines.items()
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting active pipelines: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving active pipelines: {str(e)}")

@app.get("/pipeline/{pipeline_id}/logs")
async def get_pipeline_logs(pipeline_id: str, tail: int = 50):
    """
    Get execution logs for a specific pipeline
    
    Returns the most recent log entries from the pipeline execution.
    """
    try:
        pipeline_status = asyn_worker.get_pipeline_status(pipeline_id)
        
        if not pipeline_status:
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
        
        logs = pipeline_status.get('logs', [])
        
        return {
            "pipeline_id": pipeline_id,
            "total_logs": len(logs),
            "logs": logs[-tail:] if logs else [],
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving pipeline logs: {str(e)}")

# =======================================================
# LIFESPAN MANAGEMENT
# =======================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Worker Service...")
    
    # Create data directories if they don't exist
    os.makedirs("worker/data", exist_ok=True)
    os.makedirs("worker/logs", exist_ok=True)
    
    # Initialize Redis connection if not already connected
    global redis_client
    if not redis_client:
        try:
            redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                decode_responses=True
            )
            # Check connection
            redis_client.ping()
            logger.info("✅ Connected to Redis successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            redis_client = None

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("🛑 Worker Service shutting down...")
    
    # Close Redis connection if open
    global redis_client
    if redis_client:
        try:
            redis_client.close()
            logger.info("✅ Redis connection closed")
        except:
            pass

# =======================================================
# MAIN ENTRY POINT
# =======================================================

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8082))
    
    logger.info(f"🚀 Starting Worker Service on {host}:{port}")
    
    uvicorn.run(
        "worker.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
        access_log=True
    )
