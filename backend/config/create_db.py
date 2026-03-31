import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config.settings import settings
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

def create_database():
    """Create the main database if it doesn't exist"""
    try:
        # Properly escape password if it contains special characters
        escaped_password = quote(settings.DB_PASSWORD, safe="")
        
        # Connect to default PostgreSQL database
        engine = create_engine(
            f"postgresql://{settings.DB_USER}:{escaped_password}@{settings.DB_HOST}:{settings.DB_PORT}/postgres",
            isolation_level="AUTOCOMMIT"
        )
        
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{settings.DB_NAME}'")
            )
            
            if not result.fetchone():
                # Create database
                conn.execute(text(f"CREATE DATABASE {settings.DB_NAME}"))
                logger.info(f"Database '{settings.DB_NAME}' created successfully")
            else:
                logger.info(f"Database '{settings.DB_NAME}' already exists")
        
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

if __name__ == "__main__":
    create_database()
