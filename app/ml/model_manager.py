#!/usr/bin/env python3

"""
Hugging Face Model Manager for UCLA Sentiment Analysis
Handles downloading, caching, and inference for pre-trained sentiment models
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

try:
    import torch
    from transformers import (
        AutoTokenizer, 
        AutoModelForSequenceClassification,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️  Transformers not available. Install with: pip install torch transformers")

logger = logging.getLogger(__name__)

class HuggingFaceModelManager:
    """
    Manages Hugging Face models for sentiment analysis
    Downloads, caches, and provides inference capabilities
    """
    
    def __init__(self, model_cache_dir: str = "data/models/huggingface"):
        self.model_cache_dir = Path(model_cache_dir)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Default model configuration
        self.default_model = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.model_configs = {
            "twitter-roberta": {
                "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                "description": "RoBERTa model trained on Twitter data for sentiment analysis",
                "labels": ["negative", "neutral", "positive"],
                "preprocessing": self._preprocess_tweet_text
            }
            # },
            # "distilbert-sst2": {
            #     "model_name": "distilbert-base-uncased-finetuned-sst-2-english", 
            #     "description": "DistilBERT fine-tuned on Stanford Sentiment Treebank",
            #     "labels": ["negative", "positive"],
            #     "preprocessing": self._preprocess_standard_text
            # }
        }
        
        # Initialize models storage
        self.loaded_models: Dict[str, Any] = {}
        self.model_info: Dict[str, Dict] = {}
        
    def is_available(self) -> bool:
        """Check if transformers is available"""
        return TRANSFORMERS_AVAILABLE
    
    def list_available_models(self) -> Dict[str, Dict]:
        """List all available model configurations"""
        return {
            name: {
                "model_name": config["model_name"],
                "description": config["description"],
                "labels": config["labels"],
                "downloaded": self._is_model_downloaded(name),
                "loaded": name in self.loaded_models
            }
            for name, config in self.model_configs.items()
        }
    
    def download_model(self, model_key: str = "twitter-roberta") -> Dict[str, Any]:
        """Download and cache a model"""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library not available")
        
        if model_key not in self.model_configs:
            raise ValueError(f"Unknown model key: {model_key}")
        
        config = self.model_configs[model_key]
        model_name = config["model_name"]
        cache_path = self.model_cache_dir / model_key
        
        logger.info(f"Downloading model: {model_name}")
        start_time = time.time()
        
        try:
            # Download tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(cache_path / "tokenizer")
            )
            
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                cache_dir=str(cache_path / "model")
            )
            
            download_time = time.time() - start_time
            
            # Save model info
            model_info = {
                "model_key": model_key,
                "model_name": model_name,
                "description": config["description"],
                "labels": config["labels"],
                "download_time": download_time,
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "cache_path": str(cache_path),
                "model_size_mb": self._get_model_size(cache_path)
            }
            
            # Save metadata
            with open(cache_path / "model_info.json", "w") as f:
                json.dump(model_info, f, indent=2)
            
            self.model_info[model_key] = model_info
            
            logger.info(f"Model downloaded successfully in {download_time:.2f}s")
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to download model {model_name}: {e}")
            raise
    
    def load_model(self, model_key: str = "twitter-roberta") -> bool:
        """Load a model into memory for inference"""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library not available")
        
        if model_key in self.loaded_models:
            logger.info(f"Model {model_key} already loaded")
            return True
        
        if not self._is_model_downloaded(model_key):
            logger.info(f"Model {model_key} not found, downloading...")
            self.download_model(model_key)
        
        config = self.model_configs[model_key]
        model_name = config["model_name"]
        cache_path = self.model_cache_dir / model_key
        
        try:
            logger.info(f"Loading model: {model_key}")
            start_time = time.time()
            
            # Create pipeline for easy inference
            sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=str(cache_path / "model"),
                tokenizer=str(cache_path / "tokenizer"),
                device=0 if torch.cuda.is_available() else -1,
                return_all_scores=True
            )
            
            load_time = time.time() - start_time
            
            self.loaded_models[model_key] = {
                "pipeline": sentiment_pipeline,
                "config": config,
                "loaded_at": datetime.now(timezone.utc).isoformat(),
                "load_time": load_time
            }
            
            logger.info(f"Model {model_key} loaded successfully in {load_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_key}: {e}")
            raise
    
    def predict_sentiment(self, text: str, model_key: str = "twitter-roberta") -> Dict[str, Any]:
        """Predict sentiment using specified model"""
        if not TRANSFORMERS_AVAILABLE:
            return self._fallback_prediction(text)
        
        # Ensure model is loaded
        if model_key not in self.loaded_models:
            self.load_model(model_key)
        
        model_info = self.loaded_models[model_key]
        pipeline_obj = model_info["pipeline"]
        config = model_info["config"]
        
        start_time = time.time()
        
        try:
            # Preprocess text
            processed_text = config["preprocessing"](text)
            
            # Get predictions
            results = pipeline_obj(processed_text)
            processing_time = (time.time() - start_time) * 1000
            
            # Parse results
            scores = results[0] if isinstance(results[0], list) else results
            
            # Find best prediction
            best_prediction = max(scores, key=lambda x: x['score'])
            sentiment = best_prediction['label'].lower()
            confidence = best_prediction['score']
            
            # Create probability distribution
            probabilities = {}
            for score_obj in scores:
                label = score_obj['label'].lower()
                probabilities[label] = round(score_obj['score'], 3)
            
            # Map labels to standard format
            sentiment_mapping = {
                'label_0': 'negative', 'label_1': 'neutral', 'label_2': 'positive',
                'negative': 'negative', 'neutral': 'neutral', 'positive': 'positive'
            }
            sentiment = sentiment_mapping.get(sentiment, sentiment)
            
            # Calculate compound score (simplified)
            if sentiment == 'positive':
                compound_score = confidence
            elif sentiment == 'negative':
                compound_score = -confidence
            else:
                compound_score = 0.0
            
            return {
                'text': text[:100] + '...' if len(text) > 100 else text,
                'sentiment': sentiment,
                'confidence': round(confidence, 3),
                'compound_score': round(compound_score, 3),
                'probabilities': probabilities,
                'processing_time_ms': round(processing_time, 2),
                'model_used': model_key,
                'model_name': config["model_name"],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return self._fallback_prediction(text, error=str(e))
    
    def predict_batch(self, texts: List[str], model_key: str = "twitter-roberta") -> Dict[str, Any]:
        """Predict sentiment for multiple texts"""
        if not TRANSFORMERS_AVAILABLE:
            return self._fallback_batch_prediction(texts)
        
        start_time = time.time()
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = self.predict_sentiment(text, model_key)
                result['batch_index'] = i
                results.append(result)
            except Exception as e:
                results.append({
                    'batch_index': i,
                    'text': text[:100] + '...' if len(text) > 100 else text,
                    'error': str(e),
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'model_used': model_key
                })
        
        total_time = (time.time() - start_time) * 1000
        
        # Calculate summary
        successful_results = [r for r in results if 'error' not in r]
        sentiments = [r['sentiment'] for r in successful_results]
        
        return {
            "results": results,
            "summary": {
                "total_processed": len(results),
                "successful": len(successful_results),
                "failed": len(results) - len(successful_results),
                "total_processing_time_ms": round(total_time, 2),
                "average_time_per_text_ms": round(total_time / len(texts), 2),
                "model_used": model_key,
                "sentiment_distribution": {
                    "positive": sentiments.count('positive'),
                    "negative": sentiments.count('negative'),
                    "neutral": sentiments.count('neutral')
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_model_info(self, model_key: str = None) -> Dict[str, Any]:
        """Get information about loaded models"""
        if model_key:
            if model_key in self.loaded_models:
                return {
                    "loaded": True,
                    "info": self.loaded_models[model_key],
                    "config": self.model_configs[model_key]
                }
            else:
                return {"loaded": False, "available": model_key in self.model_configs}
        else:
            return {
                "available_models": self.list_available_models(),
                "loaded_models": list(self.loaded_models.keys()),
                "transformers_available": TRANSFORMERS_AVAILABLE,
                "default_model": self.default_model
            }
    
    def _is_model_downloaded(self, model_key: str) -> bool:
        """Check if model is downloaded"""
        cache_path = self.model_cache_dir / model_key
        return (cache_path / "model_info.json").exists()
    
    def _get_model_size(self, path: Path) -> float:
        """Calculate model size in MB"""
        try:
            total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0
    
    def _preprocess_tweet_text(self, text: str) -> str:
        """Preprocess text for Twitter-trained models"""
        # Remove URLs
        import re
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Normalize mentions and hashtags
        text = re.sub(r'@\w+', '@user', text)
        text = re.sub(r'#(\w+)', r'\1', text)
        return text.strip()
    
    def _preprocess_standard_text(self, text: str) -> str:
        """Standard text preprocessing"""
        import re
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _fallback_prediction(self, text: str, error: str = None) -> Dict[str, Any]:
        """Fallback prediction when ML model fails"""
        return {
            'text': text[:100] + '...' if len(text) > 100 else text,
            'sentiment': 'neutral',
            'confidence': 0.5,
            'compound_score': 0.0,
            'probabilities': {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33},
            'processing_time_ms': 1.0,
            'model_used': 'fallback',
            'model_name': 'Simple fallback',
            'error': error,
            'note': 'ML model unavailable, using fallback',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _fallback_batch_prediction(self, texts: List[str]) -> Dict[str, Any]:
        """Fallback batch prediction"""
        results = []
        for i, text in enumerate(texts):
            result = self._fallback_prediction(text)
            result['batch_index'] = i
            results.append(result)
        
        return {
            "results": results,
            "summary": {
                "total_processed": len(results),
                "successful": len(results),
                "failed": 0,
                "total_processing_time_ms": len(texts) * 1.0,
                "average_time_per_text_ms": 1.0,
                "model_used": "fallback",
                "sentiment_distribution": {
                    "positive": 0, "negative": 0, "neutral": len(texts)
                }
            },
            "note": "ML models unavailable, using fallback",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global model manager instance
model_manager = HuggingFaceModelManager()
