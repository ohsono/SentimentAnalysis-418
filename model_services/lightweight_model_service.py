#!/usr/bin/env python3

import logging
import argparse
import psutil
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the enhanced model manager
from lightweight_model_manager import lightweight_model_manager

# Import your pydantic models
from pydantic_models import (
    ModelPredictionRequest, 
    ModelBatchRequest,
    HealthResponse,
    SentimentResponse,
    BatchSentimentResponse,
    ErrorResponse,
    ModelsResponse,
    ModelDownloadRequest,
    ModelDownloadResponse,
    ModelInfoResponse,
    MetricsResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
startup_time: Optional[datetime] = None

# Fix: Use modern datetime with timezone
def get_current_time():
    """Get current UTC time using modern datetime API"""
    return datetime.now(timezone.utc)

def get_uptime_string():
    """Calculate uptime string"""
    if startup_time is None:
        return "Unknown"
    
    uptime_seconds = (get_current_time() - startup_time).total_seconds()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    return f"{hours}h {minutes}m {seconds}s"

# Enhanced lifespan with model manager integration
@asynccontextmanager
async def lifespan(app: FastAPI):
    global startup_time
    
    # Startup
    logger.info("🤖 UCLA Sentiment Analysis Lightweight Model Service starting...")
    startup_time = get_current_time()
    
    # Initialize model manager
    try:
        await lightweight_model_manager.initialize()
        logger.info("✅ Model manager initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize model manager: {e}")
    
    logger.info("🔄 Service ready for model swapping and inference")
    
    yield
    
    # Shutdown
    logger.info("🛑 Lightweight Model Service shutting down...")
    try:
        await lightweight_model_manager.cleanup()
    except Exception as e:
        logger.warning(f"Error during cleanup: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="UCLA Sentiment Analysis Lightweight Model Service",
    description="🚀 Designed for easy model swapping and isolated inference with HuggingFace integration",
    version="1.0.0",
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

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    health_status = await lightweight_model_manager.get_health_status()
    
    return {
        "message": "🤖 UCLA Sentiment Analysis Lightweight Model Service",
        "status": "healthy" if health_status["initialized"] else "degraded",
        "version": "1.0.0",
        "uptime": get_uptime_string(),
        "timestamp": get_current_time().isoformat(),
        "model_manager": {
            "available": health_status["torch_available"],
            "models_loaded": health_status["models_loaded"],
            "models_available": health_status["models_available"]
        },
        "endpoints": {
            "health": "GET /health - Service health check",
            "predict": "POST /predict - Single text prediction", 
            "predict_batch": "POST /predict/batch - Batch predictions",
            "models": "GET /models - List available models",
            "models_download": "POST /models/download - Download model",
            "models_info": "GET /models/{model_key} - Get model details",
            "metrics": "GET /metrics - Service performance metrics"
        },
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Get memory info
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_percent": memory.percent,
            "free_gb": round((memory.total - memory.used) / (1024**3), 2)
        }
        
        # Get model manager health status
        manager_health = await lightweight_model_manager.get_health_status()
        
        status = "healthy" if manager_health["initialized"] else "degraded"
        
        return HealthResponse(
            status=status,
            service_name="Lightweight Model Service",
            timestamp=get_current_time(),
            manager_available=manager_health["initialized"],
            memory_info=memory_info,
            uptime=get_uptime_string()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/predict", response_model=SentimentResponse)
async def predict(request: ModelPredictionRequest):
    """Single prediction endpoint using model manager with smart fallback"""
    try:
        # Use model manager for prediction with smart model selection
        result = await lightweight_model_manager.predict_sentiment_async(
            text=request.text,
            model_key=request.model_name  # Can be None for auto-selection
        )
        
        # Convert to response format
        response_data = {
            "text": request.text,
            "sentiment": result["sentiment"],
            "confidence": result["confidence"] if request.return_confidence else None,
            "scores": result["probabilities"] if request.return_confidence else None,
            "model_used": result["model_used"],
            "processing_time": result["processing_time_ms"] / 1000  # Convert to seconds
        }
        
        return SentimentResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict/batch", response_model=BatchSentimentResponse)
async def predict_batch(request: ModelBatchRequest):
    """Batch prediction endpoint using model manager with smart fallback"""
    try:
        start_time = get_current_time()
        results = []
        
        # Process each text using model manager with smart selection
        for text in request.texts:
            result = await lightweight_model_manager.predict_sentiment_async(
                text=text,
                model_key=request.model_name  # Can be None for auto-selection
            )
            
            response_data = SentimentResponse(
                text=text,
                sentiment=result["sentiment"],
                confidence=result["confidence"] if request.return_confidence else None,
                scores=result["probabilities"] if request.return_confidence else None,
                model_used=result["model_used"],
                processing_time=result["processing_time_ms"] / 1000
            )
            results.append(response_data)
        
        total_time = (get_current_time() - start_time).total_seconds()
        
        # Use the model from the first prediction for reporting
        model_used = results[0].model_used if results else "unknown"
        
        return BatchSentimentResponse(
            results=results,
            total_processed=len(results),
            total_processing_time=total_time,
            model_used=model_used
        )
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/models", response_model=ModelsResponse)
async def get_models():
    """Get available models from model manager"""
    try:
        models_data = await lightweight_model_manager.list_available_models_async()
        
        # Convert to response format
        model_list = []
        for key, info in models_data["available_models"].items():
            model_info = {
                "name": key,
                "type": info["type"],
                "loaded": info["status"] == "loaded",
                "size_mb": info.get("memory_mb"),
                "last_used": info.get("loaded_at") if info["status"] == "loaded" else None
            }
            model_list.append(model_info)
        
        return ModelsResponse(
            available_models=model_list,
            current_model=models_data.get("recommended_model"),
            total_models=models_data["total_models"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.post("/models/download", response_model=ModelDownloadResponse)
async def download_model_post(request: ModelDownloadRequest):
    """Download model using model manager"""
    try:
        # Use model manager to download from HuggingFace
        result = await lightweight_model_manager.download_from_huggingface(
            model_key=request.model_name,
            force_download=request.force_download
        )
        
        return ModelDownloadResponse(
            message=f"Model {request.model_name} downloaded successfully",
            model_name=request.model_name,
            status="downloaded",
            download_size_mb=result.get("size_mb"),
            estimated_time_minutes=None,  # Could add estimation logic
            timestamp=get_current_time()
        )
        
    except Exception as e:
        logger.error(f"Model download failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model download failed: {str(e)}")

@app.get("/models/{model_key}", response_model=ModelInfoResponse)
async def get_model_info(model_key: str):
    """Get detailed information about a specific model from model manager"""
    try:
        model_info = await lightweight_model_manager.get_model_info_async(model_key)
        
        # Convert to response format
        return ModelInfoResponse(
            model_key=model_key,
            name=model_info["name"],
            type=model_info["type"],
            architecture=model_info.get("hf_model_id"),
            loaded=model_info["status"] == "loaded",
            size_mb=model_info.get("memory_mb"),
            parameters=None,  # Could extract from HF info
            accuracy=None,  # Could add if available
            last_used=model_info.get("loaded_at"),
            created_date=None,
            version="1.0.0",
            description=model_info["description"],
            supported_languages=model_info.get("languages"),
            labels=["positive", "negative", "neutral"],  # Standard sentiment labels
            performance_metrics=None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get model info for {model_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get comprehensive service metrics"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get process-specific metrics
        import os
        current_process = psutil.Process(os.getpid())
        process_memory = current_process.memory_info()
        
        # Get model manager metrics
        manager_health = await lightweight_model_manager.get_health_status()
        
        return MetricsResponse(
            service={
                "uptime": get_uptime_string(),
                "status": "healthy" if manager_health["initialized"] else "degraded",
                "manager_available": manager_health["initialized"],
                "timestamp": get_current_time().isoformat()
            },
            system={
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                    "free_gb": round((memory.total - memory.used) / (1024**3), 2)
                },
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count()
                }
            },
            process={
                "memory": {
                    "rss_mb": round(process_memory.rss / (1024**2), 2),
                    "vms_mb": round(process_memory.vms / (1024**2), 2)
                },
                "cpu_percent": current_process.cpu_percent(),
                "threads": current_process.num_threads(),
                "pid": os.getpid()
            },
            models={
                "loaded_count": manager_health["models_loaded"],
                "available_count": manager_health["models_available"],
                "current_model": None  # Could track current/default model
            },
            requests={
                "total_predictions": manager_health["total_predictions"],
                "total_batch_predictions": 0,  # Could track separately
                "average_response_time_ms": manager_health["avg_prediction_time_ms"],
                "error_rate": 0.0  # Could track error rate
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description="UCLA Sentiment Analysis Lightweight Model Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting Enhanced Lightweight Model Service on {args.host}:{args.port}")
    logger.info("🔄 Designed for easy model swapping and HuggingFace integration")
    logger.info("📚 API documentation available at /docs")
    
    uvicorn.run(
        app, 
        host=args.host, 
        port=args.port, 
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()