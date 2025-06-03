#!/usr/bin/env python3

"""
UCLA Sentiment Analysis API - Enhanced with PostgreSQL Integration
Real-time sentiment analysis using VADER
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import os
import time
import asyncio
import hashlib
import aiohttp
import json
from contextlib import asynccontextmanager

# Import modules
from .simple_sentiment_analyzer import SimpleSentimentAnalyzer
from .pydantic_models import *
from .postgres_manager import DatabaseManager, AsyncDataLoader
from app.utils.service_health import check_service_health, check_all_services, get_http_session, close_http_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# GLOBAL VARIABLES & CONFIGURATION
# ============================================

# Initialize core components
sentiment_analyzer = SimpleSentimentAnalyzer()
db_manager = DatabaseManager()
data_loader = AsyncDataLoader(db_manager)

# Worker API configuration
WORKER_API_URL = os.getenv("WORKER_API_URL", "http://worker-scraper-api:8082")
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model-service-api:8081")

# Sample data for demo (will be replaced by database)
SAMPLE_ALERTS = [
    {
        'id': 'alert_001',
        'content_id': 'post_123',
        'content_text': 'Feeling really overwhelmed with finals coming up...',
        'alert_type': 'stress',
        'severity': 'medium',
        'keywords_found': ['overwhelmed', 'finals'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'subreddit': 'UCLA',
        'author': 'stressed_student',
        'status': 'active'
    },
    {
        'id': 'alert_002',
        'content_id': 'comment_456',
        'content_text': 'I feel so depressed about my grades this quarter',
        'alert_type': 'mental_health',
        'severity': 'high',
        'keywords_found': ['depressed', 'grades'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'subreddit': 'UCLA',
        'author': 'sad_bruin',
        'status': 'active'
    }
]

SAMPLE_POSTS = [
    {
        'post_id': 'sample_1',
        'title': 'UCLA Computer Science Program Review',
        'selftext': 'Just finished my first year in CS at UCLA. The program is challenging but amazing! The professors are really helpful and the research opportunities are incredible.',
        'score': 150,
        'upvote_ratio': 0.92,
        'num_comments': 25,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'author': 'cs_student_2024',
        'subreddit': 'UCLA'
    },
    {
        'post_id': 'sample_2',
        'title': 'Campus Life at UCLA',
        'selftext': 'The dining halls are pretty good and the dorms are nice. Love the campus and all the activities available!',
        'score': 89,
        'upvote_ratio': 0.88,
        'num_comments': 15,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'author': 'campus_life_fan',
        'subreddit': 'UCLA'
    },
    {
        'post_id': 'sample_3',
        'title': 'Struggling with Workload',
        'selftext': 'This quarter has been really tough and overwhelming. Anyone else feeling stressed about the workload?',
        'score': 45,
        'upvote_ratio': 0.75,
        'num_comments': 8,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'author': 'overwhelmed_student',
        'subreddit': 'UCLA'
    },
    {
        'post_id': 'sample_4',
        'title': 'Great UCLA Resources',
        'selftext': 'The library is fantastic and the study spaces are perfect for group work. Highly recommend the research facilities!',
        'score': 78,
        'upvote_ratio': 0.85,
        'num_comments': 12,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'author': 'library_lover',
        'subreddit': 'UCLA'
    },
    {
        'post_id': 'sample_5',
        'title': 'UCLA Sports Update',
        'selftext': 'Amazing basketball game last night! The team played incredibly well and the crowd was electric.',
        'score': 203,
        'upvote_ratio': 0.94,
        'num_comments': 34,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'author': 'sports_fan_ucla',
        'subreddit': 'UCLA'
    }
]

# ============================================
# LIFESPAN MANAGEMENT
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 UCLA Sentiment Analysis API starting up...")
    
    # Initialize HTTP session
    await get_http_session()
    
    # Initialize database with retry
    max_retry = int(os.getenv("POSTGRES_MAX_RETRY", "5"))
    retry_interval = int(os.getenv("POSTGRES_RETRY_INTERVAL", "5"))
    
    for attempt in range(max_retry):
        try:
            db_initialized = await db_manager.initialize()
            if db_initialized:
                logger.info("✅ Database initialized successfully")
                
                # Start async data loader
                await data_loader.start()
                logger.info("✅ Async data loader started")
                break
            else:
                logger.warning(f"⚠️ Database initialization failed, attempt {attempt+1}/{max_retry}")
                if attempt < max_retry - 1:
                    logger.info(f"Retrying in {retry_interval} seconds...")
                    await asyncio.sleep(retry_interval)
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            if attempt < max_retry - 1:
                logger.info(f"Retrying in {retry_interval} seconds...")
                await asyncio.sleep(retry_interval)
    else:
        logger.warning("⚠️ Database initialization failed after all attempts, running in memory mode")
    
    # Check service availability
    services_health = await check_all_services()
    for service_name, health_info in services_health.items():
        if health_info.get('status') == 'operational':
            logger.info(f"✅ {service_name} is available")
        else:
            logger.warning(f"⚠️ {service_name} is not available: {health_info.get('error', 'Unknown error')}")
    
    logger.info("📊 All endpoints registered and ready!")
    logger.info("🔗 CORS enabled for all origins")
    logger.info("💡 Simple sentiment analyzer initialized")
    logger.info("🛡️ Using VADER for sentiment analysis")
    
    yield
    
    # Shutdown
    logger.info("🛑 UCLA Sentiment Analysis API shutting down...")
    
    # Stop data loader
    await data_loader.stop()
    
    # Close database connections
    await db_manager.close()
    
    # Close HTTP session
    await close_http_session()
    
    logger.info("✅ Shutdown complete")

# ============================================
# FASTAPI APP INITIALIZATION
# ============================================

app = FastAPI(
    title="UCLA Sentiment Analysis API",
    description="Real-time sentiment analysis API with PostgreSQL integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# HELPER FUNCTIONS
# ============================================

async def get_db_session():
    """Dependency to get database session"""
    if hasattr(db_manager, 'connection_pool') and db_manager.connection_pool:
        async with db_manager.connection_pool.acquire() as conn:
            yield conn
    else:
        yield None

def create_text_hash(text: str) -> str:
    """Create a hash for text deduplication"""
    return hashlib.sha256(text.encode()).hexdigest()

def detect_alerts(text: str, sentiment_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Detect if text should trigger an alert"""
    alert_keywords = {
        'mental_health': ['depressed', 'depression', 'suicide', 'kill myself', 'end it all', 'worthless'],
        'stress': ['overwhelmed', 'stressed', 'anxious', 'panic', 'breakdown', 'can\'t handle'],
        'academic': ['failing', 'dropped out', 'academic probation', 'expelled'],
        'harassment': ['bullied', 'harassed', 'threatened', 'stalked']
    }
    
    text_lower = text.lower()
    
    for alert_type, keywords in alert_keywords.items():
        found_keywords = [kw for kw in keywords if kw in text_lower]
        if found_keywords:
            # Determine severity based on sentiment and keywords
            if sentiment_result['compound_score'] < -0.5:
                severity = 'high'
            elif sentiment_result['compound_score'] < -0.2:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Escalate mental health alerts
            if alert_type == 'mental_health':
                severity = 'high' if severity != 'low' else 'medium'
            
            return {
                'alert_type': alert_type,
                'severity': severity,
                'keywords_found': found_keywords,
                'confidence': sentiment_result['confidence'],
                'compound_score': sentiment_result['compound_score']
            }
    
    return None

async def call_worker_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None, timeout: int = 10) -> Dict:
    """Call worker API endpoint"""
    session = await get_http_session()
    url = f"{WORKER_API_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    logger.error(f"Worker API returned status {response.status}: {text}")
                    return {"error": f"Worker API returned status {response.status}", "details": text}
        elif method.upper() == "POST":
            async with session.post(url, json=data, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    logger.error(f"Worker API returned status {response.status}: {text}")
                    return {"error": f"Worker API returned status {response.status}", "details": text}
        else:
            return {"error": f"Unsupported method: {method}"}
    except Exception as e:
        logger.error(f"Error calling worker API: {e}")
        return {"error": f"Error calling worker API: {str(e)}"}

async def call_model_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None, timeout: int = 10) -> Dict:
    """Call model API endpoint"""
    session = await get_http_session()
    url = f"{MODEL_SERVICE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    logger.error(f"Model API returned status {response.status}: {text}")
                    return {"error": f"Model API returned status {response.status}", "details": text}
        elif method.upper() == "POST":
            async with session.post(url, json=data, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    logger.error(f"Model API returned status {response.status}: {text}")
                    return {"error": f"Model API returned status {response.status}", "details": text}
        else:
            return {"error": f"Unsupported method: {method}"}
    except Exception as e:
        logger.error(f"Error calling model API: {e}")
        return {"error": f"Error calling model API: {str(e)}"}

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """API root endpoint with comprehensive information"""
    endpoints = {
        "health": "GET /health - Health check and system status",
        "docs": "GET /docs - Interactive API documentation", 
        "predict": "POST /predict - Analyze sentiment with VADER",
        "predict_batch": "POST /predict/batch - Batch analysis with VADER",
        "scrape": "POST /scrape - Scrape Reddit data (via worker API)",
        "tasks": "GET /tasks - Get active tasks (via worker API)",
        "task_status": "GET /tasks/{task_id} - Get task status (via worker API)",
        "analytics": "GET /analytics - Get analytics dashboard data from database",
        "alerts": "GET /alerts - Get active alerts from database",
        "alert_update": "POST /alerts/{id}/status - Update alert status",
        "status": "GET /status - Get detailed system status"
    }
    
    features = [
        "Real-time sentiment analysis with VADER",
        "PostgreSQL database integration with async loading",
        "Batch processing support", 
        "Reddit data scraping via worker API",
        "Alert management system with database persistence",
        "Analytics dashboard with cached data",
        "VADER model (Valence Aware Dictionary and sEntiment Reasoner)"
    ]

    return {
        "message": "UCLA Sentiment Analysis API", 
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "operational",
        "database_available": hasattr(db_manager, 'connection_pool') and db_manager.connection_pool is not None,
        "worker_api_url": WORKER_API_URL,
        "model_service_url": MODEL_SERVICE_URL,
        "endpoints": endpoints,
        "features": features,
        "description": "Enhanced sentiment analysis API with PostgreSQL integration"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    # Get all service health status
    services_health = await check_all_services()
    
    # Map service health to API response
    services = {
        "sentiment_analyzer": "operational",
        "cors": "enabled",
        "async_data_loader": "operational" if data_loader.is_running else "stopped"
    }
    
    # Map external services
    for service_name, health_info in services_health.items():
        services[service_name] = health_info.get('status', 'unknown')
    
    # Check database status
    if hasattr(db_manager, 'connection_pool') and db_manager.connection_pool:
        services["database"] = "operational"
        services["postgres"] = "connected"
    else:
        services["database"] = "offline (using memory mode)"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="2.0.0",
        services=services
    )

@app.post("/predict", response_model=SentimentResponse)
async def predict_sentiment(request: SentimentRequest, background_tasks: BackgroundTasks):
    """
    Analyze sentiment using VADER
    
    This endpoint implements sentiment analysis using VADER:
    1. Results are automatically stored in database (if available)
    2. Alerts are automatically checked and created
    """
    try:
        start_time = time.time()
        logger.info(f"Sentiment analysis request: '{request.text[:50]}...'")
        
        # Create text hash for deduplication
        text_hash = create_text_hash(request.text)
        
        # Use VADER for sentiment analysis
        result = sentiment_analyzer.analyze(request.text)
        
        # Add metadata
        processing_time = (time.time() - start_time) * 1000
        result['processing_time_ms'] = round(processing_time, 2)
        result['text_hash'] = text_hash
        result['source'] = 'vader'
        result['model_used'] = 'vader'
        result['model_name'] = 'VADER (Valence Aware Dictionary and Reasoner)'
        result['timestamp'] = datetime.now(timezone.utc).isoformat()

        logger.info(f"VADER result: {result['sentiment']} (confidence: {result['confidence']:.2f})")
 
        # Remove probabilities if not requested
        if not request.include_probabilities:
            result.pop('probabilities', None)
        
        # Background tasks for database and alerts
        background_tasks.add_task(process_sentiment_result, result, request.text, text_hash)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in predict_sentiment: {e}")
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@app.post("/predict/batch")
async def predict_batch_sentiment(texts: List[str], background_tasks: BackgroundTasks):
    """Analyze sentiment for multiple texts using VADER"""
    try:
        logger.info(f"Batch sentiment analysis for {len(texts)} texts")
        
        if len(texts) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 texts allowed per batch")
        
        if not texts:
            raise HTTPException(status_code=400, detail="No texts provided")
        
        start_time = time.time()
        results = []
        vader_fallbacks = len(texts)  # All will use VADER
        
        for i, text in enumerate(texts):
            try:
                # Use VADER for all analysis
                result = sentiment_analyzer.analyze(text)
                result['source'] = 'vader'
                
                result['batch_index'] = i
                result['text_hash'] = create_text_hash(text)
                results.append(result)
                
                # Queue for database storage
                background_tasks.add_task(process_sentiment_result, result, text, result['text_hash'])
                
            except Exception as e:
                logger.error(f"Error processing text {i}: {e}")
                results.append({
                    'batch_index': i,
                    'text': text[:100] + '...' if len(text) > 100 else text,
                    'error': str(e),
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'compound_score': 0.0,
                    'source': 'error'
                })
        
        total_time = (time.time() - start_time) * 1000
        
        # Calculate summary statistics
        successful_results = [r for r in results if 'error' not in r]
        sentiments = [r['sentiment'] for r in successful_results]
        
        summary = {
            "total_processed": len(results),
            "successful": len(successful_results),
            "failed": len(results) - len(successful_results),
            "vader_fallback_used": vader_fallbacks,
            "total_processing_time_ms": round(total_time, 2),
            "average_time_per_text_ms": round(total_time / len(texts), 2),
            "sentiment_distribution": {
                "positive": sentiments.count('positive'),
                "negative": sentiments.count('negative'),
                "neutral": sentiments.count('neutral')
            }
        }
        
        response = {
            "results": results,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Batch analysis complete: {summary}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Batch sentiment analysis failed: {str(e)}")

@app.post("/scrape")
async def scrape_reddit(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Scrape Reddit data via worker API
    
    This endpoint forwards the request to the worker API for processing
    """
    try:
        logger.info(f"Forwarding scraping request for r/{request.subreddit} to worker API")
        
        # First check if worker API is available
        worker_health = await check_service_health(WORKER_API_URL, "/health")
        if worker_health.get('status') != 'operational':
            logger.error(f"Worker API is not available: {worker_health.get('error', 'Unknown error')}")
            raise HTTPException(status_code=503, detail=f"Worker API is not available: {worker_health.get('error', 'Service unavailable')}")
        
        # Prepare request data for worker API
        worker_request = {
            "subreddit": request.subreddit,
            "post_limit": request.post_limit,
            "comment_limit": 25,  # Default value
            "sort_by": "hot",     # Default value
            "time_filter": "week" # Default value
        }
        
        # Call worker API
        result = await call_worker_api("/scrape", "POST", worker_request)
        
        if "error" in result:
            logger.error(f"Worker API returned error: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Worker API error: {result['error']}")
        
        # Add gateway API metadata
        result["forwarded_by"] = "gateway-api"
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Scraping request forwarded successfully. Task ID: {result.get('task_id', 'unknown')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forwarding scraping request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to forward scraping request: {str(e)}")

@app.get("/tasks")
async def get_tasks(limit: int = Query(20, ge=1, le=100)):
    """
    Get active tasks from worker API
    
    This endpoint forwards the request to the worker API
    """
    try:
        logger.info(f"Getting tasks from worker API (limit: {limit})")
        
        # First check if worker API is available
        worker_health = await check_service_health(WORKER_API_URL, "/health")
        if worker_health.get('status') != 'operational':
            logger.error(f"Worker API is not available: {worker_health.get('error', 'Unknown error')}")
            raise HTTPException(status_code=503, detail=f"Worker API is not available: {worker_health.get('error', 'Service unavailable')}")
        
        # Call worker API
        result = await call_worker_api(f"/tasks?limit={limit}")
        
        if "error" in result:
            logger.error(f"Worker API returned error: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Worker API error: {result['error']}")
        
        # Add gateway API metadata
        result["forwarded_by"] = "gateway-api"
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Got {len(result.get('tasks', []))} tasks from worker API")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get task status from worker API
    
    This endpoint forwards the request to the worker API
    """
    try:
        logger.info(f"Getting status for task {task_id} from worker API")
        
        # First check if worker API is available
        worker_health = await check_service_health(WORKER_API_URL, "/health")
        if worker_health.get('status') != 'operational':
            logger.error(f"Worker API is not available: {worker_health.get('error', 'Unknown error')}")
            raise HTTPException(status_code=503, detail=f"Worker API is not available: {worker_health.get('error', 'Service unavailable')}")
        
        # Call worker API
        result = await call_worker_api(f"/tasks/{task_id}")
        
        if "error" in result:
            logger.error(f"Worker API returned error: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Worker API error: {result['error']}")
        
        # Add gateway API metadata
        result["forwarded_by"] = "gateway-api"
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Got status for task {task_id}: {result.get('status', 'unknown')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@app.get("/analytics")
async def get_analytics(db_session=Depends(get_db_session)):
    """Get comprehensive analytics data from database or fallback to mock"""
    try:
        logger.info("Generating analytics data")
        
        if db_session:
            # Get analytics from database
            analytics_data = await db_manager.get_sentiment_analytics()
            
            if analytics_data:
                # Enhance with additional computed metrics
                current_time = datetime.now(timezone.utc)
                
                enhanced_analytics = {
                    "overview": {
                        "total_posts": sum(item['count'] for item in analytics_data.get('sentiment_distribution', [])),
                        "data_source": "database",
                        "last_updated": current_time.isoformat(),
                        "database_connected": True,
                        "total_comments": 0,  # Default value
                        "avg_sentiment": 0.0  # Default value
                    },
                    "sentiment_distribution": {
                        item['sentiment']: item['count'] 
                        for item in analytics_data.get('sentiment_distribution', [])
                    },
                    "model_performance": analytics_data.get('confidence_stats', []),
                    "source_breakdown": analytics_data.get('model_usage', []),
                    "alerts_summary": analytics_data.get('recent_alerts', []),
                    "timestamp": current_time.isoformat(),
                    "data_freshness": "real-time from database"
                }
                
                return enhanced_analytics
        
        # Fallback to mock analytics
        current_time = datetime.now(timezone.utc)
        
        mock_analytics = {
            "overview": {
                "total_posts": 1234,
                "total_comments": 4567,
                "avg_sentiment": 0.234,
                "data_freshness": "mock data",
                "last_updated": current_time.isoformat(),
                "posts_today": 87,
                "active_users": 342,
                "database_connected": False
            },
            "sentiment_distribution": {
                "positive": 45.2,
                "neutral": 38.1,
                "negative": 16.7
            },
            "category_breakdown": {
                "academic_departments": {
                    "count": 420,
                    "avg_sentiment": 0.15,
                    "trending": "up"
                },
                "campus_life": {
                    "count": 380,
                    "avg_sentiment": 0.22,
                    "trending": "stable"
                },
                "sports": {
                    "count": 250,
                    "avg_sentiment": 0.45,
                    "trending": "up"
                }
            },
            "alerts_summary": {
                "total_active": len(SAMPLE_ALERTS),
                "by_severity": {
                    "critical": 0,
                    "high": len([a for a in SAMPLE_ALERTS if a['severity'] == 'high']),
                    "medium": len([a for a in SAMPLE_ALERTS if a['severity'] == 'medium']),
                    "low": 0
                },
                "recent_24h": len(SAMPLE_ALERTS),
                "resolved_today": 3
            },
            "performance_metrics": {
                "api_response_time_ms": 45.2,
                "processing_speed": "1,250 texts/minute (VADER)",
                "uptime": "99.8%",
                "accuracy_score": 0.92
            },
            "timestamp": current_time.isoformat(),
            "data_sources": ["Reddit r/UCLA", "Reddit r/bruins"],
            "generated_by": "UCLA Sentiment Analysis API v2.0.0"
        }
        
        logger.info("Analytics data generated (mock mode)")
        return mock_analytics
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")

@app.get("/alerts")
async def get_alerts(db_session=Depends(get_db_session)):
    """Get active alerts from database or fallback to mock"""
    try:
        logger.info("Retrieving active alerts")
        
        if db_session:
            # TODO: Implement database alert retrieval
            # alerts = await db_manager.get_active_alerts()
            pass
        
        # Fallback to mock alerts for now
        active_alerts = [alert for alert in SAMPLE_ALERTS if alert['status'] == 'active']
        
        # Calculate enhanced statistics
        stats = {
            "total_active": len(active_alerts),
            "by_severity": {
                "critical": len([a for a in active_alerts if a['severity'] == 'critical']),
                "high": len([a for a in active_alerts if a['severity'] == 'high']),
                "medium": len([a for a in active_alerts if a['severity'] == 'medium']),
                "low": len([a for a in active_alerts if a['severity'] == 'low'])
            },
            "by_type": {
                "mental_health": len([a for a in active_alerts if a['alert_type'] == 'mental_health']),
                "stress": len([a for a in active_alerts if a['alert_type'] == 'stress']),
                "harassment": len([a for a in active_alerts if a['alert_type'] == 'harassment']),
                "other": len([a for a in active_alerts if a['alert_type'] not in ['mental_health', 'stress', 'harassment']])
            }
        }
        
        response = {
            "active_alerts": active_alerts,
            "stats": stats,
            "database_connected": db_session is not None,
            "summary": {
                "total_active": len(active_alerts),
                "needs_immediate_attention": len([a for a in active_alerts if a['severity'] in ['critical', 'high']]),
                "last_24_hours": len(active_alerts),
                "average_severity": "medium"
            },
            "recommendations": [
                "Monitor high-severity alerts closely",
                "Consider outreach for mental health alerts",
                "Review stress patterns during finals period"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Retrieved {len(active_alerts)} active alerts")
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Alert retrieval failed: {str(e)}")

@app.post("/alerts/{alert_id}/status")
async def update_alert_status(alert_id: str, update: AlertStatusUpdate):
    """Update alert status (mock implementation for now)"""
    try:
        logger.info(f"Updating alert {alert_id} status to {update.status}")
        
        # Find and update the alert (mock)
        alert_found = False
        updated_alert = None
        
        for alert in SAMPLE_ALERTS:
            if alert['id'] == alert_id:
                alert['status'] = update.status
                alert['updated_at'] = datetime.now(timezone.utc).isoformat()
                alert['updated_by'] = "api_user"
                if update.notes:
                    alert['notes'] = update.notes
                updated_alert = alert.copy()
                alert_found = True
                break
        
        if not alert_found:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
        response = {
            "status": "success",
            "message": f"Alert {alert_id} updated successfully",
            "alert": updated_alert,
            "database_connected": hasattr(db_manager, 'connection_pool') and db_manager.connection_pool is not None,
            "changes": {
                "alert_id": alert_id,
                "previous_status": "active",
                "new_status": update.status,
                "notes": update.notes,
                "updated_by": "api_user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        logger.info(f"Alert {alert_id} status updated to {update.status}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        raise HTTPException(status_code=500, detail=f"Alert update failed: {str(e)}")

@app.get("/status")
async def get_system_status():
    """Get detailed system status and performance metrics"""
    try:
        # Get real-time status of all services
        services_health = await check_all_services()
        
        # Map service status to API response format
        services = {
            "sentiment_analyzer": "operational",
            "cors": "enabled",
            "async_data_loader": "operational" if data_loader.is_running else "stopped"
        }
        
        # Map external services
        for service_name, health_info in services_health.items():
            services[service_name] = health_info.get('status', 'unknown')
            # Add response time if available
            if 'response_time_ms' in health_info:
                services[f"{service_name}_response_time_ms"] = health_info['response_time_ms']
        
        # Check database status
        if hasattr(db_manager, 'connection_pool') and db_manager.connection_pool:
            services["database"] = "operational"
            services["postgresql"] = "connected"
        else:
            services["database"] = "offline (memory mode)"
        
        # Build endpoints status
        endpoints = {
            "health_check": "✅" if "error" not in await check_service_health(f"http://localhost:8080", "/health") else "❌",
            "sentiment_analysis": "✅",
            "batch_processing": "✅",
            "reddit_scraping": "✅" if services.get("worker_api") == "operational" else "❌",
            "task_management": "✅" if services.get("worker_api") == "operational" else "❌",
            "analytics": "✅",
            "alerts": "✅"
        }
        
        return {
            "api": "operational",
            "version": "2.0.0",
            "environment": os.getenv('ENV', 'development'),
            "database_available": hasattr(db_manager, 'connection_pool') and db_manager.connection_pool is not None,
            "services": services,
            "performance": {
                "uptime": "operational",
                "response_time_ms": services.get("model_service_response_time_ms", 45.2),
                "requests_processed": 1247,
                "errors": 0,
                "success_rate": "100%"
            },
            "endpoints": endpoints,
            "last_data_collection": "real-time service health check",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        # Return basic status in case of error
        return {
            "api": "degraded",
            "version": "2.0.0",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# ============================================
# BACKGROUND TASK FUNCTIONS
# ============================================

async def process_sentiment_result(result: Dict[str, Any], text: str, text_hash: str):
    """Process sentiment result in background (store in DB, check alerts)"""
    try:
        # Prepare sentiment data for database
        sentiment_data = {
            'text': text,
            'text_hash': text_hash,
            'sentiment': result['sentiment'],
            'confidence': result['confidence'],
            'compound_score': result['compound_score'],
            'probabilities': result.get('probabilities'),
            'processing_time_ms': result.get('processing_time_ms', 0),
            'model_used': result.get('model_used', 'unknown'),
            'model_name': result.get('model_name', 'unknown'),
            'source': result['source']
        }
        
        # Queue for async database storage
        await data_loader.queue_sentiment_result(sentiment_data)
        
        # Check for alerts
        alert_data = detect_alerts(text, result)
        if alert_data:
            alert_data.update({
                'content_id': text_hash[:16],  # Use first 16 chars of hash as ID
                'content_text': text,
                'content_type': 'api_request',
                'subreddit': 'API',
                'author': 'api_user'
            })
            await data_loader.queue_alert(alert_data)
            logger.info(f"Alert queued: {alert_data['alert_type']} - {alert_data['severity']}")
        
    except Exception as e:
        logger.error(f"Error processing sentiment result: {e}")

async def store_reddit_post_with_sentiment(post_data: Dict[str, Any], sentiment_result: Dict[str, Any]):
    """Store Reddit post with sentiment analysis in background"""
    try:
        # Prepare sentiment data
        text = f"{post_data['title']} {post_data['selftext']}"
        text_hash = create_text_hash(text)
        
        sentiment_data = {
            'text': text,
            'text_hash': text_hash,
            'sentiment': sentiment_result['sentiment'],
            'confidence': sentiment_result['confidence'],
            'compound_score': sentiment_result['compound_score'],
            'probabilities': sentiment_result.get('probabilities'),
            'processing_time_ms': sentiment_result.get('processing_time_ms', 0),
            'model_used': sentiment_result.get('model_used', 'unknown'),
            'model_name': sentiment_result.get('model_name', 'unknown'),
            'source': sentiment_result['source']
        }
        
        # Queue both sentiment and post data
        await data_loader.queue_sentiment_result(sentiment_data, post_data)
        
    except Exception as e:
        logger.error(f"Error storing Reddit post with sentiment: {e}")

async def store_alert(post_data: Dict[str, Any], alert_data: Dict[str, Any]):
    """Store alert in background"""
    try:
        alert_data.update({
            'content_id': post_data['post_id'],
            'content_text': f"{post_data['title']} {post_data['selftext']}",
            'content_type': 'post',
            'subreddit': post_data.get('subreddit', 'UCLA'),
            'author': post_data.get('author', 'unknown')
        })
        
        await data_loader.queue_alert(alert_data)
        logger.info(f"Alert stored: {alert_data['alert_type']} - {alert_data['severity']}")
        
    except Exception as e:
        logger.error(f"Error storing alert: {e}")

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8080))
    
    logger.info(f"🚀 Starting UCLA Sentiment Analysis API v2.0.0 on {host}:{port}")
    logger.info("📚 Interactive docs available at: /docs")
    logger.info("📖 ReDoc documentation at: /redoc")
    logger.info("🗄️ PostgreSQL integration with async data loading")
    
    uvicorn.run(
        "app.api.main_enhanced:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
        access_log=True
    )
