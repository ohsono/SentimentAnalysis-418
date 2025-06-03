import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# Database URL from environment, if no database URL feed use default sqllite locally
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./sentiment_analysis.db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_connection():
    """Get database connection"""
    try:
        db = SessionLocal()
        return db
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def init_database():
    """Initialize database tables"""
    try:
        # Import models to register them
        from .models import Post, Comment, Alert
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
