#!/usr/bin/env python3

"""
Enhanced Model Service Client with Circuit Breaker and VADER Fallback
Implements failsafe features for UCLA Sentiment Analysis
"""

import os
import logging
import requests
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum

# Import VADER for failsafe fallback
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as VaderAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    print("⚠️  VADER not available. Install with: pip install vaderSentiment")

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Circuit is open, using fallback
    HALF_OPEN = "half_open" # Testing if service is back

class ModelServiceClientWithCircuitBreaker:
    """
    Enhanced model service client with circuit breaker pattern
    Automatically falls back to VADER after multiple failures
    """
    
    def __init__(self, model_service_url: str = None):
        self.model_service_url = model_service_url or os.getenv(
            "MODEL_SERVICE_URL", 
            "http://localhost:8081"
        )
        self.timeout = int(os.getenv("MODEL_SERVICE_TIMEOUT", "30"))
        
        # Circuit breaker configuration
        self.failure_threshold = int(os.getenv("MODEL_SERVICE_FAILURE_THRESHOLD", "3"))
        self.recovery_timeout = int(os.getenv("MODEL_SERVICE_RECOVERY_TIMEOUT", "60"))  # seconds
        self.half_open_max_calls = int(os.getenv("MODEL_SERVICE_HALF_OPEN_CALLS", "1"))
        
        # Circuit breaker state
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
        # Initialize VADER as fallback
        self.vader_analyzer = VaderAnalyzer() if VADER_AVAILABLE else None
        
        # Service status tracking
        self._service_available = None
        self._last_health_check = 0
        self._health_check_interval = 30  # Check every 30 seconds
        
        logger.info(f"Model service client initialized with circuit breaker")
        logger.info(f"Failure threshold: {self.failure_threshold}, Recovery timeout: {self.recovery_timeout}s")
        logger.info(f"VADER fallback: {'Available' if VADER_AVAILABLE else 'Not available'}")
    
    def _should_attempt_request(self) -> bool:
        """Check if we should attempt a request based on circuit breaker state"""
        current_time = time.time()
        
        if self.circuit_state == CircuitState.CLOSED:
            return True
        elif self.circuit_state == CircuitState.OPEN:
            if current_time - self.last_failure_time > self.recovery_timeout:
                self.circuit_state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("Circuit breaker: Moving to HALF_OPEN state")
                return True
            return False
        elif self.circuit_state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def _record_success(self):
        """Record a successful request"""
        if self.circuit_state == CircuitState.HALF_OPEN:
            self.circuit_state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info("Circuit breaker: Service recovered, moving to CLOSED state")
        elif self.circuit_state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)  # Gradual recovery
    
    def _record_failure(self):
        """Record a failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.circuit_state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.circuit_state = CircuitState.OPEN
                logger.warning(f"Circuit breaker: OPENED after {self.failure_count} failures")
                logger.info("Switching to VADER fallback for sentiment analysis")
        elif self.circuit_state == CircuitState.HALF_OPEN:
            self.circuit_state = CircuitState.OPEN
            logger.warning("Circuit breaker: Service still failing, back to OPEN state")
        
        self.half_open_calls += 1
    
    def _vader_fallback(self, text: str, include_probabilities: bool = True) -> Dict[str, Any]:
        """Use VADER as fallback when model service is unavailable"""
        if not VADER_AVAILABLE:
            return self._simple_fallback(text, "VADER not available")
        
        start_time = time.time()
        
        try:
            # Analyze with VADER
            scores = self.vader_analyzer.polarity_scores(text)
            processing_time = (time.time() - start_time) * 1000
            
            # Convert VADER output to our format
            compound = scores['compound']
            
            if compound >= 0.05:
                sentiment = 'positive'
                confidence = min(0.7 + abs(compound) * 0.3, 0.95)
            elif compound <= -0.05:
                sentiment = 'negative'
                confidence = min(0.7 + abs(compound) * 0.3, 0.95)
            else:
                sentiment = 'neutral'
                confidence = 0.6 + (0.4 * (1 - abs(compound)))
            
            result = {
                'text': text[:100] + '...' if len(text) > 100 else text,
                'sentiment': sentiment,
                'confidence': round(confidence, 3),
                'compound_score': round(compound, 3),
                'processing_time_ms': round(processing_time, 2),
                'model_used': 'vader',
                'model_name': 'VADER Sentiment Analyzer',
                'source': 'vader-fallback',
                'circuit_breaker_state': self.circuit_state.value,
                'failure_count': self.failure_count,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if include_probabilities:
                result['probabilities'] = {
                    'positive': round(scores['pos'], 3),
                    'negative': round(scores['neg'], 3),
                    'neutral': round(scores['neu'], 3)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"VADER fallback failed: {e}")
            return self._simple_fallback(text, f"VADER error: {str(e)}")
    
    def _simple_fallback(self, text: str, reason: str) -> Dict[str, Any]:
        """Ultimate fallback with simple sentiment analysis"""
        # Import here to avoid circular imports
        try:
            from app.api.main_docker import sentiment_analyzer
            result = sentiment_analyzer.analyze(text)
            result.update({
                'source': 'simple-fallback',
                'model_used': 'simple-rules',
                'model_name': 'Simple rule-based classifier',
                'circuit_breaker_state': self.circuit_state.value,
                'failure_count': self.failure_count,
                'fallback_reason': reason
            })
            return result
        except ImportError:
            # Ultimate fallback
            return {
                'text': text[:100] + '...' if len(text) > 100 else text,
                'sentiment': 'neutral',
                'confidence': 0.5,
                'compound_score': 0.0,
                'probabilities': {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33},
                'processing_time_ms': 1.0,
                'model_used': 'emergency-fallback',
                'source': 'emergency-fallback',
                'error': reason,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def predict_sentiment(self, text: str, model: str = "distilbert-sentiment", 
                         include_probabilities: bool = True) -> Dict[str, Any]:
        """
        Predict sentiment with circuit breaker protection
        Falls back to VADER after multiple ML service failures
        """
        # Check circuit breaker state
        if not self._should_attempt_request():
            logger.debug(f"Circuit breaker {self.circuit_state.value}: Using VADER fallback")
            return self._vader_fallback(text, include_probabilities)
        
        # Attempt ML service request
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
                result['circuit_breaker_state'] = self.circuit_state.value
                self._record_success()
                return result
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.warning(f"Model service request failed: {e}")
            self._record_failure()
            
            # Return VADER fallback
            return self._vader_fallback(text, include_probabilities)
    
    def predict_batch(self, texts: List[str], model: str = "distilbert-sentiment",
                     include_probabilities: bool = True) -> Dict[str, Any]:
        """
        Batch predict with circuit breaker protection
        """
        # Check circuit breaker state
        if not self._should_attempt_request():
            logger.debug(f"Circuit breaker {self.circuit_state.value}: Using VADER batch fallback")
            return self._vader_batch_fallback(texts, include_probabilities)
        
        try:
            response = requests.post(
                f"{self.model_service_url}/predict/batch",
                json={
                    "texts": texts,
                    "model": model,
                    "include_probabilities": include_probabilities
                },
                timeout=self.timeout * 2
            )
            
            if response.status_code == 200:
                result = response.json()
                result['source'] = 'model-service'
                result['circuit_breaker_state'] = self.circuit_state.value
                self._record_success()
                return result
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Model service batch request failed: {e}")
            self._record_failure()
            
            return self._vader_batch_fallback(texts, include_probabilities)
    
    def _vader_batch_fallback(self, texts: List[str], include_probabilities: bool = True) -> Dict[str, Any]:
        """VADER batch fallback"""
        start_time = time.time()
        results = []
        
        for i, text in enumerate(texts):
            result = self._vader_fallback(text, include_probabilities)
            result['batch_index'] = i
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
                "method": "vader-fallback",
                "circuit_breaker_state": self.circuit_state.value,
                "sentiment_distribution": {
                    "positive": sentiments.count('positive'),
                    "negative": sentiments.count('negative'),
                    "neutral": sentiments.count('neutral')
                }
            },
            "source": "vader-fallback",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring"""
        return {
            "circuit_state": self.circuit_state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout,
            "model_service_url": self.model_service_url,
            "vader_available": VADER_AVAILABLE,
            "time_until_retry": max(0, self.recovery_timeout - (time.time() - self.last_failure_time)) if self.circuit_state == CircuitState.OPEN else 0
        }
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (for admin use)"""
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        logger.info("Circuit breaker manually reset to CLOSED state")
    
    def list_models(self) -> Dict[str, Any]:
        """List available models with circuit breaker awareness"""
        if not self._should_attempt_request():
            return {
                "available": False,
                "error": f"Model service unavailable (circuit breaker {self.circuit_state.value})",
                "circuit_breaker_status": self.get_circuit_breaker_status(),
                "fallback": "VADER sentiment analysis active"
            }
        
        try:
            response = requests.get(f"{self.model_service_url}/models", timeout=10)
            if response.status_code == 200:
                result = response.json()
                self._record_success()
                return result
            else:
                raise Exception(f"HTTP {response.status_code}")
        except Exception as e:
            self._record_failure()
            return {
                "available": False,
                "error": str(e),
                "circuit_breaker_status": self.get_circuit_breaker_status()
            }

# Global enhanced model service client
enhanced_model_service_client = ModelServiceClientWithCircuitBreaker()
