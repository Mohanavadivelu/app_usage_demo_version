"""
Database configuration and connection management for MCP App Usage Analytics Server.

This module handles database connections, connection pooling, and provides
utilities for database operations across the application.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

import sqlite3
import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """
    Database configuration class for managing connection parameters.
    
    This class centralizes database configuration and provides methods
    for establishing and managing database connections.
    
    Attributes:
        db_path (str): Path to the SQLite database file
        timeout (int): Connection timeout in seconds
        check_same_thread (bool): SQLite thread safety setting
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database configuration.
        
        Args:
            db_path (str, optional): Path to database file. 
                                   Defaults to '../database/app_usage.db'
        """
        if db_path is None:
            # Default path relative to the mcp-server-app-usage directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            self.db_path = os.path.join(os.path.dirname(project_root), 'database', 'app_usage.db')
        else:
            self.db_path = db_path
            
        self.timeout = 30.0
        self.check_same_thread = False
        
        # Validate database file exists
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
    
    def get_connection_params(self) -> Dict[str, Any]:
        """
        Get database connection parameters.
        
        Returns:
            dict: Dictionary containing connection parameters
        """
        return {
            'database': self.db_path,
            'timeout': self.timeout,
            'check_same_thread': self.check_same_thread
        }


@contextmanager
def get_database_connection(config: Optional[DatabaseConfig] = None):
    """
    Context manager for database connections.
    
    Provides a database connection with automatic cleanup and error handling.
    Ensures connections are properly closed even if exceptions occur.
    
    Args:
        config (DatabaseConfig, optional): Database configuration object
    
    Yields:
        sqlite3.Connection: Database connection object
    
    Raises:
        DatabaseError: If connection cannot be established
        
    Example:
        >>> with get_database_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM app_usage LIMIT 5")
        ...     results = cursor.fetchall()
    """
    if config is None:
        config = DatabaseConfig()
    
    connection = None
    try:
        connection = sqlite3.connect(**config.get_connection_params())
        connection.row_factory = sqlite3.Row  # Enable dict-like access to rows
        logger.debug(f"Database connection established: {config.db_path}")
        yield connection
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        if connection:
            connection.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database connection: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()
            logger.debug("Database connection closed")


def execute_query(query: str, params: tuple = (), config: Optional[DatabaseConfig] = None) -> list:
    """
    Execute a SELECT query and return results.
    
    This utility function handles the common pattern of executing a query
    and returning all results with proper error handling.
    
    Args:
        query (str): SQL query to execute
        params (tuple): Query parameters for parameterized queries
        config (DatabaseConfig, optional): Database configuration
    
    Returns:
        list: List of query results as sqlite3.Row objects
    
    Raises:
        DatabaseError: If query execution fails
        
    Example:
        >>> results = execute_query(
        ...     "SELECT * FROM app_usage WHERE user = ?", 
        ...     ("john_doe",)
        ... )
        >>> for row in results:
        ...     print(row['application_name'])
    """
    with get_database_connection(config) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_update(query: str, params: tuple = (), config: Optional[DatabaseConfig] = None) -> int:
    """
    Execute an INSERT, UPDATE, or DELETE query.
    
    Args:
        query (str): SQL query to execute
        params (tuple): Query parameters for parameterized queries
        config (DatabaseConfig, optional): Database configuration
    
    Returns:
        int: Number of affected rows
    
    Raises:
        DatabaseError: If query execution fails
    """
    with get_database_connection(config) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount


def get_table_info(table_name: str, config: Optional[DatabaseConfig] = None) -> list:
    """
    Get information about a database table structure.
    
    Args:
        table_name (str): Name of the table to inspect
        config (DatabaseConfig, optional): Database configuration
    
    Returns:
        list: Table structure information
    """
    query = f"PRAGMA table_info({table_name})"
    return execute_query(query, (), config)


# Global database configuration instance
_db_config = None


def get_default_config() -> DatabaseConfig:
    """
    Get the default database configuration instance.
    
    Returns:
        DatabaseConfig: Default configuration instance
    """
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def set_default_config(config: DatabaseConfig):
    """
    Set the default database configuration.
    
    Args:
        config (DatabaseConfig): Configuration to set as default
    """
    global _db_config
    _db_config = config
