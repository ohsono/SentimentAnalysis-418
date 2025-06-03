#!/usr/bin/env python3

"""
Analytics Background Tasks
Handles analytics computation, caching, and metrics collection
"""

import logging
import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from celery import Task

from .celery_app import celery_app

logger = logging.getLogger(__name__)

class AnalyticsTask(Task):
    """Base task class for analytics operations"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called on task success"""
        logger.info(f"Analytics task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        logger.error(f"Analytics task {task_id} failed: {exc}")

@celery_app.task(base=AnalyticsTask, bind=True, max_retries=2)
def refresh_analytics_cache(self, force_refresh: bool = False):
    """
    Refresh analytics cache with latest data
    
    Args:
        force_refresh: Force refresh even if cache is not expired
    """
    try:
        logger.info(f"Refreshing analytics cache (force: {force_refresh})")
        
        cache_summary = {
            'cache_entries_updated': 0,
            'computation_time_ms': 0,
            'data_points_processed': 0,
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        start_time = time.time()
        
        # Simulate analytics computation
        analytics_data = compute_dashboard_analytics()
        cache_summary['data_points_processed'] = analytics_data['data_points']
        
        # Simulate cache update operations
        cache_entries = [
            'sentiment_distribution',
            'hourly_activity', 
            'model_performance',
            'alert_statistics',
            'subreddit_breakdown'
        ]
        
        for entry in cache_entries:
            time.sleep(0.1)  # Simulate cache write
            cache_summary['cache_entries_updated'] += 1
            logger.debug(f"Updated cache entry: {entry}")
        
        computation_time = (time.time() - start_time) * 1000
        cache_summary['computation_time_ms'] = round(computation_time, 2)
        cache_summary['completed_at'] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Analytics cache refresh completed: {cache_summary}")
        return cache_summary
        
    except Exception as exc:
        logger.error(f"Analytics cache refresh failed: {exc}")
        self.retry(countdown=300, exc=exc)

def compute_dashboard_analytics() -> Dict[str, Any]:
    """Compute analytics data for dashboard"""
    
    # Simulate data computation
    time.sleep(1)
    
    return {
        'sentiment_distribution': {
            'positive': 45.2,
            'neutral': 38.1,
            'negative': 16.7
        },
        'hourly_activity': [
            {'hour': h, 'posts': 20 + (h % 12) * 5} 
            for h in range(24)
        ],
        'model_performance': {
            'vader_accuracy': 0.85,
            'llm_accuracy': 0.92,
            'average_response_time': 45.2
        },
        'alert_statistics': {
            'total_active': 12,
            'high_priority': 3,
            'medium_priority': 7,
            'low_priority': 2
        },
        'data_points': 15000,
        'computed_at': datetime.now(timezone.utc).isoformat()
    }

@celery_app.task(base=AnalyticsTask, bind=True, max_retries=2)
def collect_system_metrics(self):
    """
    Collect system performance metrics
    """
    try:
        logger.info("Collecting system metrics")
        
        metrics = {
            'system': collect_system_performance(),
            'application': collect_application_metrics(),
            'database': collect_database_metrics(),
            'collected_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Store metrics (would use DatabaseManager in real implementation)
        logger.info(f"System metrics collected: {len(metrics)} categories")
        return metrics
        
    except Exception as exc:
        logger.error(f"System metrics collection failed: {exc}")
        self.retry(countdown=120, exc=exc)

def collect_system_performance() -> Dict[str, Any]:
    """Collect system performance metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_usage_percent': cpu_percent,
            'memory_usage_percent': memory.percent,
            'memory_available_mb': memory.available // (1024 * 1024),
            'disk_usage_percent': disk.percent,
            'disk_free_gb': disk.free // (1024 * 1024 * 1024),
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
    except Exception as e:
        logger.warning(f"Failed to collect system metrics: {e}")
        return {'error': str(e)}

def collect_application_metrics() -> Dict[str, Any]:
    """Collect application-specific metrics"""
    # Simulate application metrics
    import random
    
    return {
        'api_requests_per_minute': random.randint(50, 200),
        'average_response_time_ms': random.uniform(30, 100),
        'active_connections': random.randint(10, 50),
        'cache_hit_rate': random.uniform(0.8, 0.95),
        'error_rate_percent': random.uniform(0.1, 2.0)
    }

def collect_database_metrics() -> Dict[str, Any]:
    """Collect database performance metrics"""
    # Simulate database metrics
    import random
    
    return {
        'active_connections': random.randint(5, 20),
        'queries_per_second': random.randint(100, 500),
        'average_query_time_ms': random.uniform(5, 50),
        'table_sizes_mb': {
            'sentiment_analysis_results': random.randint(100, 500),
            'reddit_posts': random.randint(50, 200),
            'sentiment_alerts': random.randint(10, 50)
        },
        'index_usage_percent': random.uniform(85, 95)
    }

@celery_app.task(base=AnalyticsTask, bind=True, max_retries=2)
def generate_daily_report(self, date: str = None):
    """
    Generate daily analytics report
    
    Args:
        date: Date for report (YYYY-MM-DD), defaults to yesterday
    """
    try:
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"Generating daily report for {date}")
        
        report_data = {
            'report_date': date,
            'summary': generate_daily_summary(date),
            'sentiment_analysis': generate_sentiment_summary(date),
            'alert_summary': generate_alert_summary(date),
            'performance_summary': generate_performance_summary(date),
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Daily report generated for {date}")
        return report_data
        
    except Exception as exc:
        logger.error(f"Daily report generation failed: {exc}")
        self.retry(countdown=300, exc=exc)

def generate_daily_summary(date: str) -> Dict[str, Any]:
    """Generate daily summary statistics"""
    import random
    
    return {
        'total_posts_analyzed': random.randint(500, 2000),
        'total_comments_analyzed': random.randint(1000, 5000),
        'alerts_generated': random.randint(10, 50),
        'model_service_uptime_percent': random.uniform(95, 100),
        'api_requests': random.randint(5000, 20000)
    }

def generate_sentiment_summary(date: str) -> Dict[str, Any]:
    """Generate sentiment analysis summary"""
    import random
    
    return {
        'sentiment_distribution': {
            'positive': random.uniform(40, 50),
            'neutral': random.uniform(35, 45),
            'negative': random.uniform(10, 20)
        },
        'average_confidence': random.uniform(0.75, 0.9),
        'model_usage': {
            'vader_fallback_percent': random.uniform(10, 30),
            'llm_service_percent': random.uniform(70, 90)
        }
    }

def generate_alert_summary(date: str) -> Dict[str, Any]:
    """Generate alert summary"""
    import random
    
    return {
        'alerts_by_type': {
            'mental_health': random.randint(2, 10),
            'stress': random.randint(5, 20),
            'academic': random.randint(3, 15),
            'harassment': random.randint(0, 5)
        },
        'alerts_by_severity': {
            'high': random.randint(2, 8),
            'medium': random.randint(5, 15),
            'low': random.randint(3, 12)
        },
        'response_times': {
            'average_hours': random.uniform(2, 8),
            'alerts_resolved': random.randint(8, 25)
        }
    }

def generate_performance_summary(date: str) -> Dict[str, Any]:
    """Generate performance summary"""
    import random
    
    return {
        'api_performance': {
            'average_response_time_ms': random.uniform(40, 80),
            'p95_response_time_ms': random.uniform(100, 200),
            'error_rate_percent': random.uniform(0.1, 1.0)
        },
        'model_performance': {
            'average_inference_time_ms': random.uniform(50, 150),
            'successful_predictions': random.randint(1800, 2200),
            'failed_predictions': random.randint(10, 50)
        },
        'resource_usage': {
            'average_cpu_percent': random.uniform(20, 60),
            'average_memory_percent': random.uniform(40, 80),
            'disk_io_operations': random.randint(1000, 5000)
        }
    }

@celery_app.task(base=AnalyticsTask, bind=True, max_retries=2)
def compute_trend_analysis(self, days_back: int = 30):
    """
    Compute trend analysis over specified period
    
    Args:
        days_back: Number of days to analyze
    """
    try:
        logger.info(f"Computing trend analysis for last {days_back} days")
        
        trend_data = {
            'period_days': days_back,
            'sentiment_trends': compute_sentiment_trends(days_back),
            'volume_trends': compute_volume_trends(days_back),
            'alert_trends': compute_alert_trends(days_back),
            'computed_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Trend analysis completed for {days_back} days")
        return trend_data
        
    except Exception as exc:
        logger.error(f"Trend analysis failed: {exc}")
        self.retry(countdown=300, exc=exc)

def compute_sentiment_trends(days: int) -> Dict[str, Any]:
    """Compute sentiment trends over time"""
    import random
    
    # Simulate trend data
    daily_trends = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_trends.append({
            'date': date,
            'positive_percent': random.uniform(40, 50),
            'negative_percent': random.uniform(10, 20),
            'neutral_percent': random.uniform(30, 45),
            'volume': random.randint(100, 500)
        })
    
    return {
        'daily_trends': daily_trends[:7],  # Last 7 days
        'overall_trend': random.choice(['improving', 'stable', 'declining']),
        'trend_strength': random.uniform(0.1, 0.8)
    }

def compute_volume_trends(days: int) -> Dict[str, Any]:
    """Compute volume trends over time"""
    import random
    
    return {
        'average_daily_posts': random.randint(200, 800),
        'peak_hour': random.randint(14, 18),
        'growth_rate_percent': random.uniform(-5, 15),
        'weekly_pattern': {
            'monday': random.uniform(0.8, 1.2),
            'tuesday': random.uniform(0.9, 1.1),
            'wednesday': random.uniform(0.9, 1.1),
            'thursday': random.uniform(0.9, 1.1),
            'friday': random.uniform(1.0, 1.3),
            'saturday': random.uniform(0.7, 1.0),
            'sunday': random.uniform(0.6, 0.9)
        }
    }

def compute_alert_trends(days: int) -> Dict[str, Any]:
    """Compute alert trends over time"""
    import random
    
    return {
        'average_daily_alerts': random.randint(5, 25),
        'trend_direction': random.choice(['increasing', 'stable', 'decreasing']),
        'most_common_type': random.choice(['stress', 'mental_health', 'academic']),
        'seasonal_factors': random.uniform(0.8, 1.2)
    }
