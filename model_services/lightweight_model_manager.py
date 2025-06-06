#!/usr/bin/env python3

"""
Enhanced Lightweight Model Manager for Swappable ML Models
Optimized for Docker environments with HuggingFace integration
"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import torch
    from transformers import (
        AutoTokenizer, 
        AutoModelForSequenceClassification, 
        pipeline
    )
    import numpy as np
    from huggingface_hub import snapshot_download, model_info
    TORCH_AVAILABLE = True
    HF_AVAILABLE = True
except ImportError as e:
    TORCH_AVAILABLE = False
    HF_AVAILABLE = False
    logger.warning(f"PyTorch/Transformers/HuggingFace not available: {e}")

# Import NLTK VADER as fallback
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    
    # Download VADER lexicon if not present
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        logger.info("Downloading NLTK VADER lexicon...")
        nltk.download('vader_lexicon', quiet=True)
    
    VADER_AVAILABLE = True
    logger.info("✅ NLTK VADER available as fallback sentiment analyzer")
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("NLTK VADER not available - limited fallback options")

class LightweightModelManager:
    """
    Enhanced lightweight model manager with HuggingFace integration
    
    Features:
    - HuggingFace model downloading
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
        self.model_paths = ['models/', 'model/', './models/', '../models/']
        self.model_found = False
        self.cache_dir = "./model_cache"
        
        # Create cache directory
        Path(self.cache_dir).mkdir(exist_ok=True)
        
        # Check for existing models
        for path in self.model_paths:
            if os.path.exists(path):
                logger.info(f"Found model directory: {path}")
                files = os.listdir(path)
                if files:
                    logger.info(f"Model files: {files}")
                    self.model_found = True
                    break
        
        if not self.model_found:
            logger.warning("No model files found in expected locations")
                
        # Enhanced model registry with HuggingFace models + VADER fallback
        self.available_models = {
            "vader": {
                "name": "NLTK VADER Sentiment",
                "model_name": "vader_lexicon",
                "description": "Fast rule-based sentiment analyzer (no download required)",
                "size": "tiny",
                "speed": "very_fast",
                "accuracy": "good",
                "languages": ["en"],
                "use_case": "general_fast",
                "memory_mb": 1,
                "hf_model_id": None,
                "author": "NLTK/Georgetown",
                "license": "apache-2.0",
                "tags": ["sentiment-analysis", "rule-based", "fast"],
                "pipeline_task": "sentiment-analysis",
                "is_fallback": True,
                "requires_download": False
            },
            "distilbert-sentiment": {
                "name": "DistilBERT Sentiment",
                "model_name": "distilbert-base-uncased-finetuned-sst-2-english",
                "description": "Fast and efficient sentiment analysis",
                "size": "small",
                "speed": "fast",
                "accuracy": "good",
                "languages": ["en"],
                "use_case": "general",
                "memory_mb": 250,
                "hf_model_id": "distilbert-base-uncased-finetuned-sst-2-english",
                "author": "Hugging Face",
                "license": "apache-2.0",
                "tags": ["sentiment-analysis", "pytorch", "distilbert"],
                "pipeline_task": "sentiment-analysis",
                "is_fallback": False,
                "requires_download": True
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
                "memory_mb": 500,
                "hf_model_id": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                "author": "CardiffNLP",
                "license": "mit",
                "tags": ["sentiment-analysis", "twitter", "roberta"],
                "pipeline_task": "sentiment-analysis",
                "is_fallback": False,
                "requires_download": True
            },
            "bert-multilingual": {
                "name": "BERT Multilingual Sentiment",
                "model_name": "nlptown/bert-base-multilingual-uncased-sentiment",
                "description": "Multilingual sentiment analysis",
                "size": "large", 
                "speed": "slow",
                "accuracy": "excellent",
                "languages": ["en", "es", "fr", "de", "it", "pt"],
                "use_case": "multilingual",
                "memory_mb": 450,
                "hf_model_id": "nlptown/bert-base-multilingual-uncased-sentiment",
                "author": "NLPTown",
                "license": "mit",
                "tags": ["sentiment-analysis", "multilingual", "bert"],
                "pipeline_task": "sentiment-analysis",
                "is_fallback": False,
                "requires_download": True
            },
            "finbert-sentiment": {
                "name": "FinBERT Sentiment",
                "model_name": "ProsusAI/finbert",
                "description": "Financial sentiment analysis",
                "size": "medium",
                "speed": "medium", 
                "accuracy": "excellent",
                "languages": ["en"],
                "use_case": "financial",
                "memory_mb": 400,
                "hf_model_id": "ProsusAI/finbert",
                "author": "ProsusAI",
                "license": "cc-by-4.0",
                "tags": ["sentiment-analysis", "financial", "bert"],
                "pipeline_task": "sentiment-analysis",
                "is_fallback": False,
                "requires_download": True
            }
        }
        
        # Performance tracking
        self.prediction_count = 0
        self.total_prediction_time = 0.0
        self.last_prediction_time = None
        self.download_history = {}
        
        # Health status
        self.health_status = {
            "initialized": False,
            "models_loaded": 0,
            "models_downloaded": 0,
            "last_error": None,
            "memory_usage": 0,
            "torch_available": TORCH_AVAILABLE,
            "hf_available": HF_AVAILABLE,
            "vader_available": VADER_AVAILABLE
        }
        
        # Initialize VADER if available
        self.vader_analyzer = None
        if VADER_AVAILABLE:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                logger.info("✅ NLTK VADER sentiment analyzer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize VADER: {e}")
                self.vader_analyzer = None
    
    async def initialize(self):
        """Initialize the model manager"""
        try:
            logger.info("Initializing enhanced model manager...")
            
            if TORCH_AVAILABLE:
                # Set device (CPU for lightweight deployment)
                self.device = torch.device("cpu")
                
                # Initialize locks for each model
                for model_key in self.available_models.keys():
                    self.loading_locks[model_key] = asyncio.Lock()
                    
                logger.info("✅ PyTorch models support initialized")
            else:
                logger.warning("PyTorch not available - using VADER fallback only")
            
            # Ensure VADER is always available as fallback
            if VADER_AVAILABLE and self.vader_analyzer is None:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                logger.info("✅ VADER fallback initialized")
            
            self.health_status["initialized"] = True
            logger.info("✅ Enhanced model manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize model manager: {e}")
            self.health_status["last_error"] = str(e)
            raise
    
    async def get_hf_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get model information from HuggingFace Hub"""
        if not HF_AVAILABLE:
            raise Exception("HuggingFace Hub not available")
        
        try:
            logger.info(f"Fetching model info from HuggingFace: {model_id}")
            
            # Get model info from HuggingFace
            info = model_info(model_id)
            
            # Extract relevant information
            hf_info = {
                "model_id": model_id,
                "author": info.author if hasattr(info, 'author') else "Unknown",
                "downloads": info.downloads if hasattr(info, 'downloads') else 0,
                "likes": info.likes if hasattr(info, 'likes') else 0,
                "library_name": info.library_name if hasattr(info, 'library_name') else "transformers",
                "tags": info.tags if hasattr(info, 'tags') else [],
                "pipeline_tag": info.pipeline_tag if hasattr(info, 'pipeline_tag') else None,
                "created_at": info.created_at.isoformat() if hasattr(info, 'created_at') and info.created_at else None,
                "last_modified": info.last_modified.isoformat() if hasattr(info, 'last_modified') and info.last_modified else None,
                "model_size": getattr(info, 'safetensors', {}).get('total', 0) if hasattr(info, 'safetensors') else 0
            }
            
            return hf_info
            
        except Exception as e:
            logger.error(f"Failed to get HuggingFace model info for {model_id}: {e}")
            return {"error": str(e)}
    
    async def download_from_huggingface(self, model_key: str, force_download: bool = False) -> Dict[str, Any]:
        """Download model from HuggingFace Hub"""
        if not HF_AVAILABLE:
            raise Exception("HuggingFace Hub not available")
        
        if model_key not in self.available_models:
            raise ValueError(f"Unknown model: {model_key}")
        
        model_info = self.available_models[model_key]
        hf_model_id = model_info["hf_model_id"]
        
        try:
            logger.info(f"Downloading model from HuggingFace: {hf_model_id}")
            start_time = time.time()
            
            # Create model-specific cache directory
            model_cache_dir = os.path.join(self.cache_dir, model_key)
            
            # Download model files
            downloaded_path = snapshot_download(
                repo_id=hf_model_id,
                cache_dir=model_cache_dir,
                force_download=force_download,
                local_files_only=False
            )
            
            download_time = time.time() - start_time
            
            # Get additional model info from HuggingFace
            hf_info = await self.get_hf_model_info(hf_model_id)
            
            # Update download history
            self.download_history[model_key] = {
                "downloaded_at": datetime.now(timezone.utc),
                "download_time": download_time,
                "path": downloaded_path,
                "hf_info": hf_info,
                "force_download": force_download
            }
            
            self.health_status["models_downloaded"] += 1
            
            logger.info(f"✅ Model {model_key} downloaded successfully in {download_time:.2f}s")
            
            return {
                "model_key": model_key,
                "hf_model_id": hf_model_id,
                "status": "downloaded",
                "download_time": download_time,
                "path": downloaded_path,
                "size_mb": hf_info.get("model_size", 0) / (1024 * 1024) if hf_info.get("model_size") else None,
                "hf_info": hf_info
            }
            
        except Exception as e:
            error_msg = f"Failed to download model {model_key} from HuggingFace: {e}"
            logger.error(error_msg)
            self.health_status["last_error"] = error_msg
            raise Exception(error_msg)
    
    async def predict_with_vader(self, text: str) -> Dict[str, Any]:
        """Fast sentiment prediction using NLTK VADER"""
        if not VADER_AVAILABLE or self.vader_analyzer is None:
            raise Exception("VADER sentiment analyzer not available")
        
        start_time = time.time()
        
        try:
            # Get VADER scores
            scores = self.vader_analyzer.polarity_scores(text)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Determine sentiment based on compound score
            compound = scores['compound']
            if compound >= 0.05:
                sentiment = 'positive'
                confidence = abs(compound)
            elif compound <= -0.05:
                sentiment = 'negative'
                confidence = abs(compound)
            else:
                sentiment = 'neutral'
                confidence = 1 - abs(compound)
            
            # Normalize confidence to 0-1 range
            confidence = min(1.0, max(0.0, confidence))
            
            # Create probabilities from VADER scores
            probabilities = {
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu']
            }
            
            # Update metrics
            self.prediction_count += 1
            self.total_prediction_time += processing_time
            self.last_prediction_time = datetime.now(timezone.utc)
            
            result = {
                "sentiment": sentiment,
                "confidence": round(confidence, 4),
                "compound_score": round(compound, 4),
                "probabilities": probabilities,
                "text_length": len(text),
                "model_used": "vader",
                "model_name": "NLTK VADER Sentiment",
                "hf_model_id": None,
                "processing_time_ms": round(processing_time, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "vader_scores": scores  # Include raw VADER scores
            }
            
            logger.debug(f"VADER prediction: {sentiment} (compound: {compound:.3f}, {processing_time:.1f}ms)")
            return result
            
        except Exception as e:
            error_msg = f"VADER prediction failed: {e}"
            logger.error(error_msg)
            self.health_status["last_error"] = error_msg
            raise Exception(error_msg)

    async def load_model(self, model_key: str, auto_download: bool = True) -> bool:
        """Load a specific model (with async locking and auto-download)"""
        # Handle VADER separately - no loading required
        if model_key == "vader":
            if VADER_AVAILABLE and self.vader_analyzer is not None:
                logger.debug("VADER analyzer already available")
                return True
            else:
                raise Exception("VADER sentiment analyzer not available")
        
        if not TORCH_AVAILABLE:
            raise Exception("PyTorch/Transformers not available for non-VADER models")
        
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
                hf_model_id = model_info["hf_model_id"]
                
                logger.info(f"Loading model: {model_key} ({hf_model_id})")
                start_time = time.time()
                
                # Try to load from cache first, download if needed
                try:
                    tokenizer = AutoTokenizer.from_pretrained(hf_model_id, local_files_only=not auto_download)
                    model = AutoModelForSequenceClassification.from_pretrained(hf_model_id, local_files_only=not auto_download)
                except Exception as cache_error:
                    if auto_download:
                        logger.info(f"Model not in cache, downloading: {model_key}")
                        await self.download_from_huggingface(model_key)
                        tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
                        model = AutoModelForSequenceClassification.from_pretrained(hf_model_id)
                    else:
                        raise cache_error
                
                model.to(self.device)
                model.eval()  # Set to evaluation mode
                
                # Create pipeline for easy inference
                classifier = pipeline(
                    model_info["pipeline_task"],
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
                    "prediction_count": 0,
                    "hf_model_id": hf_model_id
                }
                
                self.model_metadata[model_key] = {
                    **model_info,
                    "loaded": True,
                    "load_time": load_time,
                    "loaded_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.health_status["models_loaded"] += 1
                
                logger.info(f"✅ Model {model_key} loaded successfully in {load_time:.2f}s")
                return True
                
            except Exception as e:
                error_msg = f"Failed to load model {model_key}: {e}"
                logger.error(error_msg)
                self.health_status["last_error"] = error_msg
                raise Exception(error_msg)
    
    async def predict_sentiment_async(self, text: str, model_key: str = None) -> Dict[str, Any]:
        """Predict sentiment asynchronously with smart fallback to VADER"""
        
        # Smart model selection logic
        if model_key is None:
            model_key = self.get_recommended_model()
        
        # If requested model is VADER or fallback conditions met, use VADER
        if (model_key == "vader" or 
            (not TORCH_AVAILABLE and VADER_AVAILABLE) or
            (model_key != "vader" and not TORCH_AVAILABLE)):
            
            logger.debug(f"Using VADER fallback (requested: {model_key}, torch: {TORCH_AVAILABLE})")
            return await self.predict_with_vader(text)
        
        # Try to use requested HuggingFace model with VADER fallback
        try:
            # Ensure model is loaded
            await self.load_model(model_key)
            
            start_time = time.time()
            
            model_info = self.loaded_models[model_key]
            classifier = model_info["classifier"]
            
            # Run prediction
            results = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: classifier(text)
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Process results
            scores = results[0] if isinstance(results, list) else results
            
            # Convert to standard format
            sentiment_map = {
                'POSITIVE': 'positive',
                'NEGATIVE': 'negative', 
                'NEUTRAL': 'neutral',
                'LABEL_0': 'negative',  # Some models use LABEL_X format
                'LABEL_1': 'positive',
                'LABEL_2': 'neutral'
            }
            
            # Find highest scoring label
            if isinstance(scores, list):
                best_result = max(scores, key=lambda x: x['score'])
                sentiment = sentiment_map.get(best_result['label'].upper(), best_result['label'].lower())
                confidence = best_result['score']
                
                # Create probabilities dict
                probabilities = {
                    sentiment_map.get(s['label'].upper(), s['label'].lower()): s['score'] 
                    for s in scores
                }
            else:
                # Single result format
                sentiment = sentiment_map.get(scores['label'].upper(), scores['label'].lower())
                confidence = scores['score']
                probabilities = {sentiment: confidence}
            
            # Calculate compound score
            pos_score = probabilities.get('positive', 0)
            neg_score = probabilities.get('negative', 0)
            compound_score = pos_score - neg_score
            
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
                "hf_model_id": model_info["hf_model_id"],
                "processing_time_ms": round(processing_time, 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.debug(f"HF prediction: {sentiment} (conf: {confidence:.3f}, {processing_time:.1f}ms)")
            return result
            
        except Exception as e:
            # Fallback to VADER if HuggingFace model fails
            if VADER_AVAILABLE:
                logger.warning(f"HuggingFace model {model_key} failed, falling back to VADER: {e}")
                return await self.predict_with_vader(text)
            else:
                error_msg = f"Prediction failed for model {model_key} and VADER not available: {e}"
                logger.error(error_msg)
                self.health_status["last_error"] = error_msg
                raise Exception(error_msg)
    
    def predict_sentiment(self, text: str, model_key: str = None) -> Dict[str, Any]:
        """Synchronous wrapper for backward compatibility"""
        return asyncio.run(self.predict_sentiment_async(text, model_key))

    async def download_from_huggingface(self, model_key: str, force_download: bool = False) -> Dict[str, Any]:
        """Download model from HuggingFace Hub"""
        if model_key == "vader":
            # VADER doesn't need downloading
            return {
                "model_key": model_key,
                "status": "already_available",
                "message": "VADER is built-in and doesn't require downloading"
            }
        
        if not HF_AVAILABLE:
            raise Exception("HuggingFace Hub not available")
        
        if model_key not in self.available_models:
            raise ValueError(f"Unknown model: {model_key}")
        
        model_info = self.available_models[model_key]
        hf_model_id = model_info["hf_model_id"]
        
        if not hf_model_id:
            raise ValueError(f"Model {model_key} doesn't have HuggingFace model ID")
        
        try:
            logger.info(f"Downloading model from HuggingFace: {hf_model_id}")
            start_time = time.time()
            
            # Create model-specific cache directory
            model_cache_dir = os.path.join(self.cache_dir, model_key)
            
            # Download model files
            downloaded_path = snapshot_download(
                repo_id=hf_model_id,
                cache_dir=model_cache_dir,
                force_download=force_download,
                local_files_only=False
            )
            
            download_time = time.time() - start_time
            
            # Get additional model info from HuggingFace
            hf_info = await self.get_hf_model_info(hf_model_id)
            
            # Update download history
            self.download_history[model_key] = {
                "downloaded_at": datetime.now(timezone.utc),
                "download_time": download_time,
                "path": downloaded_path,
                "hf_info": hf_info,
                "force_download": force_download
            }
            
            self.health_status["models_downloaded"] += 1
            
            logger.info(f"✅ Model {model_key} downloaded successfully in {download_time:.2f}s")
            
            return {
                "model_key": model_key,
                "hf_model_id": hf_model_id,
                "status": "downloaded",
                "download_time": download_time,
                "path": downloaded_path,
                "size_mb": hf_info.get("model_size", 0) / (1024 * 1024) if hf_info.get("model_size") else None,
                "hf_info": hf_info
            }
            
        except Exception as e:
            error_msg = f"Failed to download model {model_key} from HuggingFace: {e}"
            logger.error(error_msg)
            self.health_status["last_error"] = error_msg
            raise Exception(error_msg)
    
    async def list_available_models_async(self) -> Dict[str, Any]:
        """List all available models with comprehensive metadata"""
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
            
            # Add download information
            if key in self.download_history:
                download_info = self.download_history[key]
                model_data.update({
                    "downloaded": True,
                    "downloaded_at": download_info["downloaded_at"].isoformat(),
                    "download_time": download_info["download_time"],
                    "local_path": download_info["path"]
                })
            else:
                model_data["downloaded"] = False
            
            models[key] = model_data
        
        return {
            "available_models": models,
            "total_models": len(models),
            "loaded_models": len(self.loaded_models),
            "downloaded_models": len(self.download_history),
            "recommended_model": self.get_recommended_model()
        }
    
    def list_available_models(self) -> Dict[str, Any]:
        """Synchronous wrapper"""
        return asyncio.run(self.list_available_models_async())
    
    async def get_model_info_async(self, model_key: str) -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        if model_key not in self.available_models:
            raise ValueError(f"Unknown model: {model_key}")
        
        model_info = self.available_models[model_key].copy()
        
        # Add runtime information
        if model_key in self.loaded_models:
            load_info = self.loaded_models[model_key]
            model_info.update({
                "status": "loaded",
                "loaded_at": load_info["loaded_at"].isoformat(),
                "load_time": load_info["load_time"],
                "prediction_count": load_info["prediction_count"]
            })
        else:
            model_info["status"] = "available"
        
        # Add download information
        if model_key in self.download_history:
            download_info = self.download_history[model_key]
            model_info.update({
                "downloaded": True,
                "downloaded_at": download_info["downloaded_at"].isoformat(),
                "download_time": download_info["download_time"],
                "local_path": download_info["path"],
                "hf_info": download_info["hf_info"]
            })
        else:
            model_info["downloaded"] = False
            # Get live HuggingFace info
            if HF_AVAILABLE:
                try:
                    hf_info = await self.get_hf_model_info(model_info["hf_model_id"])
                    model_info["hf_info"] = hf_info
                except:
                    pass
        
        return model_info
    
    def get_model_info(self, model_key: str) -> Dict[str, Any]:
        """Synchronous wrapper"""
        return asyncio.run(self.get_model_info_async(model_key))
    
    def get_recommended_model(self) -> str:
        """Get the recommended model based on availability"""
        # If we have loaded HuggingFace models, prefer distilbert
        if self.loaded_models and "distilbert-sentiment" in self.loaded_models:
            return "distilbert-sentiment"
        
        # If PyTorch is available, recommend distilbert for download
        if TORCH_AVAILABLE:
            return "distilbert-sentiment"
        
        # Fallback to VADER if PyTorch not available
        if VADER_AVAILABLE:
            return "vader"
        
        # Last resort
        return "distilbert-sentiment"
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status"""
        # Calculate memory usage (simplified)
        memory_usage = len(self.loaded_models) * 300  # Rough estimate
        
        avg_prediction_time = (
            self.total_prediction_time / self.prediction_count
            if self.prediction_count > 0 else 0
        )
        
        return {
            **self.health_status,
            "models_available": len(self.available_models),
            "models_loaded": len(self.loaded_models),
            "models_downloaded": len(self.download_history),
            "total_predictions": self.prediction_count,
            "avg_prediction_time_ms": round(avg_prediction_time, 2),
            "last_prediction": self.last_prediction_time.isoformat() if self.last_prediction_time else None,
            "memory_usage_mb": memory_usage,
            "device": str(self.device) if hasattr(self, 'device') else "cpu",
            "cache_dir": self.cache_dir,
            "model_found_locally": self.model_found,
            "fallback_available": VADER_AVAILABLE,
            "recommended_model": self.get_recommended_model()
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
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("✅ Model cache cleared")
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up model manager...")
        await self.clear_cache()
        logger.info("✅ Model manager cleanup complete")

# Global instance for easy access
lightweight_model_manager = LightweightModelManager()