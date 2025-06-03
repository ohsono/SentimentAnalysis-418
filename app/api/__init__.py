#!/usr/bin/env python3

"""
UCLA Sentiment Analysis API Module
Enhanced main API with failsafe features
"""

from .main_enhanced import app
from .pydantic_models import SentimentRequest, LLMSentimentRequest, LLMBatchRequest, ModelDownloadRequest, ScrapeRequest, AlertStatusUpdate, HealthResponse, SentimentResponse
#from .failsafe_llm_client import FailsafeLLMClient
from .simple_sentiment_analyzer import SimpleSentimentAnalyzer
from .postgres_manager import DatabaseManager, AsyncDataLoader

__all__ = [
    "app",
    "SimpleSentimentAnalyzer",
    "SentimentRequest", 
    "LLMSentimentRequest", 
    "LLMBatchRequest", 
    "ModelDownloadRequest", 
    "ScrapeRequest", 
    "AlertStatusUpdate", 
    "HealthResponse", 
    "SentimentResponse",
    "DatabaseManager",
    "AsyncDataLoader"
]
