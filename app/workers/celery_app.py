#!/usr/bin/env python3

"""
Celery Application for UCLA Sentiment Analysis
Handles background tasks, data processing, and async operations
"""

import os
import logging
from celery import Celery
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# Build broker URL
if REDIS_PASSWORD:
    BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
    RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Create Celery app
celery_app = Celery(
    'ucla_sentiment_worker',
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        'app.workers.sentiment_tasks',
        'app.workers.database_tasks',
        'app.workers.analytics_tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'app.workers.sentiment_tasks.*': {'queue': 'sentiment'},
        'app.workers.database_tasks.*': {'queue': 'database'},
        'app.workers.analytics_tasks.*': {'queue': 'analytics'},
    },
    
    # Task configuration
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_eager_result=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # Worker settings
    worker_concurrency=2,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-data': {
            'task': 'app.workers.database_tasks.cleanup_old_data',
            'schedule': timedelta(hours=6),  # Every 6 hours
        },
        'refresh-analytics': {
            'task': 'app.workers.analytics_tasks.refresh_analytics_cache',
            'schedule': timedelta(minutes=15),  # Every 15 minutes
        },
        'health-check': {
            'task': 'app.workers.analytics_tasks.collect_system_metrics',
            'schedule': timedelta(minutes=5),  # Every 5 minutes
        },
    },
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Configure queues
celery_app.conf.task_default_queue = 'default'
celery_app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'sentiment': {
        'exchange': 'sentiment',
        'routing_key': 'sentiment',
    },
    'database': {
        'exchange': 'database', 
        'routing_key': 'database',
    },
    'analytics': {
        'exchange': 'analytics',
        'routing_key': 'analytics',
    },
}

if __name__ == '__main__':
    celery_app.start()
