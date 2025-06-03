#!/usr/bin/env python3

"""
Lightweight Model Manager for Swappable ML Models
Optimized for Docker environments with easy model replacement
"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    import torch
    from transformers import (
        AutoTokenizer, 
        AutoModelForSequenceClassification, 
        pipeline
    )
    import numpy as np
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch/Transformers not available - model service will be limited")

class LightweightModelManager:
    """
    Lightweight model manager designed for easy swapping and Docker deployment
    
    Features:
    - Lazy loading of models
    - Memory-efficient model caching
    - Async model operations
    - Easy model swapping
    - Health monitoring
    """
    
    def __init__(self):
        self.loaded_models = {}
        self.model_cache = {}
        self.model_metadata = {}
        self.loading_locks = {}
        
        # Model registry - easily swappable
        self.available_models = {
            "distilbert-sentiment": {
                "name": "DistilBERT Sentiment",
                "model_name": "distilbert-base-uncased-finetuned-sst-2-english",
                "description": "Fast and efficient sentiment analysis",
                "size": "small",
                "speed": "fast",
                "accuracy": "good",
                "languages": ["en"],
                "use_case": "general",
                "memory_mb": 250
            },
            "twitter-roberta": {
                "name": "Twitter RoBERTa",
                "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                "description": "Optimized for social media text",
                "size": "medium",
                "speed": "medium",
                "accuracy": "excellent",
                "languages": ["en"],
                "use_case": "social_media",
                "memory_mb": 500
            },
            "bert-sentiment": {
                "name": "BERT Multilingual Sentiment",
                "model_name": "nlptown/bert-base-multilingual-uncased-sentiment",
                "description": "Multilingual sentiment analysis",
                "size": "large",
                "speed": "slow",
                "accuracy": "excellent",
                "languages": ["en", "es", "fr", "de", "it", "pt"],
                "use_case": "multilingual",
                "memory_mb": 450
            }
        }
        
        # Performance tracking
        self.prediction_count = 0
        self.total_prediction_time = 0.0
        self.last_prediction_time = None
        
        # Health status
        self.health_status = {
            "initialized": False,
            "models_loaded": 0,
            "last_error": None,
            "memory_usage": 0
        }
    
    async def initialize(self):
        """Initialize the model manager"""
        try:
            if not TORCH_AVAILABLE:
                raise Exception("PyTorch/Transformers not available")
            
            logger.info("Initializing lightweight model manager...")
            
            # Set device (CPU for lightweight deployment)
            self.device = torch.device("cpu")
            
            # Initialize locks for each model
            for model_key in self.available_models.keys():
                self.loading_locks[model_key] = asyncio.Lock()
            
            self.health_status["initialized"] = True
            logger.info("✅ Lightweight model manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize model manager: {e}")
            self.health_status["last_error"] = str(e)
            raise
    
    async def load_model(self, model_key: str) -> bool:
        """Load a specific model (with async locking)"""
        if not TORCH_AVAILABLE:
            raise Exception("PyTorch/Transformers not available")
        
        if model_key in self.loaded_models:
            logger.debug(f"Model {model_key} already loaded")
            return True
        
        if model_key not in self.available_models:
            raise ValueError(f"Unknown model: {model_key}")
        
        # Use async lock to prevent concurrent loading
        async with self.loading_locks[model_key]:
            # Double-check after acquiring lock
            if model_key in self.loaded_models:
                return True
            
            try:
                model_info = self.available_models[model_key]
                model_name = model_info["model_name"]
                
                logger.info(f"Loading model: {model_key} ({model_name})")
                start_time = time.time()
                
                # Load tokenizer and model
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSequenceClassification.from_pretrained(model_name)
                model.to(self.device)
                model.eval()  # Set to evaluation mode
                
                # Create pipeline for easy inference
                classifier = pipeline(
                    "sentiment-analysis",
                    model=model,
                    tokenizer=tokenizer,
                    device=-1,  # CPU
                    return_all_scores=True
                )
                
                load_time = time.time() - start_time
                
                # Store loaded model
                self.loaded_models[model_key] = {
                    "classifier": classifier,
                    "tokenizer": tokenizer,
                    "model": model,
                    "loaded_at": datetime.now(timezone.utc),
                    "load_time": load_time,
                    "prediction_count": 0
                }
                
                self.model_metadata[model_key] = {
                    **model_info,
                    "loaded": True,
                    "load_time": load_time
                }
                
                self.health_status["models_loaded"] += 1
                
                logger.info(f"✅ Model {model_key} loaded successfully in {load_time:.2f}s")
                return True
                
            except Exception as e:
                error_msg = f"Failed to load model {model_key}: {e}"
                logger.error(error_msg)
                self.health_status["last_error"] = error_msg
                raise Exception(error_msg)
    
    async def predict_sentiment_async(self, text: str, model_key: str = "distilbert-sentiment") -> Dict[str, Any]:
        """Predict sentiment asynchronously"""
        if not TORCH_AVAILABLE:
            raise Exception("PyTorch/Transformers not available")
        
        # Ensure model is loaded
        await self.load_model(model_key)
        
        start_time = time.time()
        
        try:
            model_info = self.loaded_models[model_key]
            classifier = model_info["classifier"]
            
            # Run prediction (this blocks, but we're in async context)
            results = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: classifier(text)
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Process results
            scores = results[0]  # Pipeline returns list, we want first result
            
            # Convert to standard format
            sentiment_map = {
                'POSITIVE': 'positive',
                'NEGATIVE': 'negative', 
                'NEUTRAL': 'neutral'
            }
            
            # Find highest scoring label
            best_result = max(scores, key=lambda x: x['score'])
            sentiment = sentiment_map.get(best_result['label'].upper(), 'neutral')
            confidence = best_result['score']
            
            # Calculate compound score (VADER-like)
            pos_score = next((s['score'] for s in scores if s['label'].upper() == 'POSITIVE'), 0)
            neg_score = next((s['score'] for s in scores if s['label'].upper() == 'NEGATIVE'), 0)
            compound_score = pos_score - neg_score
            
            # Create probabilities dict
            probabilities = {
                sentiment_map.get(s['label'].upper(), s['label'].lower()): s['score'] 
                for s in scores
            }
            
            # Update metrics
            self.prediction_count += 1
            self.total_prediction_time += processing_time
            self.last_prediction_time = datetime.now(timezone.utc)
            model_info["prediction_count"] += 1
            
            result = {
                "sentiment": sentiment,
                "confidence": round(confidence, 4),
                "compound_score": round(compound_score, 4),
                "probabilities": probabilities,
                "text_length": len(text),
                "model_used": model_key,
                "model_name": self.available_models[model_key]["name"],
                "processing_time_ms": round(processing_time, 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.debug(f"Prediction complete: {sentiment} (conf: {confidence:.3f}, {processing_time:.1f}ms)")
            return result
            
        except Exception as e:
            error_msg = f"Prediction failed for model {model_key}: {e}"
            logger.error(error_msg)
            self.health_status["last_error"] = error_msg
            raise Exception(error_msg)
    
    def predict_sentiment(self, text: str, model_key: str = "distilbert-sentiment") -> Dict[str, Any]:
        """Synchronous wrapper for backward compatibility"""
        return asyncio.run(self.predict_sentiment_async(text, model_key))
    
    async def list_available_models_async(self) -> Dict[str, Any]:
        """List all available models with metadata"""
        models = {}
        
        for key, info in self.available_models.items():
            model_data = info.copy()
            
            # Add runtime information
            if key in self.loaded_models:
                load_info = self.loaded_models[key]
                model_data.update({
                    "status": "loaded",
                    "loaded_at": load_info["loaded_at"].isoformat(),
                    "load_time": load_info["load_time"],
                    "prediction_count": load_info["prediction_count"]
                })
            else:
                model_data["status"] = "available"
            
            models[key] = model_data
        
        return models
    
    def list_available_models(self) -> Dict[str, Any]:
        """Synchronous wrapper"""
        return asyncio.run(self.list_available_models_async())
    
    async def download_model_async(self, model_key: str) -> Dict[str, Any]:
        """Download and cache a model"""
        if model_key not in self.available_models:
            raise ValueError(f"Unknown model: {model_key}")
        
        # Loading the model effectively downloads it
        success = await self.load_model(model_key)
        
        if success:
            return {
                "model_key": model_key,
                "status": "downloaded",
                "loaded": True,
                "metadata": self.model_metadata.get(model_key, {})
            }
        else:
            raise Exception(f"Failed to download model {model_key}")
    
    def download_model(self, model_key: str) -> Dict[str, Any]:
        """Synchronous wrapper"""
        return asyncio.run(self.download_model_async(model_key))
    
    def get_loaded_models(self) -> Dict[str, Any]:
        """Get information about currently loaded models"""
        return {
            key: {
                "loaded_at": info["loaded_at"].isoformat(),
                "load_time": info["load_time"],
                "prediction_count": info["prediction_count"]
            }
            for key, info in self.loaded_models.items()
        }
    
    def get_recommended_model(self) -> str:
        """Get the recommended model for general use"""
        return "distilbert-sentiment"  # Fast and reliable default
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status"""
        # Calculate memory usage (simplified)
        memory_usage = len(self.loaded_models) * 200  # Rough estimate
        
        avg_prediction_time = (
            self.total_prediction_time / self.prediction_count
            if self.prediction_count > 0 else 0
        )
        
        return {
            **self.health_status,
            "torch_available": TORCH_AVAILABLE,
            "models_available": len(self.available_models),
            "models_loaded": len(self.loaded_models),
            "total_predictions": self.prediction_count,
            "avg_prediction_time_ms": round(avg_prediction_time, 2),
            "last_prediction": self.last_prediction_time.isoformat() if self.last_prediction_time else None,
            "memory_usage_mb": memory_usage,
            "device": str(self.device) if hasattr(self, 'device') else "unknown"
        }
    
    async def clear_cache(self):
        """Clear all loaded models to free memory"""
        logger.info("Clearing model cache...")
        
        # Clear models
        for key in list(self.loaded_models.keys()):
            try:
                model_info = self.loaded_models[key]
                del model_info["classifier"]
                del model_info["tokenizer"] 
                del model_info["model"]
                del self.loaded_models[key]
                logger.info(f"Cleared model: {key}")
            except Exception as e:
                logger.warning(f"Error clearing model {key}: {e}")
        
        # Clear metadata
        self.model_metadata.clear()
        
        # Update health status
        self.health_status["models_loaded"] = 0
        
        # Force garbage collection
        if TORCH_AVAILABLE:
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        logger.info("✅ Model cache cleared")
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up model manager...")
        await self.clear_cache()
        logger.info("✅ Model manager cleanup complete")

# Global instance for easy access
lightweight_model_manager = LightweightModelManager()
