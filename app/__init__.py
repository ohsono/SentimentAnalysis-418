#!/usr/bin/env python3

"""
UCLA Sentiment Analysis API Module
Enhanced with failsafe features and PostgreSQL integration
"""

__version__ = "2.0.0"
__title__ = "UCLA Sentiment Analysis API"
__description__ = "Enhanced sentiment analysis API with robust failsafe mechanisms"
__author__ = "UCLA MASDS Team"

from .api.main_enhanced import app
#from .api.failsafe_llm_client import FailsafeLLMClient
from .api.simple_sentiment_analyzer import SimpleSentimentAnalyzer
from .database.postgres_manager_enhanced import DatabaseManager, AsyncDataLoader

__all__ = [
    "app",
#    "FailsafeLLMClient", 
    "SimpleSentimentAnalyzer",
    "DatabaseManager",
    "AsyncDataLoader"
]
