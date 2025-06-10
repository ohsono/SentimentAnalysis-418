#!/usr/bin/env python3

"""
Fixed UCLA Sentiment Analysis Model Service
Robust sentiment analysis with VADER fallback and proper error handling
"""

import os
import sys
import time
import logging
import asyncio
import psutil
import argparse
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager

try:
    from .lightweight_model_manager import lightweight_model_manager
except ImportError:
    # Fallback for when running directly (not as module)
    from lightweight_model_manager import lightweight_model_manager

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import requests
try:
    from .pydantic_models import (
        PredictionRequest,
        PredictionResponse,
        ModelBatchRequest,
        HealthResponse,
        SentimentResponse,
        BatchSentimentResponse,
        ErrorResponse,
        ModelsResponse
    )
except ImportError:
    from pydantic_models import (
        PredictionRequest,
        PredictionResponse,
        ModelBatchRequest,
        HealthResponse,
        SentimentResponse,
        BatchSentimentResponse,
        ErrorResponse,
        ModelsResponse
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
startup_time: Optional[datetime] = None

# Check available dependencies
TORCH_AVAILABLE = False
HF_AVAILABLE = False
VADER_AVAILABLE = False

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    TORCH_AVAILABLE = True
    logger.info("✅ PyTorch and Transformers available")
except ImportError as e:
    logger.warning(f"❌ PyTorch/Transformers not available: {e}")

try:
    from huggingface_hub import snapshot_download
    HF_AVAILABLE = True
    logger.info("✅ HuggingFace Hub available")
except ImportError as e:
    logger.warning(f"❌ HuggingFace Hub not available: {e}")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    
    # Set NLTK data path
    nltk_data_paths = [
        './nltk_data',
        '/app/nltk_data', 
        os.path.expanduser('~/nltk_data'),
        '/usr/local/share/nltk_data'
    ]
    
    for path in nltk_data_paths:
        if os.path.exists(path):
            nltk.data.path.insert(0, path)
            logger.info(f"📁 Added NLTK data path: {path}")
    
    # Try to find VADER lexicon
    try:
        nltk.data.find('vader_lexicon')
        VADER_AVAILABLE = True
        logger.info("✅ NLTK VADER lexicon found")
    except LookupError:
        # Try to download VADER lexicon
        try:
            for path in nltk_data_paths:
                try:
                    os.makedirs(path, exist_ok=True)
                    nltk.download('vader_lexicon', download_dir=path, quiet=True)
                    VADER_AVAILABLE = True
                    logger.info(f"✅ NLTK VADER lexicon downloaded to {path}")
                    break
                except Exception as download_error:
                    logger.debug(f"Failed to download to {path}: {download_error}")
                    continue
        except Exception as e:
            logger.warning(f"Failed to download VADER lexicon: {e}")
            
except ImportError as e:
    logger.warning(f"❌ NLTK not available: {e}")

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

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

# class PredictionRequest(BaseModel):
#     text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
#     model_name: Optional[str] = Field(default=None, description="Model to use (auto-select if None)")
#     return_confidence: bool = Field(default=True, description="Include confidence scores")

# class PredictionResponse(BaseModel):
#     text: str
#     sentiment: str
#     confidence: Optional[float] = None
#     scores: Optional[Dict[str, float]] = None
#     model_used: str
#     processing_time_ms: float
#     timestamp: str

# class HealthResponse(BaseModel):
#     status: str
#     service: str
#     models_available: Dict[str, bool]
#     fallback_available: bool
#     timestamp: str
#     uptime_seconds: float
    
# class ErrorResponse(BaseModel):
#     error: str
#     detail: str
#     timestamp: str

# class BatchSentimentResponse(BaseModel):
#     results: List[PredictionResponse]
#     total_processed: int
#     total_processing_time: float
#     model_used: str

# class ModelsResponse(BaseModel):
#     models: List[Dict[str, Any]]
#     total_available: int
#     fallback_available: bool
#     recommended: Optional[str]
#     timestamp: str

# ============================================================================
# SENTIMENT ANALYZER CLASS
# ============================================================================

class RobustSentimentAnalyzer:
    """Robust sentiment analyzer with multiple fallback options"""
    
    def __init__(self):
        self.vader_analyzer = None
        self.hf_models = {}
        self.model_cache_dir = os.getenv('MODEL_CACHE_DIR', './model_cache')
        self.startup_time = datetime.now(timezone.utc)
        
        # Create cache directory
        Path(self.model_cache_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Model cache directory: {self.model_cache_dir}")
        
        # Initialize VADER
        self._init_vader()
        
        # Available models
        self.available_models = {
            "vader": {
                "name": "NLTK VADER",
                "available": VADER_AVAILABLE,
                "type": "rule-based",
                "description": "Fast rule-based sentiment analysis"
            },
            "distilbert-sentiment": {
                "name": "DistilBERT Sentiment",
                "available": TORCH_AVAILABLE and HF_AVAILABLE,
                "type": "transformer",
                "description": "Transformer-based sentiment analysis"
            }
        }
    
    def _init_vader(self):
        """Initialize VADER sentiment analyzer"""
        if not VADER_AVAILABLE:
            logger.warning("❌ VADER not available")
            return
            
        try:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("✅ VADER sentiment analyzer initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize VADER: {e}")
            self.vader_analyzer = None
    
    def predict_with_vader(self, text: str) -> Dict[str, Any]:
        """Predict sentiment using VADER"""
        if not self.vader_analyzer:
            raise Exception("VADER analyzer not available")
        
        start_time = time.time()
        
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            processing_time = (time.time() - start_time) * 1000
            
            # Determine sentiment from compound score
            compound = scores['compound']
            if compound >= 0.05:
                sentiment = 'positive'
                confidence = min(1.0, abs(compound) + 0.1)
            elif compound <= -0.05:
                sentiment = 'negative'
                confidence = min(1.0, abs(compound) + 0.1)
            else:
                sentiment = 'neutral'
                confidence = 1.0 - abs(compound)
            
            return {
                "sentiment": sentiment,
                "confidence": round(confidence, 4),
                "scores": {
                    "positive": scores['pos'],
                    "negative": scores['neg'],
                    "neutral": scores['neu']
                },
                "compound_score": compound,
                "model_used": "vader",
                "processing_time_ms": round(processing_time, 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"VADER prediction failed: {e}")
            raise
    
    def predict_with_transformers(self, text: str, model_name: str = "distilbert-sentiment") -> Dict[str, Any]:
        """Predict sentiment using HuggingFace transformers"""
        if not TORCH_AVAILABLE or not HF_AVAILABLE:
            raise Exception("PyTorch or HuggingFace not available")
        
        start_time = time.time()
        
        try:
            # Load model if not already loaded
            if model_name not in self.hf_models:
                self._load_hf_model(model_name)
            
            classifier = self.hf_models[model_name]
            results = classifier(text)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Process results
            if isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], list):
                    # Multiple scores returned
                    scores_list = results[0]
                else:
                    # Single result
                    scores_list = results
            else:
                scores_list = [results] if not isinstance(results, list) else results
            
            # Convert to standard format
            scores = {}
            max_score = 0
            predicted_sentiment = "neutral"
            
            for score_dict in scores_list:
                label = score_dict["label"].lower()
                score = score_dict["score"]
                
                # Map labels to standard format
                if label in ["positive", "pos", "label_1"]:
                    scores["positive"] = score
                    if score > max_score:
                        max_score = score
                        predicted_sentiment = "positive"
                elif label in ["negative", "neg", "label_0"]:
                    scores["negative"] = score
                    if score > max_score:
                        max_score = score
                        predicted_sentiment = "negative"
                else:
                    scores["neutral"] = score
                    if score > max_score:
                        max_score = score
                        predicted_sentiment = "neutral"
            
            # Ensure all categories exist
            for category in ["positive", "negative", "neutral"]:
                if category not in scores:
                    scores[category] = 0.0
            
            return {
                "sentiment": predicted_sentiment,
                "confidence": round(max_score, 4),
                "scores": scores,
                "compound_score": scores.get("positive", 0) - scores.get("negative", 0),
                "model_used": model_name,
                "processing_time_ms": round(processing_time, 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Transformer prediction failed: {e}")
            raise
    
    def _load_hf_model(self, model_name: str):
        """Load HuggingFace model"""
        model_mapping = {
            "distilbert-sentiment": "distilbert-base-uncased-finetuned-sst-2-english",
            "twitter-roberta": "cardiffnlp/twitter-roberta-base-sentiment-latest"
        }
        
        hf_model_id = model_mapping.get(model_name, model_name)
        
        try:
            logger.info(f"Loading HuggingFace model: {hf_model_id}")
            
            # Try to use cached model first
            model_cache_path = os.path.join(self.model_cache_dir, model_name)
            
            try:
                # Try loading from cache
                classifier = pipeline(
                    "sentiment-analysis",
                    model=hf_model_id,
                    cache_dir=model_cache_path,
                    local_files_only=True,
                    device=-1,  # CPU
                    return_all_scores=True
                )
                logger.info(f"✅ Loaded model from cache: {model_name}")
                
            except Exception as cache_error:
                logger.info(f"Cache miss, downloading model: {cache_error}")
                
                # Download model
                classifier = pipeline(
                    "sentiment-analysis",
                    model=hf_model_id,
                    cache_dir=model_cache_path,
                    device=-1,  # CPU
                    return_all_scores=True
                )
                logger.info(f"✅ Downloaded and loaded model: {model_name}")
            
            self.hf_models[model_name] = classifier
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise Exception(f"Failed to load model {model_name}: {e}")
    
    def predict(self, text: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Predict sentiment with intelligent fallback"""
        
        # Smart model selection
        if model_name is None:
            if TORCH_AVAILABLE and HF_AVAILABLE:
                model_name = "distilbert-sentiment"
            elif VADER_AVAILABLE:
                model_name = "vader"
            else:
                raise Exception("No sentiment analysis models available")
        
        # Try requested model first
        try:
            if model_name == "vader":
                return self.predict_with_vader(text)
            else:
                return self.predict_with_transformers(text, model_name)
                
        except Exception as primary_error:
            logger.warning(f"Primary model {model_name} failed: {primary_error}")
            
            # Fallback to VADER
            if VADER_AVAILABLE and model_name != "vader":
                logger.info("Falling back to VADER")
                try:
                    result = self.predict_with_vader(text)
                    result["fallback_used"] = True
                    result["primary_error"] = str(primary_error)
                    return result
                except Exception as fallback_error:
                    logger.error(f"VADER fallback also failed: {fallback_error}")
            
            # No fallback available
            raise Exception(f"Prediction failed for model {model_name} and VADER not available: {primary_error}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status"""
        uptime = (datetime.now(timezone.utc) - self.startup_time).total_seconds()
        
        return {
            "models_available": {
                name: info["available"] 
                for name, info in self.available_models.items()
            },
            "fallback_available": VADER_AVAILABLE,
            "torch_available": TORCH_AVAILABLE,
            "hf_available": HF_AVAILABLE,
            "vader_available": VADER_AVAILABLE,
            "loaded_models": list(self.hf_models.keys()),
            "cache_dir": self.model_cache_dir,
            "uptime_seconds": uptime
        }

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Global analyzer instance
analyzer = RobustSentimentAnalyzer()


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


app = FastAPI(
    title="UCLA Sentiment Analysis - Fixed Model Service",
    description="Robust sentiment analysis with VADER fallback",
    version="2.0.0",
    docs_url="/docs"
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
#    health = analyzer.get_health_status()
    # return {
    #     "service": "UCLA Sentiment Analysis - Fixed Model Service",
    #     "version": "2.0.0",
    #     "status": "healthy",
    #     "description": "Robust sentiment analysis with intelligent fallback",
    #     "models_available": health["models_available"],
    #     "fallback_available": health["fallback_available"],
    #     "uptime_seconds": health["uptime_seconds"],
    #     "endpoints": {
    #         "predict": "POST /predict - Sentiment prediction",
    #         "health": "GET /health - Service health check",
    #         "models": "GET /models - List available models"
    #     },
    #     "timestamp": datetime.now(timezone.utc).isoformat()
    # }

    health_status = await lightweight_model_manager.get_health_status() 

    return {
        "message": "🤖 UCLA Sentiment Analysis Lightweight Model Service",
        "status": "healthy" if health_status["initialized"] else "degraded",
        "version": "2.2.0",
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
            service="Fixed Lightweight Model Service",
            timestamp=get_current_time(),
            manager_available=manager_health["initialized"],
            memory_info=memory_info,
            uptime=get_uptime_string()
            # models_available=health["models_available"],
            # fallback_available=health["fallback_available"],
            # timestamp=datetime.now(timezone.utc).isoformat(),
            # uptime_seconds=health["uptime_seconds"]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/predict", response_model=PredictionResponse)
async def predict_sentiment(request: PredictionRequest):
    """Single prediction endpoint using model manager with smart fallback"""
    try:
        logger.info(f"Prediction request: model={request.model_name}, text_length={len(request.text)}")
        
        # result = analyzer.predict(request.text, request.model_name)

        # Use model manager for prediction with smart model selection
        result = await lightweight_model_manager.predict_sentiment_async(
            text=request.text,
            model_key=request.model_name  # Can be None for auto-selection
        )

        # Format response
        response_data = {
            "text": request.text,
            "sentiment": result["sentiment"],
            "confidence": result["confidence"] if request.return_confidence else None,
            "scores": result["scores"] if request.return_confidence else None,
            "model_used": result["model_used"],
            "processing_time_ms": result["processing_time_ms"],
            "timestamp": result["timestamp"]
        }
        
        logger.info(f"Prediction successful: {result['sentiment']} (conf: {result['confidence']:.3f})")
        return PredictionResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Prediction failed: {str(e)}"
        )

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

@app.get("/models")
async def list_models():
    """List available models"""
    try:
        models_data = await lightweight_model_manager.list_available_models_async()
        
        models = []
        #for name, info in analyzer.available_models.items():
        for key, info in models_data["available_models"].items():
            # model_info = {
            #     "name": name,
            #     "display_name": info["name"],
            #     "type": info["type"],
            #     "available": info["available"],
            #     "description": info["description"],
            #     "loaded": name in analyzer.hf_models or (name == "vader" and VADER_AVAILABLE)
            # }
            model_info = {
                "name": key,
                "type": info["type"],
                "loaded": info["status"] == "loaded",
                "size_mb": info.get("memory_mb"),
                "last_used": info.get("loaded_at") if info["status"] == "loaded" else None
            }

            models.append(model_info)
        
        # return {
        #     "models": models,
        #     "total_available": sum(1 for m in models if m["available"]),
        #     "fallback_available": health["fallback_available"],
        #     "recommended": "vader" if VADER_AVAILABLE else None,
        #     "timestamp": datetime.now(timezone.utc).isoformat()
        # }
        return ModelsResponse(
            available_models=model_list,
            current_model=models_data.get("recommended_model"),
            total_models=models_data["total_models"]
        )

    except Exception as e:
        logger.error(f"List models failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@app.post("/models/{model_name}/download")
async def download_model(model_name: str, background_tasks: BackgroundTasks):
    """Download a model in the background"""
    if model_name == "vader":
        return {"message": "VADER doesn't require downloading", "status": "available"}
    
    if not TORCH_AVAILABLE or not HF_AVAILABLE:
        raise HTTPException(
            status_code=400, 
            detail="PyTorch/HuggingFace not available for model downloading"
        )
    
    def download_task():
        try:
            analyzer._load_hf_model(model_name)
            logger.info(f"Background download completed: {model_name}")
        except Exception as e:
            logger.error(f"Background download failed: {e}")
    
    background_tasks.add_task(download_task)
    
    return {
        "message": f"Model {model_name} download started",
        "status": "downloading",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

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

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description="UCLA Sentiment Analysis - Fixed Model Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting UCLA Sentiment Analysis - Fixed Model Service")
    logger.info(f"📡 Server: {args.host}:{args.port}")
    logger.info(f"🤖 Models available: {analyzer.available_models}")
    logger.info(f"🔄 VADER fallback: {'✅' if VADER_AVAILABLE else '❌'}")
    logger.info(f"🔄 PyTorch available: {'✅' if TORCH_AVAILABLE else '❌'}")
    logger.info(f"📚 API docs: http://{args.host}:{args.port}/docs")
    
    # Test VADER if available
    if VADER_AVAILABLE:
        try:
            test_result = analyzer.predict_with_vader("This is a test message")
            logger.info(f"✅ VADER test successful: {test_result['sentiment']}")
        except Exception as e:
            logger.warning(f"⚠️ VADER test failed: {e}")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level.lower()
    )

if __name__ == "__main__":
    main()
