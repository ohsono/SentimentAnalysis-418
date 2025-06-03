#!/usr/bin/env python3

"""
Enhanced Model Service Client with Circuit Breaker Pattern
Implements failsafe features and fallback to VADER sentiment analysis
"""

import os
import logging
import requests
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logging.warning("VADER Sentiment not available. Install with: pip install vaderSentiment")

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker triggered, using fallback
    HALF_OPEN = "half_open"  # Testing if service recovered

class ModelServiceClientWithCircuitBreaker:
    """
    Enhanced Model Service Client with Circuit Breaker Pattern
    Automatically falls back to VADER sentiment when LLM service fails
    """
    
    def __init__(self, model_service_url: str = None):
        self.model_service_url = model_service_url or os.getenv(
            "MODEL_SERVICE_URL", 
            "http://localhost:8081"
        )
        self.timeout = int(os.getenv("MODEL_SERVICE_TIMEOUT", "30"))
        
        # Circuit Breaker Configuration
        self.failure_threshold = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "3"))
        self.recovery_timeout = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))  # seconds
        self.half_open_max_calls = int(os.getenv("CIRCUIT_BREAKER_HALF_OPEN_CALLS", "3"))
        
        # Circuit Breaker State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
        # Initialize VADER for fallback
        if VADER_AVAILABLE:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("✅ VADER Sentiment Analyzer initialized for fallback")
        else:
            self.vader_analyzer = None
            logger.warning("⚠️ VADER not available - using simple fallback")
        
        logger.info(f"🔒 Circuit Breaker initialized: threshold={self.failure_threshold}, recovery={self.recovery_timeout}s")
    
    def _record_success(self):
        """Record successful call to LLM service"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset failure count on success
    
    def _record_failure(self):
        """Record failed call to LLM service"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self._open_circuit()
    
    def _open_circuit(self):
        """Open circuit breaker - use fallback only"""
        self.state = CircuitState.OPEN
        logger.warning(f"🚨 Circuit breaker OPENED - {self.failure_count} consecutive failures. Using VADER fallback.")
    
    def _close_circuit(self):
        """Close circuit breaker - resume normal operation"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_calls = 0
        logger.info("✅ Circuit breaker CLOSED - LLM service recovered")
    
    def _should_attempt_call(self) -> bool:
        """Check if we should attempt to call LLM service"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("🔄 Circuit breaker HALF-OPEN - testing service recovery")
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def predict_sentiment(self, text: str, model: str = "distilbert-sentiment", 
                         include_probabilities: bool = True) -> Dict[str, Any]:
        """
        Predict sentiment with circuit breaker protection
        Falls back to VADER when LLM service fails
        """
        # Check circuit breaker state
        if not self._should_attempt_call():
            logger.debug(f"Circuit breaker {self.state.value} - using VADER fallback")
            return self._vader_fallback(text, "Circuit breaker open")
        
        # Attempt LLM service call
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
                result['source'] = 'llm-service'
                result['circuit_state'] = self.state.value
                self._record_success()
                return result
            else:
                logger.warning(f"LLM service HTTP error: {response.status_code}")
                self._record_failure()
                return self._vader_fallback(text, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning("LLM service timeout")
            self._record_failure()
            return self._vader_fallback(text, "Service timeout")
        except requests.exceptions.ConnectionError:
            logger.warning("LLM service connection error")
            self._record_failure()
            return self._vader_fallback(text, "Connection error")
        except Exception as e:
            logger.error(f"LLM service unexpected error: {e}")
            self._record_failure()
            return self._vader_fallback(text, f"Unexpected error: {str(e)}")
    
    def predict_batch(self, texts: List[str], model: str = "distilbert-sentiment",
                     include_probabilities: bool = True) -> Dict[str, Any]:
        """
        Batch predict with circuit breaker protection
        """
        if not self._should_attempt_call():
            logger.debug(f"Circuit breaker {self.state.value} - using VADER batch fallback")
            return self._vader_batch_fallback(texts, "Circuit breaker open")
        
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
                result['source'] = 'llm-service'
                result['circuit_state'] = self.state.value
                self._record_success()
                return result
            else:
                self._record_failure()
                return self._vader_batch_fallback(texts, f"HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"LLM batch service error: {e}")
            self._record_failure()
            return self._vader_batch_fallback(texts, str(e))
    
    def _vader_fallback(self, text: str, reason: str) -> Dict[str, Any]:
        """Fallback to VADER sentiment analysis"""
        if not VADER_AVAILABLE:
            return self._simple_fallback(text, reason)
        
        start_time = time.time()
        
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            processing_time = (time.time() - start_time) * 1000
            
            # Convert VADER scores to standard format
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
            
            return {
                'text': text[:100] + '...' if len(text) > 100 else text,
                'sentiment': sentiment,
                'confidence': round(confidence, 3),
                'compound_score': round(compound, 3),
                'probabilities': {
                    'positive': round(scores['pos'], 3),
                    'negative': round(scores['neg'], 3),
                    'neutral': round(scores['neu'], 3)
                },
                'processing_time_ms': round(processing_time, 2),
                'model_used': 'vader',
                'model_name': 'VADER Sentiment Analyzer',
                'source': 'vader-fallback',
                'fallback_reason': reason,
                'circuit_state': self.state.value,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"VADER fallback error: {e}")
            return self._simple_fallback(text, f"VADER error: {e}")
    
    def _vader_batch_fallback(self, texts: List[str], reason: str) -> Dict[str, Any]:
        """Batch VADER fallback"""
        start_time = time.time()
        results = []
        
        for i, text in enumerate(texts):
            result = self._vader_fallback(text, reason)
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
                "fallback_reason": reason,
                "circuit_state": self.state.value,
                "sentiment_distribution": {
                    "positive": sentiments.count('positive'),
                    "negative": sentiments.count('negative'),
                    "neutral": sentiments.count('neutral')
                }
            },
            "source": "vader-fallback",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _simple_fallback(self, text: str, reason: str) -> Dict[str, Any]:
        """Ultimate fallback when VADER is not available"""
        return {
            'text': text[:100] + '...' if len(text) > 100 else text,
            'sentiment': 'neutral',
            'confidence': 0.5,
            'compound_score': 0.0,
            'probabilities': {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33},
            'processing_time_ms': 1.0,
            'model_used': 'simple-fallback',
            'model_name': 'Simple rule-based fallback',
            'source': 'simple-fallback',
            'fallback_reason': reason,
            'circuit_state': self.state.value,
            'note': 'VADER and LLM service unavailable',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "time_since_last_failure": time.time() - self.last_failure_time if self.last_failure_time > 0 else 0,
            "recovery_timeout": self.recovery_timeout,
            "half_open_calls": self.half_open_calls if self.state == CircuitState.HALF_OPEN else 0,
            "vader_available": VADER_AVAILABLE,
            "service_url": self.model_service_url
        }
    
    def list_models(self) -> Dict[str, Any]:
        """List available models with circuit breaker protection"""
        if not self._should_attempt_call():
            return {
                "available": False,
                "reason": f"Circuit breaker {self.state.value}",
                "fallback": "VADER sentiment analysis available" if VADER_AVAILABLE else "Simple fallback only"
            }
        
        try:
            response = requests.get(f"{self.model_service_url}/models", timeout=10)
            if response.status_code == 200:
                result = response.json()
                self._record_success()
                return result
            else:
                self._record_failure()
                return {"available": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            self._record_failure()
            return {"available": False, "error": str(e)}

# Global enhanced model service client
enhanced_model_client = ModelServiceClientWithCircuitBreaker()
