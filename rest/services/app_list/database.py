"""
Database initialization for App List service.
"""
import logging
from core.database import db_manager

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the app list database tables."""
    try:
        logger.info("Initializing app list database...")
        db_manager.init_app_list_table()
        logger.info("App list database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize app list database: {e}")
        raise

if __name__ == "__main__":
    # Run this file directly to initialize the app list database
    init_db()
