import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def load_config(config_file: str = None) -> Dict[str, Any]:
    """Load configuration from file and environment"""
    
    # Default configuration
    config = {
        'app': {
            'name': 'UCLA Sentiment Analysis',
            'version': '1.0.0',
            'debug': os.getenv('DEBUG', 'false').lower() == 'true'
        },
        'reddit': {
            'client_id': os.getenv('REDDIT_CLIENT_ID'),
            'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
            'user_agent': os.getenv('REDDIT_USER_AGENT', 'UCLA-Sentiment/1.0'),
            'subreddit': os.getenv('SUBREDDIT', 'UCLA'),
            'post_limit': int(os.getenv('POST_LIMIT', '100')),
            'comment_limit': int(os.getenv('COMMENT_LIMIT', '50'))
        },
        'database': {
            'url': os.getenv('DATABASE_URL', 'sqlite:///./sentiment_analysis.db'),
            'pool_size': int(os.getenv('DB_POOL_SIZE', '10'))
        },
        'api': {
            'host': os.getenv('API_HOST', '0.0.0.0'),
            'port': int(os.getenv('API_PORT', '8080')),
            'workers': int(os.getenv('API_WORKERS', '1'))
        },
        'dashboard': {
            'host': os.getenv('DASHBOARD_HOST', '0.0.0.0'),
            'port': int(os.getenv('DASHBOARD_PORT', '8501'))
        },
        'alerts': {
            'email_enabled': os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true',
            'slack_enabled': os.getenv('ALERT_SLACK_ENABLED', 'false').lower() == 'true',
            'recipients': os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',')
        },
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    
    # Load from YAML file if specified
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    config.update(file_config)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Error loading config file {config_file}: {e}")
    
    return config