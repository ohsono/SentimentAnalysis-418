import logging
from typing import Dict, List, Any
from datetime import datetime, timezone
import re

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Process and filter Reddit data
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.keyword_categories = self._load_categories()
        self.red_flag_keywords = self._load_red_flags()
        
    def _load_categories(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load keyword categories
        """
        return {
            'academic_departments': {
                'computer_science': ['computer science', 'cs', 'programming', 'code', 'coding'],
                'engineering': ['engineering', 'mechanical', 'electrical'],
                'business': ['business', 'finance', 'accounting'],
                'pre_med': ['pre med', 'premed', 'medical school', 'mcat']
            },
            'campus_life': {
                'housing': ['dorms', 'housing', 'roommate', 'hedrick', 'rieber'],
                'dining': ['dining', 'food', 'meal plan', 'bruin plate'],
                'events': ['events', 'party', 'social', 'club'],
                'mingle': ['date', 'boy friend', 'girl friend', 'hang out']
            },
            'sports': {
                'football': ['football', 'bruins football'],
                'basketball': ['basketball', 'march madness','pac 10', 'college basketball'],
                'baseball': ['baseball'],
                'e-sports': ['LOL', 'league of legends'],
                'general': ['athletics', 'sports', 'team', 'match', 'game']
            },
            'administrative': {
                'admissions': ['admissions', 'acceptance', 'application'],
                'financial_aid': ['financial aid', 'scholarship', 'tuition'],
                'academics': ['classes', 'professor', 'grades', 'gpa']
            },
            'other': {          
            }
        }
    
    def _load_red_flags(self) -> Dict[str, List[str]]:
        """Load red flag keywords"""
        return {
            'critical': ['suicide', 'kill myself', 'end my life', 'want to die'],
            'high': ['depression', 'depressed', 'hopeless', 'worthless'],
            'medium': ['anxiety', 'stressed', 'overwhelmed', 'panic']
        }
    
    def categorize_text(self, text: str) -> Dict[str, List[str]]:
        """
        Categorize text based on keywords
        """
        text_lower = text.lower()
        found_categories = {}
        
        for main_category, subcategories in self.keyword_categories.items():
            found_subcategories = []
            for subcategory, keywords in subcategories.items():
                if any(keyword in text_lower for keyword in keywords):
                    found_subcategories.append(subcategory)
            
            if found_subcategories:
                found_categories[main_category] = found_subcategories
        
        return found_categories
    
    def detect_red_flags(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect concerning content
        """
        text_lower = text.lower()
        alerts = []
        
        for severity, keywords in self.red_flag_keywords.items():
            found_keywords = [kw for kw in keywords if kw in text_lower]
            if found_keywords:
                alerts.append({
                    'type': 'mental_health',
                    'postID': postID,
                    'severity': severity,
                    'keywords_found': found_keywords,
                    'timestamp': datetime.now(timezone.utc)
                })
        
        return alerts
    
    def process_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process list of posts"""
        processed = []
        
        for post in posts:
            try:
                text = f"{post.get('title', '')} {post.get('selftext', '')}"
                
                # Add processing metadata
                post['processed_at'] = datetime.now(timezone.utc)
                post['categories'] = self.categorize_text(text)
                post['red_flags'] = self.detect_red_flags(text)
                post['text_length'] = len(text)
                
                processed.append(post)
                
            except Exception as e:
                logger.error(f"Error processing post {post.get('post_id', 'unknown')}: {e}")
                continue
        
        return processed
    
    def process_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process list of comments
        """
        processed = []
        
        for comment in comments:
            try:
                text = comment.get('body', '')
                
                # Add processing metadata
                comment['processed_at'] = datetime.now(timezone.utc)
                comment['categories'] = self.categorize_text(text)
                comment['red_flags'] = self.detect_red_flags(text)
                comment['text_length'] = len(text)
                
                processed.append(comment)
                
            except Exception as e:
                logger.error(f"Error processing comment {comment.get('comment_id', 'unknown')}: {e}")
                continue
        
        return processed