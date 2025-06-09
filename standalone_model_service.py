#!/usr/bin/env python3

"""
Standalone UCLA Sentiment Analysis Model Service
Fixed version with VADER fallback and proper error handling
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    model_name: Optional[str] = Field(default=None, description="Model to use (auto-select if None)")
    return_confidence: bool = Field(default=True, description="Include confidence scores")

class PredictionResponse(BaseModel):
    text: str
    sentiment: str
    confidence: Optional[float] = None
    scores: Optional[Dict[str, float]] = None
    model_used: str
    processing_time_ms: float
    timestamp: str

class BatchSentimentResponse(BaseModel):
    results: List[PredictionResponse]
    total_processed: int
    total_processing_time: float
    model_used: str

class HealthResponse(BaseModel):
    status: str
    service: str
    models_available: Dict[str, bool]
    fallback_available: bool
    timestamp: str
    uptime_seconds: float

class ModelsResponse(BaseModel):
    models: List[Dict[str, Any]]
    total_available: int
    fallback_available: bool
    recommended: Optional[str]
    timestamp: str
    
class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str

# ============================================================================
# SENTIMENT ANALYZER CLASS
# ============================================================================

class StandaloneSentimentAnalyzer:
    """Standalone sentiment analyzer with VADER fallback"""
    
    def __init__(self):
        self.vader_analyzer = None
        self.startup_time = datetime.now(timezone.utc)
        
        # Initialize VADER
        self._init_vader()
        
        # Available models
        self.available_models = {
            "vader": {
                "name": "NLTK VADER",
                "available": VADER_AVAILABLE,
                "type": "rule-based",
                "description": "Fast rule-based sentiment analysis"
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
    
    def predict(self, text: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Predict sentiment with fallback"""
        
        # For now, only VADER is available
        if not VADER_AVAILABLE:
            raise Exception("No sentiment analysis models available")
        
        return self.predict_with_vader(text)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status"""
        uptime = (datetime.now(timezone.utc) - self.startup_time).total_seconds()
        
        return {
            "models_available": {
                name: info["available"] 
                for name, info in self.available_models.items()
            },
            "fallback_available": VADER_AVAILABLE,
            "vader_available": VADER_AVAILABLE,
            "uptime_seconds": uptime
        }

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Global analyzer instance
analyzer = StandaloneSentimentAnalyzer()

app = FastAPI(
    title="UCLA Sentiment Analysis - Standalone Model Service",
    description="Standalone sentiment analysis with VADER",
    version="2.1.0",
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
    """Root endpoint"""
    health = analyzer.get_health_status()
    
    return {
        "service": "UCLA Sentiment Analysis - Standalone Model Service",
        "version": "2.1.0",
        "status": "healthy",
        "description": "Standalone sentiment analysis service with VADER",
        "models_available": health["models_available"],
        "fallback_available": health["fallback_available"],
        "uptime_seconds": health["uptime_seconds"],
        "endpoints": {
            "predict": "POST /predict - Sentiment prediction",
            "health": "GET /health - Service health check",
            "models": "GET /models - List available models"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        health = analyzer.get_health_status()
        
        # Determine overall status
        has_any_model = any(health["models_available"].values())
        status = "healthy" if has_any_model else "degraded"
        
        return HealthResponse(
            status=status,
            service="Standalone Model Service",
            models_available=health["models_available"],
            fallback_available=health["fallback_available"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=health["uptime_seconds"]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/predict", response_model=PredictionResponse)
async def predict_sentiment(request: PredictionRequest):
    """Predict sentiment endpoint"""
    try:
        logger.info(f"Prediction request: model={request.model_name}, text_length={len(request.text)}")
        
        # Get prediction
        result = analyzer.predict(request.text, request.model_name)
        
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
        raise HTTPException(
            status_code=500, 
            detail=f"Prediction failed: {str(e)}"
        )

@app.post("/predict/batch", response_model=BatchSentimentResponse)
async def predict_batch_sentiment(request: Dict[str, Any]):
    """Predict sentiment for multiple texts"""
    try:
        texts = request.get("texts", [])
        model_name = request.get("model_name")
        return_confidence = request.get("return_confidence", True)
        
        if not texts:
            raise HTTPException(status_code=400, detail="No texts provided")
        
        if len(texts) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 texts allowed per batch")
        
        logger.info(f"Batch prediction request: {len(texts)} texts")
        
        start_time = time.time()
        results = []
        
        # Process each text
        for text in texts:
            result = analyzer.predict(text, model_name)
            
            response_data = PredictionResponse(
                text=text,
                sentiment=result["sentiment"],
                confidence=result["confidence"] if return_confidence else None,
                scores=result["scores"] if return_confidence else None,
                model_used=result["model_used"],
                processing_time_ms=result["processing_time_ms"],
                timestamp=result["timestamp"]
            )
            results.append(response_data)
        
        total_time = time.time() - start_time
        
        # Use the model from the first prediction for reporting
        model_used = results[0].model_used if results else "unknown"
        
        return BatchSentimentResponse(
            results=results,
            total_processed=len(results),
            total_processing_time=total_time,
            model_used=model_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/models", response_model=ModelsResponse)
async def get_models():
    """Get available models"""
    try:
        health = analyzer.get_health_status()
        
        models = []
        for name, info in analyzer.available_models.items():
            model_info = {
                "name": name,
                "display_name": info["name"],
                "type": info["type"],
                "available": info["available"],
                "description": info["description"],
                "loaded": name == "vader" and VADER_AVAILABLE
            }
            models.append(model_info)
        
        return ModelsResponse(
            models=models,
            total_available=sum(1 for m in models if m["available"]),
            fallback_available=health["fallback_available"],
            recommended="vader" if VADER_AVAILABLE else None,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"List models failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description="UCLA Sentiment Analysis - Standalone Model Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting UCLA Sentiment Analysis - Standalone Model Service")
    logger.info(f"📡 Server: {args.host}:{args.port}")
    logger.info(f"🔄 VADER available: {'✅' if VADER_AVAILABLE else '❌'}")
    logger.info(f"📚 API docs: http://{args.host}:{args.port}/docs")
    
    # Test VADER if available
    if VADER_AVAILABLE:
        try:
            test_result = analyzer.predict_with_vader("This is a test message")
            logger.info(f"✅ VADER test successful: {test_result['sentiment']}")
        except Exception as e:
            logger.warning(f"⚠️ VADER test failed: {e}")
    else:
        logger.error("❌ No sentiment analysis models available!")
        sys.exit(1)
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level.lower()
    )

if __name__ == "__main__":
    main()
