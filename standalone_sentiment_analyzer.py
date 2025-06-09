#!/usr/bin/env python3

"""
Standalone Sentiment Analyzer for Reddit Scraper
Works independently of the model service to avoid Docker permission issues
"""

import os
import time
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class StandaloneSentimentAnalyzer:
    """
    Standalone sentiment analyzer that works without external dependencies
    Uses VADER sentiment analysis with fallback to simple rule-based analysis
    """
    
    def __init__(self):
        self.vader_available = False
        self.vader_analyzer = None
        
        # Try to initialize VADER
        try:
            # Download VADER lexicon to a writable location
            import nltk
            import ssl
            
            # Handle SSL certificate issues
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context
            
            # Set custom NLTK data path to avoid permission issues
            nltk_data_path = os.path.expanduser('~/nltk_data')
            if not os.path.exists(nltk_data_path):
                os.makedirs(nltk_data_path, exist_ok=True)
            nltk.data.path.append(nltk_data_path)
            
            # Download VADER lexicon
            try:
                nltk.download('vader_lexicon', download_dir=nltk_data_path, quiet=True)
            except:
                # If download fails, try without specifying download_dir
                nltk.download('vader_lexicon', quiet=True)
            
            from nltk.sentiment import SentimentIntensityAnalyzer
            self.vader_analyzer = SentimentIntensityAnalyzer()
            self.vader_available = True
            print("✅ VADER sentiment analyzer initialized")
            
        except Exception as e:
            logger.warning(f"VADER not available: {e}")
            print("⚠️  VADER not available, using rule-based fallback")
            self.vader_available = False
        
        # Rule-based sentiment keywords
        self.positive_words = {
            'great', 'good', 'excellent', 'amazing', 'awesome', 'fantastic', 'wonderful',
            'love', 'like', 'happy', 'excited', 'perfect', 'best', 'brilliant', 'outstanding',
            'thrilled', 'delighted', 'pleased', 'satisfied', 'grateful', 'thankful',
            'success', 'achievement', 'win', 'victory', 'accomplish', 'proud'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry', 'frustrated',
            'disappointed', 'upset', 'sad', 'depressed', 'worried', 'anxious', 'stressed',
            'fail', 'failure', 'problem', 'issue', 'difficulty', 'struggle', 'concern',
            'worst', 'sucks', 'boring', 'annoying', 'irritating', 'useless'
        }
        
        self.neutral_words = {
            'okay', 'fine', 'normal', 'average', 'standard', 'typical', 'regular',
            'neutral', 'moderate', 'fair', 'decent', 'adequate'
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        start_time = time.time()
        
        if not text or not isinstance(text, str):
            return self._create_result('neutral', 0.5, 0.0, start_time)
        
        # Clean text
        clean_text = self._clean_text(text)
        
        if self.vader_available and self.vader_analyzer:
            try:
                # Use VADER analyzer
                scores = self.vader_analyzer.polarity_scores(clean_text)
                compound = scores['compound']
                
                # Convert compound score to sentiment label
                if compound >= 0.05:
                    sentiment = 'positive'
                    confidence = min(0.5 + (compound * 0.5), 1.0)
                elif compound <= -0.05:
                    sentiment = 'negative'
                    confidence = min(0.5 + (abs(compound) * 0.5), 1.0)
                else:
                    sentiment = 'neutral'
                    confidence = 0.5 + (0.5 - abs(compound))
                
                return self._create_result(sentiment, confidence, compound, start_time, 'vader')
                
            except Exception as e:
                logger.warning(f"VADER analysis failed: {e}")
        
        # Fallback to rule-based analysis
        return self._rule_based_analysis(clean_text, start_time)
    
    def _rule_based_analysis(self, text: str, start_time: float) -> Dict[str, Any]:
        """
        Simple rule-based sentiment analysis as fallback
        """
        words = text.lower().split()
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        neutral_count = sum(1 for word in words if word in self.neutral_words)
        
        # Calculate sentiment
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            sentiment = 'neutral'
            confidence = 0.5
            compound_score = 0.0
        else:
            positive_ratio = positive_count / total_sentiment_words
            negative_ratio = negative_count / total_sentiment_words
            
            if positive_ratio > negative_ratio:
                sentiment = 'positive'
                confidence = 0.5 + (positive_ratio * 0.3)
                compound_score = positive_ratio - negative_ratio
            elif negative_ratio > positive_ratio:
                sentiment = 'negative'
                confidence = 0.5 + (negative_ratio * 0.3)
                compound_score = -(negative_ratio - positive_ratio)
            else:
                sentiment = 'neutral'
                confidence = 0.5
                compound_score = 0.0
        
        return self._create_result(sentiment, confidence, compound_score, start_time, 'rule_based')
    
    def _clean_text(self, text: str) -> str:
        """Clean text for analysis"""
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?]', ' ', text)
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _create_result(self, sentiment: str, confidence: float, compound_score: float, 
                      start_time: float, source: str = 'fallback') -> Dict[str, Any]:
        """Create standardized result dictionary"""
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            'sentiment': sentiment,
            'confidence': max(0.0, min(1.0, confidence)),  # Clamp between 0 and 1
            'compound_score': max(-1.0, min(1.0, compound_score)),  # Clamp between -1 and 1
            'processing_time_ms': round(processing_time, 2),
            'model_used': 'vader' if source == 'vader' else 'rule_based',
            'model_name': 'VADER' if source == 'vader' else 'Rule-Based',
            'source': source,
            'probabilities': {
                'positive': max(0, compound_score) if source == 'vader' else (0.7 if sentiment == 'positive' else 0.3),
                'negative': abs(min(0, compound_score)) if source == 'vader' else (0.7 if sentiment == 'negative' else 0.3),
                'neutral': 1 - abs(compound_score) if source == 'vader' else (0.7 if sentiment == 'neutral' else 0.3)
            }
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple texts"""
        return [self.analyze(text) for text in texts]
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status"""
        return {
            'available': True,
            'vader_available': self.vader_available,
            'models': ['vader'] if self.vader_available else ['rule_based'],
            'fallback_available': True
        }

# Test the analyzer
if __name__ == "__main__":
    print("🧪 Testing Standalone Sentiment Analyzer")
    print("=" * 50)
    
    analyzer = StandaloneSentimentAnalyzer()
    
    # Test sentences
    test_texts = [
        "I love UCLA! It's an amazing university with great professors.",
        "I'm really stressed about my midterms. Everything is going wrong.",
        "The weather is okay today. Nothing special.",
        "UCLA's campus is beautiful and the students are friendly.",
        "I'm feeling overwhelmed with my coursework and assignments."
    ]
    
    print("📊 Test Results:")
    for i, text in enumerate(test_texts, 1):
        result = analyzer.analyze(text)
        print(f"\n{i}. Text: {text[:50]}...")
        print(f"   Sentiment: {result['sentiment']} (confidence: {result['confidence']:.2f})")
        print(f"   Compound Score: {result['compound_score']:.2f}")
        print(f"   Model: {result['model_name']}")
        print(f"   Processing Time: {result['processing_time_ms']:.2f}ms")
    
    print(f"\n🔧 Analyzer Status: {analyzer.get_status()}")
