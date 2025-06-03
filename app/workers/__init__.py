#!/usr/bin/env python3

"""
UCLA Sentiment Analysis - Background Workers Module

This module contains background task processors for:
- Sentiment analysis batch processing
- Database maintenance and cleanup
- Analytics computation and caching
- System monitoring and metrics collection
"""

from .celery_app import celery_app
from . import sentiment_tasks
from . import database_tasks
from . import analytics_tasks

__all__ = [
    'celery_app',
    'sentiment_tasks',
    'database_tasks', 
    'analytics_tasks'
]
