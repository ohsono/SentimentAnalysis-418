#!/usr/bin/env python3

"""
DistilBERT Model Manager for Sentiment Analysis
Lightweight, fast, and accurate sentiment analysis using DistilBERT
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    pipeline
)
import psutil
from datetime import datetime, timezone
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DistilBERTModelManager:
    """
    Manages DistilBERT models for sentiment analysis
    Optimized for speed and low memory usage
    """
    
    def __init__(self, model_cache_dir: str = "/app/models"):
        self.model_cache_dir = model_cache_dir
        self.loaded_models = {}
        self.model_configs = {
            "distilbert-sentiment": {
                "model_name": "distilbert-base-uncased-finetuned-sst-2-english",
                "description": "DistilBERT fine-tuned on SST-2 (Stanford Sentiment Treebank)",
                "type": "sentiment-analysis",
                "size": "small",
                "languages": ["en"],
                "accuracy": 0.91,
                "speed": "fast"
            },
            "distilbert-emotion": {
                "model_name": "j-hartmann/emotion-english-distilroberta-base",
                "description": "DistilRoBERTa for emotion classification",
                "type": "emotion-analysis", 
                "size": "small",
                "languages": ["en"],
                "accuracy": 0.88,
                "speed": "fast"
            },
            "twitter-roberta": {
                "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                "description": "RoBERTa trained on Twitter data",
                "type": "sentiment-analysis",
                "size": "medium",
                "languages": ["en"],
                "accuracy": 0.89,
                "speed": "medium"
            }
        }
        self.default_model = "distilbert-sentiment"
        
        # Create cache directory
        os.makedirs(self.model_cache_dir, exist_ok=True)
        
    def get_model_info(self, model_key: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        if model_key not in self.model_configs:
            raise ValueError(f"Unknown model: {model_key}")
        
        config = self.model_configs[model_key].copy()
        config["loaded"] = model_key in self.loaded_models
        config["cache_path"] = os.path.join(self.model_cache_dir, model_key)
        
        return config
    
    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models with their configurations"""
        return {
            key: self.get_model_info(key) 
            for key in self.model_configs.keys()
        }
    
    def load_model(self, model_key: str = None) -> str:
        """Load a model into memory"""
        if model_key is None:
            model_key = self.default_model
            
        if model_key in self.loaded_models:
            logger.info(f"Model {model_key} already loaded")
            return model_key
            
        if model_key not in self.model_configs:
            raise ValueError(f"Unknown model: {model_key}")
        
        start_time = time.time()
        logger.info(f"Loading model: {model_key}")
        
        try:
            config = self.model_configs[model_key]
            model_name = config["model_name"]
            
            # Load tokenizer and model
            cache_dir = os.path.join(self.model_cache_dir, model_key)
            
            # Use HuggingFace pipeline for simplicity and speed
            sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                cache_dir=cache_dir,
                device=-1,  # Use CPU for consistency
                return_all_scores=True
            )
            
            self.loaded_models[model_key] = {
                "pipeline": sentiment_pipeline,
                "config": config,
                "loaded_at": datetime.now(timezone.utc),
                "load_time": time.time() - start_time
            }
            
            logger.info(f"✅ Model {model_key} loaded successfully in {time.time() - start_time:.2f}s")
            return model_key
            
        except Exception as e:
            logger.error(f"Failed to load model {model_key}: {e}")
            raise
    
    def predict_sentiment(self, text: str, model_key: str = None) -> Dict[str, Any]:
        """Predict sentiment for a single text"""
        if model_key is None:
            model_key = self.default_model
            
        # Load model if not already loaded
        if model_key not in self.loaded_models:
            self.load_model(model_key)
        
        start_time = time.time()
        
        try:
            pipeline_obj = self.loaded_models[model_key]["pipeline"]
            
            # Get prediction
            results = pipeline_obj(text)
            
            # Parse results (HuggingFace returns different formats)
            if isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], list):
                    # return_all_scores=True format
                    scores = results[0]
                else:
                    # Single prediction format
                    scores = results
            else:
                scores = results
            
            # Normalize the results
            probabilities = {}
            max_score = 0
            predicted_label = "neutral"
            
            for score_dict in scores:
                label = score_dict["label"].lower()
                score = score_dict["score"]
                
                # Map labels to standard format
                if label in ["positive", "pos", "label_1"]:
                    probabilities["positive"] = score
                    if score > max_score:
                        max_score = score
                        predicted_label = "positive"
                elif label in ["negative", "neg", "label_0"]:
                    probabilities["negative"] = score
                    if score > max_score:
                        max_score = score
                        predicted_label = "negative"
                else:
                    probabilities["neutral"] = score
                    if score > max_score:
                        max_score = score
                        predicted_label = "neutral"
            
            # Ensure all three categories exist
            if "positive" not in probabilities:
                probabilities["positive"] = 0.0
            if "negative" not in probabilities:
                probabilities["negative"] = 0.0
            if "neutral" not in probabilities:
                probabilities["neutral"] = 1.0 - probabilities["positive"] - probabilities["negative"]
            
            # Calculate compound score (similar to VADER)
            compound_score = probabilities["positive"] - probabilities["negative"]
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "sentiment": predicted_label,
                "confidence": max_score,
                "compound_score": compound_score,
                "probabilities": probabilities,
                "model_used": model_key,
                "model_name": self.model_configs[model_key]["model_name"],
                "processing_time_ms": round(processing_time, 2),
                "text_hash": hashlib.md5(text.encode()).hexdigest()[:16]
            }
            
        except Exception as e:
            logger.error(f"Prediction failed for model {model_key}: {e}")
            raise
    
    def predict_batch(self, texts: List[str], model_key: str = None) -> List[Dict[str, Any]]:
        """Predict sentiment for multiple texts efficiently"""
        if model_key is None:
            model_key = self.default_model
            
        # Load model if not already loaded
        if model_key not in self.loaded_models:
            self.load_model(model_key)
        
        start_time = time.time()
        
        try:
            pipeline_obj = self.loaded_models[model_key]["pipeline"]
            
            # Batch prediction
            results = pipeline_obj(texts)
            
            batch_results = []
            for i, text in enumerate(texts):
                try:
                    # Get results for this text
                    text_results = results[i] if isinstance(results[i], list) else [results[i]]
                    
                    # Process similar to single prediction
                    probabilities = {}
                    max_score = 0
                    predicted_label = "neutral"
                    
                    for score_dict in text_results:
                        label = score_dict["label"].lower()
                        score = score_dict["score"]
                        
                        if label in ["positive", "pos", "label_1"]:
                            probabilities["positive"] = score
                            if score > max_score:
                                max_score = score
                                predicted_label = "positive"
                        elif label in ["negative", "neg", "label_0"]:
                            probabilities["negative"] = score
                            if score > max_score:
                                max_score = score
                                predicted_label = "negative"
                        else:
                            probabilities["neutral"] = score
                            if score > max_score:
                                max_score = score
                                predicted_label = "neutral"
                    
                    # Ensure all categories exist
                    if "positive" not in probabilities:
                        probabilities["positive"] = 0.0
                    if "negative" not in probabilities:
                        probabilities["negative"] = 0.0
                    if "neutral" not in probabilities:
                        probabilities["neutral"] = 1.0 - probabilities["positive"] - probabilities["negative"]
                    
                    compound_score = probabilities["positive"] - probabilities["negative"]
                    
                    batch_results.append({
                        "sentiment": predicted_label,
                        "confidence": max_score,
                        "compound_score": compound_score,
                        "probabilities": probabilities,
                        "model_used": model_key,
                        "model_name": self.model_configs[model_key]["model_name"],
                        "batch_index": i,
                        "text_hash": hashlib.md5(text.encode()).hexdigest()[:16]
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing text {i}: {e}")
                    batch_results.append({
                        "sentiment": "neutral",
                        "confidence": 0.0,
                        "compound_score": 0.0,
                        "probabilities": {"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                        "model_used": model_key,
                        "batch_index": i,
                        "error": str(e),
                        "text_hash": hashlib.md5(text.encode()).hexdigest()[:16]
                    })
            
            total_time = (time.time() - start_time) * 1000
            
            # Add timing info to each result
            avg_time = total_time / len(texts)
            for result in batch_results:
                result["processing_time_ms"] = round(avg_time, 2)
            
            return batch_results
            
        except Exception as e:
            logger.error(f"Batch prediction failed for model {model_key}: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the model manager"""
        memory_info = psutil.virtual_memory()
        
        return {
            "status": "healthy",
            "loaded_models": list(self.loaded_models.keys()),
            "available_models": list(self.model_configs.keys()),
            "default_model": self.default_model,
            "memory_usage": {
                "total_mb": round(memory_info.total / 1024 / 1024),
                "used_mb": round(memory_info.used / 1024 / 1024),
                "percent": memory_info.percent
            },
            "cache_dir": self.model_cache_dir,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def unload_model(self, model_key: str):
        """Unload a model from memory"""
        if model_key in self.loaded_models:
            del self.loaded_models[model_key]
            logger.info(f"Model {model_key} unloaded")
        else:
            logger.warning(f"Model {model_key} was not loaded")
    
    def cleanup(self):
        """Clean up all loaded models"""
        logger.info("Cleaning up model manager...")
        self.loaded_models.clear()
        logger.info("Model manager cleanup complete")
