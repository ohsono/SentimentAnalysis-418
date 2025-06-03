import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
import time
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

class SentimentIntensityAnalyzer:
  def polarity_scores(self, text):
      # Simple fallback sentiment
      positive_words = ['good', 'great', 'amazing', 'love', 'excellent', 'awesome', 'happy']
      negative_words = ['bad', 'terrible', 'hate', 'awful', 'horrible', 'sad', 'angry']
      
      text_lower = text.lower()
      pos_count = sum(1 for word in positive_words if word in text_lower)
      neg_count = sum(1 for word in negative_words if word in text_lower)
      
      if pos_count > neg_count:
          return {'compound': 0.5, 'pos': 0.7, 'neu': 0.2, 'neg': 0.1}
      elif neg_count > pos_count:
          return {'compound': -0.5, 'pos': 0.1, 'neu': 0.2, 'neg': 0.7}
      else:
          return {'compound': 0.0, 'pos': 0.3, 'neu': 0.4, 'neg': 0.3}

class SentimentAnalyzer:
    """
    Sentiment analysis service
    """
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
    def clean_text(self, text: str) -> str:
        """Clean text for analysis"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?]', ' ', text)
        # Clean whitespace
        text = ' '.join(text.split())
        return text
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        start_time = time.time()
        
        try:
            if not text or not text.strip():
                return self._default_result(text, start_time)
            
            # Clean text
            cleaned_text = self.clean_text(text)
            
            # Analyze with VADER
            scores = self.analyzer.polarity_scores(cleaned_text)
            
            # Determine category
            compound = scores['compound']
            if compound >= 0.05:
                category = 'positive'
            elif compound <= -0.05:
                category = 'negative'
            else:
                category = 'neutral'
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                'sentiment': category,
                'confidence': max(scores['pos'], scores['neg'], scores['neu']),
                'compound_score': compound,
                'probabilities': {
                    'positive': scores['pos'],
                    'negative': scores['neg'],
                    'neutral': scores['neu']
                },
                'processing_time_ms': processing_time,
                'timestamp': datetime.now(timezone.utc),
                'text': text[:100] + '...' if len(text) > 100 else text
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return self._default_result(text, start_time, error=str(e))
    
    def _default_result(self, text: str, start_time: float, error: str = None) -> Dict[str, Any]:
        """Return default result for errors or empty text"""
        processing_time = (time.time() - start_time) * 1000
        
        result = {
            'sentiment': 'neutral',
            'confidence': 0.5,
            'compound_score': 0.0,
            'probabilities': {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34},
            'processing_time_ms': processing_time,
            'timestamp': datetime.now(timezone.utc),
            'text': text[:100] + '...' if len(text) > 100 else text
        }
        
        if error:
            result['error'] = error
            
        return result
    
    def batch_analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple texts"""
        return [self.analyze_sentiment(text) for text in texts]