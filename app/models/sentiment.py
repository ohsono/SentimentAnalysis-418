from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class SentimentRequest(BaseModel):
    """
    What this does:
    - Defines the structure for incoming sentiment analysis requests
    - Validates that text is between 1-5000 characters
    - Allows optional inclusion of probability scores
    
    Example usage:
    POST /predict with body: {"text": "UCLA is amazing!", "include_probabilities": true}
    """
    text: str = Field(..., min_length=1, max_length=5000)
    include_probabilities: bool = Field(default=True)

class SentimentResult(BaseModel):
    """
    What this does:
    - Standardizes the format of sentiment analysis results
    - Ensures all responses have the same structure
    - Makes it easy for dashboard and API consumers to use data
    
    Example result:
    {
        "text": "UCLA is amazing!",
        "sentiment": "positive",
        "confidence": 0.85,
        "compound_score": 0.7,
        "probabilities": {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
        "processing_time_ms": 45.2,
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """

    text: str
    sentiment: str  # positive, negative, neutral
    confidence: float
    compound_score: float
    probabilities: Optional[Dict[str, float]] = None
    processing_time_ms: float
    timestamp: datetime
    emoji_score: Optional[float] = None
    category: Optional[str] = None
