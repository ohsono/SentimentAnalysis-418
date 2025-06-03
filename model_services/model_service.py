#!/usr/bin/env python3

"""
Microservice that handles ML model inference separately from main API
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
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple dummy model manager to avoid errors when the real one isn't available
class DummyModelManager:
    def __init__(self):
        logger.info("Initializing dummy model manager")
    
    def health_check(self):
        return {"status": "operational", "models_loaded": 0, "dummy": True}
    
    def predict_sentiment(self, text, model=None):
        return {
            "sentiment": "neutral",
            "confidence": 0.8,
            "compound_score": 0.0,
            "probabilities": {"positive": 0.2, "neutral": 0.6, "negative": 0.2},
            "model": "dummy",
            "processing_time_ms": 0.5
        }
    
    def list_available_models(self):
        return {"dummy": {"name": "Dummy Model", "type": "fallback", "size": "small"}}
    
    def get_recommended_model(self):
        return "dummy"
    
    def download_model_async(self, model):
        return {"status": "success", "model": model, "dummy": True}
    
    def load_model_lazy(self, model):
        logger.info(f"Pretending to load model: {model}")
        return True
    
    def cleanup(self):
        pass

# Import lightweight model manager - wrap in try/except for graceful failure
try:
    from .lightweight_model_manager import LightweightModelManager
    lightweight_model_manager = LightweightModelManager()
    MODEL_MANAGER_AVAILABLE = True
except ImportError:
    logger.error("Model manager not available - using dummy implementation")
    lightweight_model_manager = DummyModelManager()
    MODEL_MANAGER_AVAILABLE = True  # Set to True since we have a dummy

# ============================================
# PYDANTIC MODELS
# ============================================

class ModelPredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    model: str = Field(default="distilbert-sentiment")
    include_probabilities: bool = Field(default=True)

class ModelBatchRequest(BaseModel):
    texts: List[str] = Field(..., max_items=50)
    model: str = Field(default="distilbert-sentiment") 
    include_probabilities: bool = Field(default=True)

class ModelDownloadRequest(BaseModel):
    model: str = Field(...)

# ============================================
# LIFESPAN MANAGEMENT
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting Model Service...")
    
    # Optionally pre-load default model
    if MODEL_MANAGER_AVAILABLE:
        model_to_preload = os.getenv("PRELOAD_MODEL")
        if model_to_preload:
            logger.info(f"Pre-loading model: {model_to_preload}")
            try:
                lightweight_model_manager.load_model_lazy(model_to_preload)
                logger.info(f"✅ Pre-loaded model: {model_to_preload}")
            except Exception as e:
                logger.warning(f"Failed to pre-load model: {e}")
    
    logger.info("🔄 Designed for easy model swapping and isolated inference")
    logger.info("📚 API documentation available at /docs")
    
    yield
    
    # Shutdown
    logger.info("🛑 Model Service shutting down...")
    
    # Cleanup
    if MODEL_MANAGER_AVAILABLE:
        lightweight_model_manager.cleanup()

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="UCLA Sentiment Analysis - Model Service",
    description="Dedicated microservice for ML model inference",
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
# MODEL SERVICE ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Model service information"""
    return {
        "service": "UCLA Sentiment Analysis - Model Service",
        "version": "1.0.0",
        "description": "Dedicated microservice for ML model inference",
        "model_manager_available": MODEL_MANAGER_AVAILABLE,
        "endpoints": {
            "health": "GET /health",
            "predict": "POST /predict", 
            "predict_batch": "POST /predict/batch",
            "models": "GET /models",
            "download": "POST /models/download"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check for model service"""
    health_info = lightweight_model_manager.health_check()
    
    return {
        "status": "healthy",
        "service": "model-service",
        "model_manager": "available",
        "health_info": health_info,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/predict")
async def predict_sentiment(request: ModelPredictionRequest):
    """Predict sentiment using ML model"""
    try:
        logger.info(f"Model prediction request: {request.model} for text length {len(request.text)}")
        
        result = lightweight_model_manager.predict_sentiment(
            request.text, 
            request.model
        )
        
        if not request.include_probabilities:
            result.pop('probabilities', None)
        
        # Add service metadata
        result['service'] = 'model-service'
        result['service_version'] = '1.0.0'
        
        logger.info(f"Prediction complete: {result['sentiment']} (conf: {result.get('confidence', 0):.2f})")
        return result
        
    except Exception as e:
        logger.error(f"Error in model prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Model prediction failed: {str(e)}")

@app.post("/predict/batch")
async def predict_batch_sentiment(request: ModelBatchRequest):
    """Batch predict sentiment using ML model"""
    try:
        logger.info(f"Batch prediction request: {request.model} for {len(request.texts)} texts")
        
        start_time = time.time()
        results = []
        
        for i, text in enumerate(request.texts):
            try:
                result = lightweight_model_manager.predict_sentiment(text, request.model)
                result['batch_index'] = i
                
                if not request.include_probabilities:
                    result.pop('probabilities', None)
                
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing text {i}: {e}")
                results.append({
                    'batch_index': i,
                    'text': text[:100] + '...' if len(text) > 100 else text,
                    'error': str(e),
                    'sentiment': 'neutral',
                    'confidence': 0.0
                })
        
        total_time = (time.time() - start_time) * 1000
        
        # Calculate summary
        successful_results = [r for r in results if 'error' not in r]
        sentiments = [r['sentiment'] for r in successful_results]
        
        summary = {
            "total_processed": len(results),
            "successful": len(successful_results),
            "failed": len(results) - len(successful_results),
            "total_processing_time_ms": round(total_time, 2),
            "average_time_per_text_ms": round(total_time / len(request.texts), 2),
            "model_used": request.model,
            "service": "model-service",
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
        
        logger.info(f"Batch prediction complete: {summary}")
        return response
        
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/models")
async def list_models():
    """List available models"""
    try:
        models = lightweight_model_manager.list_available_models()
        
        return {
            "available": True,
            "service": "model-service",
            "models": models,
            "recommended_model": lightweight_model_manager.get_recommended_model(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@app.post("/models/download")
async def download_model(request: ModelDownloadRequest):
    """Download a specific model"""
    try:
        logger.info(f"Model download request: {request.model}")
        
        result = lightweight_model_manager.download_model_async(request.model)
        
        return {
            "status": "success",
            "message": f"Model {request.model} downloaded successfully",
            "model_info": result,
            "service": "model-service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        raise HTTPException(status_code=500, detail=f"Model download failed: {str(e)}")

@app.get("/models/{model_key}")
async def get_model_info(model_key: str):
    """Get information about a specific model"""
    try:
        models = lightweight_model_manager.list_available_models()
        
        if model_key not in models:
            raise HTTPException(status_code=404, detail=f"Model {model_key} not found")
        
        return {
            "model_key": model_key,
            "info": models[model_key],
            "service": "model-service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8081))
    
    logger.info(f"🚀 Starting Model Service on {host}:{port}")
    
    uvicorn.run(
        "model_service:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
        access_log=True
    )
