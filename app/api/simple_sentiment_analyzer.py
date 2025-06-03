from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import os
import time
import re


class SimpleSentimentAnalyzer:
    """
    Lightweight sentiment analyzer for fallback and fast processing
    """
    def __init__(self):
        #initialize the words dictionary
        self.positive_words = {}
        self.negative_words = {}
        self.intensifiers   = {}
        self.negations      = {}
        # load sample words dictionary
        self.load_sample_words()
            
    def load_sample_words(self):
        """
        Load sample word lists for better accuracy
            postive_words = dictionary of postivie words
            negative_words = dictionary of negative words
            intensifiers = Intensity modifiers
            negations = Negation words
        """
        self.positive_words = {
            'amazing', 'awesome', 'excellent', 'fantastic', 'great', 'love', 'wonderful',
            'brilliant', 'outstanding', 'perfect', 'best', 'beautiful', 'incredible',
            'magnificent', 'superb', 'fabulous', 'good', 'nice', 'happy', 'excited',
            'thrilled', 'delighted', 'pleased', 'satisfied', 'proud', 'grateful',
            'optimistic', 'confident', 'successful', 'impressive', 'remarkable',
            'enjoyable', 'fun', 'interesting', 'helpful', 'valuable', 'useful'
        }
        
        self.negative_words = {
            'terrible', 'awful', 'horrible', 'hate', 'disgusting', 'pathetic',
            'useless', 'worst', 'bad', 'sad', 'angry', 'disappointed', 'frustrated',
            'annoyed', 'stressed', 'overwhelmed', 'depressed', 'worried', 'anxious',
            'upset', 'tired', 'exhausted', 'bored', 'confused', 'difficult',
            'hard', 'challenging', 'problematic', 'concerning', 'unfortunate',
            'unpleasant', 'boring', 'annoying', 'irritating', 'disturbing'
        }
        
        self.intensifiers = {
            'very': 1.3, 'really': 1.3, 'extremely': 1.5, 'incredibly': 1.4,
            'absolutely': 1.4, 'completely': 1.3, 'totally': 1.3, 'so': 1.2,
            'quite': 1.1, 'rather': 1.1, 'pretty': 1.1, 'fairly': 1.0,
            'somewhat': 0.8, 'slightly': 0.7, 'barely': 0.6, 'hardly': 0.5
        }
        
        self.negations = {
            'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither',
            'nowhere', 'hardly', 'scarcely', 'barely', "don't", "doesn't",
            "didn't", "won't", "wouldn't", "shouldn't", "couldn't", "can't"
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess text based on regex rules.
        """
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s!?.,-]', '', text)
        return text.lower()
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        """
        start_time = time.time()
        
        # Clean text
        original_text = text
        cleaned_text = self.clean_text(text)
        words = cleaned_text.split()
        
        if not words:
            return self._create_response(original_text, 'neutral', 0.5, 0.0, start_time)
        
        # Analyze sentiment with context
        positive_score = 0
        negative_score = 0
        
        for i, word in enumerate(words):
            # Check for negation in previous 2 words
            negated = any(neg in words[max(0, i-2):i] for neg in self.negations)
            
            # Check for intensifiers in previous 2 words  
            intensity = 1.0
            for j in range(max(0, i-2), i):
                if words[j] in self.intensifiers:
                    intensity = self.intensifiers[words[j]]
                    break
            
            # Calculate sentiment contribution
            if word in self.positive_words:
                score = 1.0 * intensity
                if negated:
                    negative_score += score
                else:
                    positive_score += score
                    
            elif word in self.negative_words:
                score = 1.0 * intensity
                if negated:
                    positive_score += score
                else:
                    negative_score += score
        
        # Normalize scores
        total_score = positive_score + negative_score
        if total_score == 0:
            return self._create_response(original_text, 'neutral', 0.6, 0.0, start_time)
        
        # Calculate final sentiment
        net_score = positive_score - negative_score
        compound = net_score / max(total_score, 1.0)
        
        # Determine sentiment label and confidence
        if compound >= 0.1:
            sentiment = 'positive'
            confidence = min(0.6 + abs(compound) * 0.4, 0.95)
        elif compound <= -0.1:
            sentiment = 'negative' 
            confidence = min(0.6 + abs(compound) * 0.4, 0.95)
        else:
            sentiment = 'neutral'
            confidence = 0.6 + (0.4 * (1 - abs(compound)))
        
        return self._create_response(original_text, sentiment, confidence, compound, start_time)
    
    def _create_response(self, text: str, sentiment: str, confidence: float, compound: float, start_time: float) -> Dict[str, Any]:
        """
        Create standardized response
        """
        processing_time = (time.time() - start_time) * 1000
        
        # Calculate probabilities based on compound score
        if sentiment == 'positive':
            pos_prob = confidence
            neg_prob = (1 - confidence) * 0.3
            neu_prob = 1 - pos_prob - neg_prob
        elif sentiment == 'negative':
            neg_prob = confidence
            pos_prob = (1 - confidence) * 0.3
            neu_prob = 1 - pos_prob - neg_prob
        else:
            neu_prob = confidence
            pos_prob = neg_prob = (1 - confidence) / 2
        
        return {
            'text': text[:100] + '...' if len(text) > 100 else text,
            'sentiment': sentiment,
            'confidence': round(confidence, 3),
            'compound_score': round(compound, 3),
            'probabilities': {
                'positive': round(pos_prob, 3),
                'negative': round(neg_prob, 3),
                'neutral': round(neu_prob, 3)
            },
            'processing_time_ms': round(processing_time, 2),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }