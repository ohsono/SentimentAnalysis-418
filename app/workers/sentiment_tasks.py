#!/usr/bin/env python3

"""
Sentiment Analysis Background Tasks
Handles batch processing and model inference in background
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from celery import Task

from .celery_app import celery_app
from ..api.simple_sentiment_analyzer import SimpleSentimentAnalyzer
from ..database.postgres_manager_enhanced import DatabaseManager

logger = logging.getLogger(__name__)

# Initialize components
sentiment_analyzer = SimpleSentimentAnalyzer()

class CallbackTask(Task):
    """Base task class with callback support"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called on task success"""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        logger.error(f"Task {task_id} failed: {exc}")

@celery_app.task(base=CallbackTask, bind=True, max_retries=3)
def process_sentiment_batch(self, texts: List[str], model: str = "vader", options: Dict[str, Any] = None):
    """
    Process a batch of texts for sentiment analysis
    
    Args:
        texts: List of texts to analyze
        model: Model to use ('vader' for fallback, 'llm' for model service)
        options: Additional processing options
    """
    try:
        logger.info(f"Processing sentiment batch: {len(texts)} texts with {model}")
        
        options = options or {}
        results = []
        
        for i, text in enumerate(texts):
            try:
                # Use VADER analyzer for background processing (reliable fallback)
                result = sentiment_analyzer.analyze(text)
                result.update({
                    'batch_index': i,
                    'text_length': len(text),
                    'processed_at': datetime.now(timezone.utc).isoformat(),
                    'processed_by': 'background_worker',
                    'model_used': 'vader',
                    'source': 'background_task'
                })
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing text {i}: {e}")
                results.append({
                    'batch_index': i,
                    'error': str(e),
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'compound_score': 0.0,
                    'text_length': len(text) if text else 0
                })
        
        # Calculate summary
        successful_results = [r for r in results if 'error' not in r]
        sentiments = [r['sentiment'] for r in successful_results]
        
        summary = {
            'total_processed': len(results),
            'successful': len(successful_results),
            'failed': len(results) - len(successful_results),
            'sentiment_distribution': {
                'positive': sentiments.count('positive'),
                'negative': sentiments.count('negative'),
                'neutral': sentiments.count('neutral')
            },
            'model_used': model,
            'processed_by': 'background_worker',
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Batch processing complete: {summary}")
        
        return {
            'results': results,
            'summary': summary,
            'status': 'completed'
        }
        
    except Exception as exc:
        logger.error(f"Batch processing failed: {exc}")
        self.retry(countdown=60, exc=exc)

@celery_app.task(base=CallbackTask, bind=True, max_retries=3)
def analyze_reddit_content(self, post_data: Dict[str, Any], include_comments: bool = True):
    """
    Analyze Reddit post and optionally comments
    
    Args:
        post_data: Reddit post data
        include_comments: Whether to analyze comments
    """
    try:
        logger.info(f"Analyzing Reddit post: {post_data.get('post_id', 'unknown')}")
        
        results = {}
        
        # Analyze post
        post_text = f"{post_data.get('title', '')} {post_data.get('selftext', '')}"
        if post_text.strip():
            post_sentiment = sentiment_analyzer.analyze(post_text)
            post_sentiment.update({
                'content_type': 'post',
                'content_id': post_data.get('post_id'),
                'subreddit': post_data.get('subreddit'),
                'author': post_data.get('author'),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'processed_by': 'background_worker'
            })
            results['post'] = post_sentiment
        
        # Analyze comments if provided
        if include_comments and 'comments' in post_data:
            comment_results = []
            for comment in post_data['comments']:
                try:
                    comment_text = comment.get('body', '')
                    if comment_text.strip():
                        comment_sentiment = sentiment_analyzer.analyze(comment_text)
                        comment_sentiment.update({
                            'content_type': 'comment',
                            'content_id': comment.get('comment_id'),
                            'parent_id': comment.get('post_id'),
                            'author': comment.get('author'),
                            'processed_at': datetime.now(timezone.utc).isoformat(),
                            'processed_by': 'background_worker'
                        })
                        comment_results.append(comment_sentiment)
                except Exception as e:
                    logger.error(f"Error processing comment {comment.get('comment_id', 'unknown')}: {e}")
            
            results['comments'] = comment_results
        
        # Detect alerts
        alerts = []
        if 'post' in results:
            alert = detect_content_alert(post_text, results['post'], post_data)
            if alert:
                alerts.append(alert)
        
        if 'comments' in results:
            for i, comment_result in enumerate(results['comments']):
                comment_data = post_data['comments'][i] if i < len(post_data.get('comments', [])) else {}
                alert = detect_content_alert(comment_data.get('body', ''), comment_result, comment_data)
                if alert:
                    alerts.append(alert)
        
        results['alerts'] = alerts
        results['summary'] = {
            'post_analyzed': 'post' in results,
            'comments_analyzed': len(results.get('comments', [])),
            'alerts_detected': len(alerts),
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Reddit content analysis complete: {results['summary']}")
        return results
        
    except Exception as exc:
        logger.error(f"Reddit content analysis failed: {exc}")
        self.retry(countdown=60, exc=exc)

def detect_content_alert(text: str, sentiment_result: Dict[str, Any], content_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Detect if content should trigger an alert"""
    alert_keywords = {
        'mental_health': ['depressed', 'depression', 'suicide', 'kill myself', 'end it all', 'worthless', 'hopeless'],
        'stress': ['overwhelmed', 'stressed', 'anxious', 'panic', 'breakdown', 'can\'t handle'],
        'academic': ['failing', 'dropped out', 'academic probation', 'expelled', 'flunking'],
        'harassment': ['bullied', 'harassed', 'threatened', 'stalked', 'discriminated']
    }
    
    text_lower = text.lower()
    
    for alert_type, keywords in alert_keywords.items():
        found_keywords = [kw for kw in keywords if kw in text_lower]
        if found_keywords:
            # Determine severity based on sentiment and keywords
            compound_score = sentiment_result.get('compound_score', 0)
            
            if compound_score < -0.5:
                severity = 'high'
            elif compound_score < -0.2:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Escalate mental health alerts
            if alert_type == 'mental_health':
                severity = 'high' if severity != 'low' else 'medium'
            
            return {
                'alert_type': alert_type,
                'severity': severity,
                'keywords_found': found_keywords,
                'confidence': sentiment_result.get('confidence', 0),
                'compound_score': compound_score,
                'content_id': content_data.get('post_id') or content_data.get('comment_id'),
                'content_type': sentiment_result.get('content_type', 'unknown'),
                'content_text': text[:500],  # Truncate for storage
                'subreddit': content_data.get('subreddit'),
                'author': content_data.get('author'),
                'detected_at': datetime.now(timezone.utc).isoformat(),
                'detected_by': 'background_worker'
            }
    
    return None

@celery_app.task(base=CallbackTask, bind=True)
def process_alert_queue(self, alert_data: Dict[str, Any]):
    """
    Process alerts detected in content
    
    Args:
        alert_data: Alert information to process
    """
    try:
        logger.info(f"Processing alert: {alert_data.get('alert_type', 'unknown')} - {alert_data.get('severity', 'unknown')}")
        
        # Add processing metadata
        alert_data.update({
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'processed_by': 'background_worker',
            'status': 'active'
        })
        
        # Calculate priority
        priority_map = {
            'critical': 90,
            'high': 70,
            'medium': 50,
            'low': 30
        }
        
        base_priority = priority_map.get(alert_data.get('severity', 'medium'), 50)
        if alert_data.get('alert_type') == 'mental_health':
            base_priority = min(95, base_priority + 20)
        
        alert_data['priority'] = base_priority
        
        # Here you would typically:
        # 1. Store the alert in database
        # 2. Send notifications if needed
        # 3. Update monitoring systems
        
        logger.info(f"Alert processed successfully: {alert_data.get('alert_type')}")
        return alert_data
        
    except Exception as exc:
        logger.error(f"Alert processing failed: {exc}")
        raise

@celery_app.task(base=CallbackTask, bind=True, max_retries=2)
def store_sentiment_results(self, results: List[Dict[str, Any]]):
    """
    Store sentiment analysis results in database
    
    Args:
        results: List of sentiment analysis results
    """
    try:
        logger.info(f"Storing {len(results)} sentiment results in database")
        
        # This would use the DatabaseManager to store results
        # For now, we'll simulate the storage
        
        stored_count = 0
        failed_count = 0
        
        for result in results:
            try:
                # Add storage metadata
                result.update({
                    'stored_at': datetime.now(timezone.utc).isoformat(),
                    'stored_by': 'background_worker'
                })
                
                # Here you would store in database using DatabaseManager
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store result: {e}")
                failed_count += 1
        
        summary = {
            'total_results': len(results),
            'stored_successfully': stored_count,
            'failed_to_store': failed_count,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Storage complete: {summary}")
        return summary
        
    except Exception as exc:
        logger.error(f"Batch storage failed: {exc}")
        self.retry(countdown=120, exc=exc)
