import re
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    
    # Remove Reddit markdown
    text = re.sub(r'\*{1,3}([^*]*)\*{1,3}', r'\1', text)  # Bold/italic
    text = re.sub(r'_{1,3}([^_]*)_{1,3}', r'\1', text)    # Underline
    text = re.sub(r'`([^`]*)`', r'\1', text)              # Code
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)  # Links
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract keywords from text"""
    # Simple keyword extraction
    words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
        'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 
        'boy', 'did', 'man', 'end', 'why', 'let', 'put', 'say', 'she', 'too', 
        'use'
    }
    
    keywords = [word for word in words if word not in stop_words]
    return list(set(keywords))  # Remove duplicates

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object"""
    if dt is None:
        return "N/A"
    
    # Ensure timezone awareness
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime(format_str)

def calculate_sentiment_category(compound_score: float) -> str:
    """Calculate sentiment category from compound score"""
    if compound_score >= 0.05:
        return 'positive'
    elif compound_score <= -0.05:
        return 'negative'
    else:
        return 'neutral'

def generate_hash(text: str) -> str:
    """Generate hash for text"""
    return hashlib.md5(text.encode()).hexdigest()

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value for zero denominator"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

def validate_reddit_credentials() -> bool:
    """Validate Reddit API credentials"""
    import os
    
    required = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"Missing Reddit credentials: {missing}")
        return False
    
    return True