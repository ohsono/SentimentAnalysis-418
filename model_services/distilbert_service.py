#!/usr/bin/env python3

"""
DistilBERT Model Service - Lightweight LLM API
Provides /predict/llm and /predict/llm/batch endpoints for sentiment analysis
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import os
import time
import uvicorn
import asyncio
from contextlib import asynccontextmanager

# Import our DistilBERT manager
from .distilbert_manager import DistilBERTModelManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model manager
model_manager: Optional[DistilBERTModelManager] = None

# ============================================
# PYDANTIC MODELS
# ============================================

class LLMPredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    model: str = Field(default="distilbert-sentiment", description="Model to use for prediction")
    include_probabilities: bool = Field(default=True, description="Include probability scores")

class LLMBatchRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts to analyze")
    model: str = Field(default="distilbert-sentiment", description="Model to use for prediction")
    include_probabilities: bool = Field(default=True, description="Include probability scores")

class HealthResponse(BaseModel):
    status: str
    service: str
    model_manager_available: bool
    loaded_models: List[str]
    memory_info: Dict[str, Any]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    service: str
    model_manager_available: bool
    loaded_models: List[str]
    memory_info: Dict[str, Any]
    timestamp: str

# ============================================
# SERVICE METRICS
# ============================================

service_metrics = {
    "requests_processed": 0,
    "successful_predictions": 0,
    "failed_predictions": 0,
    "total_processing_time": 0.0,
    "startup_time": datetime.now(timezone.utc)
}

# ============================================
# LIFESPAN MANAGEMENT
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global model_manager
    
    # Startup
    logger.info("🤖 Starting DistilBERT Model Service...")
    
    try:
        # Initialize model manager
        model_cache_dir = os.getenv("MODEL_CACHE_DIR", "/app/models")
        model_manager = DistilBERTModelManager(model_cache_dir)
        
        # Pre-load default model
        preload_model = os.getenv("PRELOAD_MODEL", "distilbert-sentiment")
        if preload_model:
            logger.info(f"Pre-loading model: {preload_model}")
            model_manager.load_model(preload_model)
            logger.info(f"✅ Pre-loaded model: {preload_model}")
        
        logger.info("✅ DistilBERT Model Service ready")
        
    except Exception as e:
        logger.error(f"Failed to initialize model service: {e}")
        model_manager = None
    
    yield
    
    # Shutdown
    logger.info("🛑 DistilBERT Model Service shutting down...")
    if model_manager:
        model_manager.cleanup()

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="UCLA Sentiment Analysis - DistilBERT Model Service",
    description="Lightweight LLM service for sentiment analysis using DistilBERT",
    version="1.0.0",
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
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Model service information"""
    return {
        "service": "UCLA Sentiment Analysis - DistilBERT Model Service",
        "version": "1.0.0",
        "description": "Lightweight LLM service for sentiment analysis using DistilBERT",
        "model_type": "DistilBERT",
        "architecture": "transformer",
        "task": "sentiment-analysis",
        "endpoints": {
            "health": "GET /health - Service health check",
            "predict_llm": "POST /predict/llm - Single text sentiment analysis",
            "predict_llm_batch": "POST /predict/llm/batch - Batch text sentiment analysis",
            "models": "GET /models - List available models",
            "model_info": "GET /models/{model_key} - Get model details",
            "metrics": "GET /metrics - Service performance metrics"
        },
        "features": [
            "Fast DistilBERT inference",
            "Batch processing support",
            "Multiple model variants",
            "Pre-downloaded models",
            "CPU optimized"
        ],
        "model_manager_available": model_manager is not None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check for model service"""
    if not model_manager:
        return HealthResponse(
            status="unhealthy",
            service="distilbert-model-service",
            model_manager_available=False,
            loaded_models=[],
            memory_info={},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    try:
        health_info = model_manager.get_health_status()
        
        return HealthResponse(
            status="healthy",
            service="distilbert-model-service",
            model_manager_available=True,
            loaded_models=health_info["loaded_models"],
            memory_info=health_info["memory_usage"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="degraded",
            service="distilbert-model-service",
            model_manager_available=False,
            loaded_models=[],
            memory_info={},
            timestamp=datetime.now(timezone.utc).isoformat()
        )

@app.post("/predict/llm")
async def predict_llm(request: LLMPredictionRequest):
    """
    LLM Sentiment Prediction Endpoint
    
    Analyzes sentiment using DistilBERT or other specified models.
    Returns sentiment classification with confidence scores.
    """
    if not model_manager:
        raise HTTPException(
            status_code=503,
            detail="Model service not available - model manager failed to initialize"
        )
    
    start_time = time.time()
    service_metrics["requests_processed"] += 1
    
    try:
        logger.info(f"LLM prediction request: {request.model} for text length {len(request.text)}")
        
        # Get prediction from model manager
        result = model_manager.predict_sentiment(request.text, request.model)
        
        # Remove probabilities if not requested
        if not request.include_probabilities:
            result.pop('probabilities', None)
        
        # Add service metadata
        processing_time = (time.time() - start_time) * 1000
        result.update({
            'service': 'distilbert-model-service',
            'service_version': '1.0.0',
            'endpoint': '/predict/llm',
            'request_processing_time_ms': round(processing_time, 2),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # Update metrics
        service_metrics["successful_predictions"] += 1
        service_metrics["total_processing_time"] += processing_time
        
        logger.info(f"LLM prediction complete: {result['sentiment']} (conf: {result['confidence']:.3f}, {processing_time:.1f}ms)")
        return result
        
    except Exception as e:
        service_metrics["failed_predictions"] += 1
        logger.error(f"Error in LLM prediction: {e}")
        raise HTTPException(status_code=500, detail=f"LLM prediction failed: {str(e)}")

@app.post("/predict/llm/batch")
async def predict_llm_batch(request: LLMBatchRequest):
    """
    LLM Batch Sentiment Prediction Endpoint
    
    Analyzes sentiment for multiple texts efficiently using DistilBERT.
    Optimized for batch processing with detailed summary statistics.
    """
    if not model_manager:
        raise HTTPException(
            status_code=503,
            detail="Model service not available - model manager failed to initialize"
        )
    
    start_time = time.time()
    service_metrics["requests_processed"] += 1
    
    try:
        logger.info(f"LLM batch prediction request: {request.model} for {len(request.texts)} texts")
        
        # Validate batch size
        if len(request.texts) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 texts allowed per batch")
        
        # Get batch predictions from model manager
        results = model_manager.predict_batch(request.texts, request.model)
        
        # Remove probabilities if not requested
        if not request.include_probabilities:
            for result in results:
                result.pop('probabilities', None)
        
        total_time = (time.time() - start_time) * 1000
        
        # Calculate detailed summary
        successful_results = [r for r in results if 'error' not in r]
        sentiments = [r['sentiment'] for r in successful_results]
        confidences = [r['confidence'] for r in successful_results]
        
        summary = {
            "total_processed": len(results),
            "successful": len(successful_results),
            "failed": len(results) - len(successful_results),
            "total_processing_time_ms": round(total_time, 2),
            "average_time_per_text_ms": round(total_time / len(request.texts), 2),
            "model_used": request.model,
            "service": "distilbert-model-service",
            "endpoint": "/predict/llm/batch",
            "sentiment_distribution": {
                "positive": sentiments.count('positive'),
                "negative": sentiments.count('negative'),
                "neutral": sentiments.count('neutral')
            },
            "confidence_stats": {
                "average": round(sum(confidences) / len(confidences), 3) if confidences else 0,
                "min": round(min(confidences), 3) if confidences else 0,
                "max": round(max(confidences), 3) if confidences else 0
            }
        }
        
        response = {
            "results": results,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Update metrics
        service_metrics["successful_predictions"] += len(successful_results)
        service_metrics["failed_predictions"] += (len(results) - len(successful_results))
        service_metrics["total_processing_time"] += total_time
        
        logger.info(f"LLM batch prediction complete: {summary}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        service_metrics["failed_predictions"] += 1
        logger.error(f"Error in LLM batch prediction: {e}")
        raise HTTPException(status_code=500, detail=f"LLM batch prediction failed: {str(e)}")

@app.get("/models")
async def list_models():
    """List available DistilBERT models and their capabilities"""
    if not model_manager:
        return {
            "available": False,
            "error": "Model manager not available",
            "models": {},
            "service": "distilbert-model-service"
        }
    
    try:
        models = model_manager.list_available_models()
        
        return {
            "available": True,
            "service": "distilbert-model-service",
            "model_type": "DistilBERT",
            "models": models,
            "loaded_models": list(model_manager.loaded_models.keys()),
            "default_model": model_manager.default_model,
            "cache_dir": model_manager.model_cache_dir,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@app.get("/models/{model_key}")
async def get_model_info(model_key: str):
    """Get detailed information about a specific DistilBERT model"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    try:
        model_info = model_manager.get_model_info(model_key)
        
        # Add runtime information if model is loaded
        if model_key in model_manager.loaded_models:
            loaded_info = model_manager.loaded_models[model_key]
            model_info.update({
                "status": "loaded",
                "loaded_at": loaded_info["loaded_at"].isoformat(),
                "load_time_seconds": round(loaded_info["load_time"], 2)
            })
        else:
            model_info["status"] = "available"
        
        return {
            "model_key": model_key,
            "info": model_info,
            "service": "distilbert-model-service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.post("/models/{model_key}/load")
async def load_model(model_key: str, background_tasks: BackgroundTasks):
    """Load a specific model into memory"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    try:
        if model_key in model_manager.loaded_models:
            return {
                "status": "already_loaded",
                "model_key": model_key,
                "message": f"Model {model_key} is already loaded",
                "service": "distilbert-model-service",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Load model in background for non-blocking response
        def load_model_task():
            try:
                model_manager.load_model(model_key)
                logger.info(f"Background model loading completed: {model_key}")
            except Exception as e:
                logger.error(f"Background model loading failed: {e}")
        
        background_tasks.add_task(load_model_task)
        
        return {
            "status": "loading",
            "model_key": model_key,
            "message": f"Model {model_key} is being loaded in background",
            "service": "distilbert-model-service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

@app.delete("/models/{model_key}/unload")
async def unload_model(model_key: str):
    """Unload a specific model from memory"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    try:
        model_manager.unload_model(model_key)
        
        return {
            "status": "success",
            "model_key": model_key,
            "message": f"Model {model_key} unloaded successfully",
            "service": "distilbert-model-service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error unloading model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unload model: {str(e)}")

@app.get("/metrics")
async def get_service_metrics():
    """Get service performance metrics and statistics"""
    uptime_seconds = (datetime.now(timezone.utc) - service_metrics["startup_time"]).total_seconds()
    
    total_predictions = service_metrics["successful_predictions"] + service_metrics["failed_predictions"]
    success_rate = (
        service_metrics["successful_predictions"] / total_predictions
        if total_predictions > 0 else 1.0
    )
    
    avg_processing_time = (
        service_metrics["total_processing_time"] / service_metrics["successful_predictions"]
        if service_metrics["successful_predictions"] > 0 else 0.0
    )
    
    metrics = {
        "service": "distilbert-model-service",
        "model_type": "DistilBERT",
        "uptime_seconds": round(uptime_seconds, 2),
        "requests_processed": service_metrics["requests_processed"],
        "predictions": {
            "successful": service_metrics["successful_predictions"],
            "failed": service_metrics["failed_predictions"],
            "total": total_predictions,
            "success_rate": round(success_rate, 4)
        },
        "performance": {
            "total_processing_time_ms": round(service_metrics["total_processing_time"], 2),
            "average_processing_time_ms": round(avg_processing_time, 2),
            "requests_per_second": round(service_metrics["requests_processed"] / uptime_seconds, 2) if uptime_seconds > 0 else 0
        },
        "model_manager_available": model_manager is not None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Add model manager metrics if available
    if model_manager:
        health_info = model_manager.get_health_status()
        metrics.update({
            "loaded_models": health_info["loaded_models"],
            "available_models": health_info["available_models"],
            "memory_usage": health_info["memory_usage"]
        })
    
    return metrics

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8081))
    
    logger.info(f"🚀 Starting DistilBERT Model Service on {host}:{port}")
    logger.info("🤖 Lightweight LLM service with /predict/llm and /predict/llm/batch endpoints")
    logger.info("📚 API documentation available at /docs")
    
    uvicorn.run(
        "model_services.distilbert_service:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
        access_log=True
    )
