#!/usr/bin/env python3

"""
Lightweight Model Service - Swappable LLM Inference Microservice
Dedicated service for ML model inference, separate from main API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import os
import time
import uvicorn
import asyncio
from .pydantic_models import ModelPredictionRequest, ModelBatchRequest
from .pydantic_models import ModelDownloadRequest, HealthResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import model manager (fallback gracefully if not available)
try:
    from models.ml.lightweight_model_manager import LightweightModelManager
    MODEL_MANAGER_AVAILABLE = True
    model_manager = LightweightModelManager()
except ImportError:
    MODEL_MANAGER_AVAILABLE = False
    model_manager = None
    logger.warning("Model manager not available - service will return errors")

# ============================================
# FASTAPI APP
# ============================================
app = FastAPI(
    title="UCLA Sentiment Analysis - Lightweight Model Service",
    description="Swappable microservice for ML model inference - designed for easy model replacement",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service metrics
service_metrics = {
    "requests_processed": 0,
    "successful_predictions": 0,
    "failed_predictions": 0,
    "total_processing_time": 0.0,
    "startup_time": datetime.now(timezone.utc)
}

# ============================================
# MODEL SERVICE ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Model service information and capabilities"""
    return {
        "service": "UCLA Sentiment Analysis - Lightweight Model Service",
        "version": "1.0.0",
        "description": "Swappable microservice for ML model inference",
        "model_manager_available": MODEL_MANAGER_AVAILABLE,
        "architecture": "microservice",
        "purpose": "Isolated LLM inference to enable easy model swapping",
        "endpoints": {
            "health": "GET /health - Service health check",
            "predict": "POST /predict - Single text prediction", 
            "predict_batch": "POST /predict/batch - Batch predictions",
            "models": "GET /models - List available models",
            "models_download": "POST /models/download - Download model",
            "models_info": "GET /models/{model_key} - Get model details",
            "metrics": "GET /metrics - Service performance metrics"
        },
        "features": [
            "Isolated model inference",
            "Hot-swappable model architecture", 
            "Batch processing support",
            "Health monitoring",
            "Performance metrics",
            "Graceful error handling"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check for model service"""
    if not MODEL_MANAGER_AVAILABLE:
        return HealthResponse(
            status="degraded",
            service="model-service",
            model_manager_available=False,
            loaded_models=[],
            recommended_model="none",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    try:
        # Get model manager health info
        health_info = await model_manager.get_health_status()
        loaded_models = list(model_manager.get_loaded_models().keys()) if hasattr(model_manager, 'get_loaded_models') else []
        
        return HealthResponse(
            status="healthy",
            service="model-service",
            model_manager_available=True,
            loaded_models=loaded_models,
            recommended_model=model_manager.get_recommended_model() if hasattr(model_manager, 'get_recommended_model') else "distilbert-sentiment",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="model-service",
            model_manager_available=False,
            loaded_models=[],
            recommended_model="none",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

@app.post("/predict")
async def predict_sentiment(request: ModelPredictionRequest):
    """
    Predict sentiment using specified ML model
    
    This endpoint provides isolated model inference that can be easily swapped
    or replaced without affecting the main API service.
    """
    if not MODEL_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Model manager not available in this service instance"
        )
    
    start_time = time.time()
    service_metrics["requests_processed"] += 1
    
    try:
        logger.info(f"Model prediction request: {request.model} for text length {len(request.text)}")
        
        # Use model manager for prediction
        result = await model_manager.predict_sentiment_async(
            request.text, 
            request.model
        )
        
        # Remove probabilities if not requested
        if not request.include_probabilities:
            result.pop('probabilities', None)
        
        # Add service metadata
        processing_time = (time.time() - start_time) * 1000
        result.update({
            'service': 'lightweight-model-service',
            'service_version': '1.0.0',
            'processing_time_ms': round(processing_time, 2),
            'model_service_used': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # Update metrics
        service_metrics["successful_predictions"] += 1
        service_metrics["total_processing_time"] += processing_time
        
        logger.info(f"Prediction complete: {result['sentiment']} (conf: {result['confidence']:.2f}, {processing_time:.2f}ms)")
        return result
        
    except Exception as e:
        service_metrics["failed_predictions"] += 1
        logger.error(f"Error in model prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Model prediction failed: {str(e)}")

@app.post("/predict/batch")
async def predict_batch_sentiment(request: ModelBatchRequest):
    """
    Batch predict sentiment using specified ML model
    
    Processes multiple texts efficiently in a single request.
    """
    if not MODEL_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Model manager not available in this service instance"
        )
    
    start_time = time.time()
    service_metrics["requests_processed"] += 1
    
    try:
        logger.info(f"Batch prediction request: {request.model} for {len(request.texts)} texts")
        
        # Validate batch size
        if len(request.texts) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 texts allowed per batch")
        
        results = []
        successful_predictions = 0
        
        # Process each text
        for i, text in enumerate(request.texts):
            try:
                result = await model_manager.predict_sentiment_async(text, request.model)
                result['batch_index'] = i
                
                if not request.include_probabilities:
                    result.pop('probabilities', None)
                
                results.append(result)
                successful_predictions += 1
                
            except Exception as e:
                logger.error(f"Error processing text {i}: {e}")
                results.append({
                    'batch_index': i,
                    'text': text[:100] + '...' if len(text) > 100 else text,
                    'error': str(e),
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'model_used': request.model
                })
        
        total_time = (time.time() - start_time) * 1000
        
        # Calculate summary
        sentiments = [r['sentiment'] for r in results if 'error' not in r]
        
        summary = {
            "total_processed": len(results),
            "successful": successful_predictions,
            "failed": len(results) - successful_predictions,
            "total_processing_time_ms": round(total_time, 2),
            "average_time_per_text_ms": round(total_time / len(request.texts), 2),
            "model_used": request.model,
            "service": "lightweight-model-service",
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
        
        # Update metrics
        service_metrics["successful_predictions"] += successful_predictions
        service_metrics["failed_predictions"] += (len(results) - successful_predictions)
        service_metrics["total_processing_time"] += total_time
        
        logger.info(f"Batch prediction complete: {summary}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        service_metrics["failed_predictions"] += 1
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/models")
async def list_models():
    """List available models and their capabilities"""
    if not MODEL_MANAGER_AVAILABLE:
        return {
            "available": False,
            "error": "Model manager not available",
            "models": {},
            "service": "lightweight-model-service"
        }
    
    try:
        models = await model_manager.list_available_models_async()
        loaded_models = model_manager.get_loaded_models() if hasattr(model_manager, 'get_loaded_models') else {}
        
        return {
            "available": True,
            "service": "lightweight-model-service",
            "models": models,
            "loaded_models": list(loaded_models.keys()),
            "recommended_model": model_manager.get_recommended_model() if hasattr(model_manager, 'get_recommended_model') else "distilbert-sentiment",
            "swappable": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@app.post("/models/download")
async def download_model(request: ModelDownloadRequest):
    """Download and cache a specific model for future use"""
    if not MODEL_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Model manager not available in this service instance"
        )
    
    try:
        logger.info(f"Model download request: {request.model}")
        
        # Download and cache the model
        result = await model_manager.download_model_async(request.model)
        
        return {
            "status": "success",
            "message": f"Model {request.model} downloaded and cached successfully",
            "model_info": result,
            "service": "lightweight-model-service",
            "cached": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        raise HTTPException(status_code=500, detail=f"Model download failed: {str(e)}")

@app.get("/models/{model_key}")
async def get_model_info(model_key: str):
    """Get detailed information about a specific model"""
    if not MODEL_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    try:
        models = await model_manager.list_available_models_async()
        
        if model_key not in models:
            raise HTTPException(status_code=404, detail=f"Model {model_key} not found")
        
        model_info = models[model_key]
        
        # Add runtime information if model is loaded
        loaded_models = model_manager.get_loaded_models() if hasattr(model_manager, 'get_loaded_models') else {}
        if model_key in loaded_models:
            model_info["status"] = "loaded"
            model_info["memory_usage"] = "estimated"  # Could add actual memory usage
        else:
            model_info["status"] = "available"
        
        return {
            "model_key": model_key,
            "info": model_info,
            "service": "lightweight-model-service",
            "swappable": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

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
    
    return {
        "service": "lightweight-model-service",
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
        "model_manager_available": MODEL_MANAGER_AVAILABLE,
        "loaded_models": list(model_manager.get_loaded_models().keys()) if MODEL_MANAGER_AVAILABLE and hasattr(model_manager, 'get_loaded_models') else [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ============================================
# SERVICE MANAGEMENT ENDPOINTS
# ============================================

@app.post("/service/reload")
async def reload_model_manager():
    """Reload the model manager (for hot-swapping models)"""
    if not MODEL_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    try:
        logger.info("Reloading model manager...")
        
        # Clear loaded models and reinitialize
        if hasattr(model_manager, 'clear_cache'):
            await model_manager.clear_cache()
        
        if hasattr(model_manager, 'initialize'):
            await model_manager.initialize()
        
        return {
            "status": "success",
            "message": "Model manager reloaded successfully",
            "service": "lightweight-model-service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error reloading model manager: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload model manager: {str(e)}")

@app.post("/service/clear-cache")
async def clear_model_cache():
    """Clear all cached models to free memory"""
    if not MODEL_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    try:
        logger.info("Clearing model cache...")
        
        if hasattr(model_manager, 'clear_cache'):
            await model_manager.clear_cache()
        
        return {
            "status": "success",
            "message": "Model cache cleared successfully",
            "service": "lightweight-model-service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

# ============================================
# STARTUP/SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Model service startup tasks"""
    logger.info("🤖 UCLA Sentiment Analysis Lightweight Model Service starting...")
    
    if MODEL_MANAGER_AVAILABLE:
        logger.info("✅ Model manager available")
        
        # Initialize model manager
        try:
            if hasattr(model_manager, 'initialize'):
                await model_manager.initialize()
            logger.info("✅ Model manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize model manager: {e}")
        
        # Optionally pre-load default model
        preload_model = os.getenv("PRELOAD_MODEL", "distilbert-sentiment")
        if preload_model and hasattr(model_manager, 'load_model'):
            logger.info(f"Pre-loading model: {preload_model}")
            try:
                await model_manager.load_model(preload_model)
                logger.info(f"✅ Pre-loaded model: {preload_model}")
            except Exception as e:
                logger.warning(f"Failed to pre-load model: {e}")
    else:
        logger.warning("⚠️  Model manager not available - service will return errors")
    
    logger.info("🔄 Service ready for model swapping and inference")

@app.on_event("shutdown")
async def shutdown_event():
    """Model service shutdown tasks"""
    logger.info("🛑 Lightweight Model Service shutting down...")
    
    if MODEL_MANAGER_AVAILABLE and hasattr(model_manager, 'cleanup'):
        try:
            await model_manager.cleanup()
            logger.info("✅ Model manager cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8081))
    
    logger.info(f"🚀 Starting Lightweight Model Service on {host}:{port}")
    logger.info("🔄 Designed for easy model swapping and isolated inference")
    logger.info("📚 API documentation available at /docs")
    
    uvicorn.run(
        "lightweight_model_service:app",
        host=host,
        port=port,
        reload=False,  # Disable reload in production for stability
        log_level="info",
        access_log=True
    )
