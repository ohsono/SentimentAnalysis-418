import logging
import logging.config
import os
from typing import Dict, Any

def setup_logging(config: Dict[str, Any] = None):
    """Setup application logging"""
    
    if config is None:
        config = {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    
    # Convert string level to logging constant
    level = getattr(logging, config.get('level', 'INFO').upper())
    format_str = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/app.log') if os.path.exists('logs') else logging.NullHandler()
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('streamlit').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)