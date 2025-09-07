"""
Database initialization for App Usage service.
"""
import logging
from core.database import db_manager

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the app usage database tables."""
    try:
        logger.info("Initializing app usage database...")
        db_manager.init_app_usage_table()
        logger.info("App usage database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize app usage database: {e}")
        raise

if __name__ == "__main__":
    # Run this file directly to initialize the app usage database
    init_db()
