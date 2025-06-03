#!/usr/bin/env python3

"""
Model Service Client for UCLA Sentiment Analysis
Handles communication with external model service
"""

import os
import logging
import requests
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ModelServiceClient:
    """
    Client for communicating with external model service
    Provides fallback to simple sentiment analysis if model service unavailable
    """
    
    def __init__(self, model_service_url: str = None):
        # if model_service_url is null localhost:8081
        self.model_service_url = model_service_url or os.getenv(
            "MODEL_SERVICE_URL", 
            "http://localhost:8081"
        )
        self.timeout = int(os.getenv("MODEL_SERVICE_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("MODEL_SERVICE_RETRIES", "2"))
        
        # Track service status
        self._service_available = None
        self._last_health_check = 0
        self._health_check_interval = 60  # Check every minute
        
        logger.info(f"Model service client initialized: {self.model_service_url}")
    
    def is_service_available(self) -> bool:
        """
        Check if model service is available with caching
        """
        current_time = time.time()
        
        # Use cached result if recent
        if (self._service_available is not None and 
            current_time - self._last_health_check < self._health_check_interval):
            return self._service_available
        
        try:
            response = requests.get(
                f"{self.model_service_url}/health",
                timeout=5
            )
            
            self._service_available = response.status_code == 200
            self._last_health_check = current_time
            
            if self._service_available:
                logger.debug("Model service is available")
            else:
                logger.warning(f"Model service health check failed: {response.status_code}")
            
            return self._service_available
            
        except Exception as e:
            logger.warning(f"Model service unavailable: {e}")
            self._service_available = False
            self._last_health_check = current_time
            return False
    
    def predict_sentiment(self, text: str, model: str = "distilbert-sentiment", 
                         include_probabilities: bool = True) -> Dict[str, Any]:
        """
        Predict sentiment using external model service
        Falls back to simple analysis if service unavailable
        """
        if not self.is_service_available():
            return self._fallback_prediction(text, "Model service unavailable")
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.model_service_url}/predict",
                    json={
                        "text": text,
                        "model": model,
                        "include_probabilities": include_probabilities
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result['source'] = 'model-service'
                    result['attempt'] = attempt + 1
                    return result
                elif response.status_code == 503:
                    logger.warning("Model service temporarily unavailable")
                    return self._fallback_prediction(text, "Model service overloaded")
                else:
                    logger.error(f"Model service error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Model service timeout (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
            except Exception as e:
                logger.error(f"Model service request failed: {e}")
                break
        
        # All attempts failed, use fallback
        return self._fallback_prediction(text, "Model service failed after retries")
    
    def predict_batch(self, texts: List[str], model: str = "distilbert-sentiment",
                     include_probabilities: bool = True) -> Dict[str, Any]:
        """
        Batch predict sentiment using external model service
        """
        if not self.is_service_available():
            return self._fallback_batch_prediction(texts, "Model service unavailable")
        
        try:
            response = requests.post(
                f"{self.model_service_url}/predict/batch",
                json={
                    "texts": texts,
                    "model": model,
                    "include_probabilities": include_probabilities
                },
                timeout=self.timeout * 2  # Longer timeout for batch
            )
            
            if response.status_code == 200:
                result = response.json()
                result['source'] = 'model-service'
                return result
            else:
                logger.error(f"Model service batch error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Model service batch request failed: {e}")
        
        return self._fallback_batch_prediction(texts, "Model service batch failed")
    
    def list_models(self) -> Dict[str, Any]:
        """List available models from model service"""
        if not self.is_service_available():
            return {
                "available": False,
                "error": "Model service unavailable",
                "models": {}
            }
        
        try:
            response = requests.get(
                f"{self.model_service_url}/models",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to list models: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error listing models: {e}")
        
        return {"available": False, "error": "Failed to connect to model service"}
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """Download model via model service"""
        if not self.is_service_available():
            raise Exception("Model service unavailable")
        
        try:
            response = requests.post(
                f"{self.model_service_url}/models/download",
                json={"model": model},
                timeout=300  # 5 minutes for download
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Download failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Model download failed: {e}")
            raise
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get detailed model service status
        """
        try:
            response = requests.get(
                f"{self.model_service_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "status": data,
                    "url": self.model_service_url,
                    "last_check": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "available": False,
                    "error": f"HTTP {response.status_code}",
                    "url": self.model_service_url
                }
                
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "url": self.model_service_url
            }
    
    def _fallback_prediction(self, text: str, reason: str) -> Dict[str, Any]:
        """
        Fallback to simple sentiment analysis
        """
        # Import here to avoid circular imports
        from app.api.main import sentiment_analyzer
        
        result = sentiment_analyzer.analyze(text)
        result.update({
            'source': 'fallback-simple',
            'model_used': 'simple-rules',
            'model_name': 'Simple rule-based classifier',
            'fallback_reason': reason,
            'note': 'Using simple sentiment analysis (model service unavailable)'
        })
        
        return result
    
    def _fallback_batch_prediction(self, texts: List[str], reason: str) -> Dict[str, Any]:
        """Fallback batch prediction using simple method"""
        from app.api.main import sentiment_analyzer
        
        start_time = time.time()
        results = []
        
        for i, text in enumerate(texts):
            result = sentiment_analyzer.analyze(text)
            result.update({
                'batch_index': i,
                'source': 'fallback-simple',
                'model_used': 'simple-rules',
                'fallback_reason': reason
            })
            results.append(result)
        
        total_time = (time.time() - start_time) * 1000
        sentiments = [r['sentiment'] for r in results]
        
        return {
            "results": results,
            "summary": {
                "total_processed": len(results),
                "successful": len(results),
                "failed": 0,
                "total_processing_time_ms": round(total_time, 2),
                "average_time_per_text_ms": round(total_time / len(texts), 2),
                "method": "fallback-simple",
                "fallback_reason": reason,
                "sentiment_distribution": {
                    "positive": sentiments.count('positive'),
                    "negative": sentiments.count('negative'),
                    "neutral": sentiments.count('neutral')
                }
            },
            "source": "fallback-simple",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global model service client
model_service_client = ModelServiceClient()
