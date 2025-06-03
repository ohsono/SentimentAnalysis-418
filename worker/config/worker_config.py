#!/usr/bin/env python3

"""
Worker Configuration for UCLA Sentiment Analysis
Centralized configuration for all worker processes
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WorkerConfig:
    """Configuration class for worker processes"""
    
    def __init__(self):
        # Base paths
        self.WORKER_ROOT = Path(__file__).parent.parent
        self.PROJECT_ROOT = self.WORKER_ROOT.parent
        self.DATA_DIR = self.WORKER_ROOT / "data"
        self.LOGS_DIR = self.WORKER_ROOT / "logs"
        
        # Ensure directories exist
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        
        # Reddit API Configuration
        self.REDDIT_CONFIG = {
            'client_id': os.getenv('REDDIT_CLIENT_ID'),
            'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
            'user_agent': os.getenv('REDDIT_USER_AGENT', 'UCLA-Sentiment-Analysis-Worker/1.0'),
        }
        
        # Database Configuration (same as web service)
        self.DATABASE_CONFIG = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "ucla_sentiment"),
            "username": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "password")
        }
        
        # Scraping Configuration
        self.SCRAPING_CONFIG = {
            'default_subreddit': os.getenv('DEFAULT_SUBREDDIT', 'UCLA'),
            'default_post_limit': int(os.getenv('DEFAULT_POST_LIMIT', '100')),
            'default_comment_limit': int(os.getenv('DEFAULT_COMMENT_LIMIT', '50')),
            'rate_limit_delay': float(os.getenv('RATE_LIMIT_DELAY', '1.0')),
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
        }
        
        # Processing Configuration
        self.PROCESSING_CONFIG = {
            'keyword_include': ['UCLA', 'ucla', 'Bruins', 'bruins', 'UCLA Bruins', 'ucla bruins'],
            'keyword_exclude': ['NSFW', 'nsfw'],
            'min_text_length': int(os.getenv('MIN_TEXT_LENGTH', '10')),
            'batch_size': int(os.getenv('PROCESSING_BATCH_SIZE', '100')),
        }
        
        # Worker Process Configuration
        self.WORKER_CONFIG = {
            'max_workers': int(os.getenv('MAX_WORKERS', '4')),
            'worker_timeout': int(os.getenv('WORKER_TIMEOUT', '3600')),  # 1 hour
            'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '300')),  # 5 minutes
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        }
        
        # API Communication Configuration
        self.API_CONFIG = {
            'web_service_url': os.getenv('WEB_SERVICE_URL', 'http://localhost:8080'),
            'api_key': os.getenv('WORKER_API_KEY', 'worker-secret-key'),
            'communication_enabled': os.getenv('WORKER_API_COMMUNICATION', 'true').lower() == 'true',
        }
    
    def get_reddit_config(self) -> Dict[str, Any]:
        """Get Reddit API configuration"""
        return self.REDDIT_CONFIG.copy()
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.DATABASE_CONFIG.copy()
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration"""
        return self.SCRAPING_CONFIG.copy()
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return self.PROCESSING_CONFIG.copy()
    
    def validate_config(self) -> bool:
        """Validate that all required configuration is present"""
        # Check Reddit API credentials
        reddit_required = ['client_id', 'client_secret']
        reddit_missing = [key for key in reddit_required if not self.REDDIT_CONFIG[key]]
        
        if reddit_missing:
            print(f"Missing Reddit API configuration: {reddit_missing}")
            return False
        
        # Check database configuration
        db_required = ['host', 'database', 'username', 'password']
        db_missing = [key for key in db_required if not self.DATABASE_CONFIG[key]]
        
        if db_missing:
            print(f"Missing database configuration: {db_missing}")
            return False
        
        return True
    
    def print_config_summary(self):
        """Print a summary of the configuration"""
        print("=" * 50)
        print("WORKER CONFIGURATION SUMMARY")
        print("=" * 50)
        print(f"Worker Root: {self.WORKER_ROOT}")
        print(f"Data Directory: {self.DATA_DIR}")
        print(f"Logs Directory: {self.LOGS_DIR}")
        print(f"Default Subreddit: {self.SCRAPING_CONFIG['default_subreddit']}")
        print(f"Max Workers: {self.WORKER_CONFIG['max_workers']}")
        print(f"Web Service URL: {self.API_CONFIG['web_service_url']}")
        print(f"Database Host: {self.DATABASE_CONFIG['host']}")
        print(f"Reddit Client ID: {'*' * len(self.REDDIT_CONFIG['client_id']) if self.REDDIT_CONFIG['client_id'] else 'NOT SET'}")
        print("=" * 50)

# Global configuration instance
config = WorkerConfig()
