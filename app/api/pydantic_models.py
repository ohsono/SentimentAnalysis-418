from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import os
import time
# ============================================
# PYDANTIC MODELS
# ============================================

class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    include_probabilities: bool = Field(default=True, description="Include probability scores")

class LLMSentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze with ML model")
    model: str = Field(default="twitter-roberta", description="Model to use (twitter-roberta, distilbert-sst2)")
    include_probabilities: bool = Field(default=True, description="Include probability scores")

class LLMBatchRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to analyze")
    model: str = Field(default="twitter-roberta", description="Model to use")

class ModelDownloadRequest(BaseModel):
    model: str = Field(..., description="Model key to download")

class ScrapeRequest(BaseModel):
    subreddit: str = Field(default="UCLA", description="Subreddit to scrape")
    post_limit: int = Field(default=10, ge=1, le=50, description="Number of posts to retrieve")

class AlertStatusUpdate(BaseModel):
    status: str = Field(..., description="New status for the alert")
    notes: Optional[str] = Field(None, description="Optional notes")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float
    compound_score: float
    probabilities: Optional[Dict[str, float]] = None
    processing_time_ms: float
    timestamp: str