"""
Centralized database connection and initialization logic for app_usage.db.
"""
import sqlite3
import os
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Generator
from queue import Queue, Empty

# ============================================================================
# SECTION 1: DATABASE CONNECTION & POOLING
# ============================================================================

class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass

class ConnectionPool:
    """Simple connection pool for SQLite connections."""

    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool = Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created_connections = 0
        self.logger = logging.getLogger(__name__)

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys=ON")
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"Failed to create database connection: {e}")
            raise DatabaseError(f"Failed to create database connection: {e}")

    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool."""
        try:
            # Try to get an existing connection from the pool
            return self._pool.get_nowait()
        except Empty:
            # Create a new connection if pool is empty and we haven't reached the limit
            with self._lock:
                if self._created_connections < self.max_connections:
                    self._created_connections += 1
                    return self._create_connection()
                else:
                    # Wait for a connection to become available
                    return self._pool.get()

    def return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool."""
        if conn:
            try:
                # Reset the connection state
                conn.rollback()
                self._pool.put_nowait(conn)
            except Exception as e:
                self.logger.warning(f"Failed to return connection to pool: {e}")
                # Close the connection if we can't return it to the pool
                try:
                    conn.close()
                except:
                    pass
                with self._lock:
                    self._created_connections -= 1

    def close_all(self):
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except:
                pass
        self._created_connections = 0

# ============================================================================
# SECTION 2: DATABASE MANAGEMENT
# ============================================================================

class DatabaseManager:
    """Manages SQLite database connections and operations for app_usage.db."""

    def __init__(self, db_name: str = "app_usage.db"):
        self.db_name = db_name
        self._db_path: Optional[str] = None
        self._pool: Optional[ConnectionPool] = None
        self.logger = logging.getLogger(__name__)
    
    @property
    def db_path(self) -> str:
        """Get the database file path."""
        if self._db_path is None:
            # Get the project root directory (go up from rest/core to project root)
            current_dir = os.path.dirname(os.path.abspath(__file__))  # rest/core
            rest_dir = os.path.dirname(current_dir)  # rest
            project_root = os.path.dirname(rest_dir)  # project root
            db_dir = os.path.join(project_root, 'database')
            try:
                os.makedirs(db_dir, exist_ok=True)
            except OSError as e:
                self.logger.error(f"Failed to create database directory: {e}")
                raise DatabaseError(f"Failed to create database directory: {e}")
            self._db_path = os.path.join(db_dir, self.db_name)
        return self._db_path

    @property
    def pool(self) -> ConnectionPool:
        """Get the connection pool, creating it if necessary."""
        if self._pool is None:
            self._pool = ConnectionPool(self.db_path)
        return self._pool

    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool."""
        return self.pool.get_connection()

    def return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool."""
        self.pool.return_connection(conn)

    @contextmanager
    def get_db_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections with automatic cleanup."""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            self.logger.error(f"Database operation failed: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                self.return_connection(conn)

    @contextmanager
    def get_db_transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database transactions with automatic commit/rollback."""
        conn = None
        try:
            conn = self.get_connection()
            conn.execute("BEGIN")
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            self.logger.error(f"Database transaction failed: {e}")
            raise DatabaseError(f"Database transaction failed: {e}")
        finally:
            if conn:
                self.return_connection(conn)
    
    # ========================================================================
    # SECTION 3: TABLE INITIALIZATION
    # ========================================================================
    
    def init_app_usage_table(self):
        """Initialize the app_usage table."""
        try:
            with self.get_db_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_app_version TEXT NOT NULL CHECK(length(monitor_app_version) <= 50),
                        platform TEXT NOT NULL CHECK(length(platform) <= 50),
                        user TEXT NOT NULL CHECK(length(user) <= 100),
                        application_name TEXT NOT NULL CHECK(length(application_name) <= 100),
                        application_version TEXT NOT NULL CHECK(length(application_version) <= 50),
                        log_date TEXT NOT NULL,
                        legacy_app BOOLEAN NOT NULL,
                        duration_seconds INTEGER NOT NULL CHECK(duration_seconds >= 0),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create indexes for performance optimization
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_app_usage_user ON app_usage(user)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_app_usage_date ON app_usage(log_date)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_app_usage_app ON app_usage(application_name)
                ''')

                self.logger.info("App usage table initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize app usage table: {e}")
            raise DatabaseError(f"Failed to initialize app usage table: {e}")
    
    def init_app_list_table(self):
        """Initialize the app_list table."""
        try:
            with self.get_db_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_list (
                        app_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_name TEXT NOT NULL,
                        app_type TEXT NOT NULL,
                        current_version TEXT NOT NULL,
                        released_date TEXT NOT NULL,
                        publisher TEXT NOT NULL,
                        description TEXT NOT NULL,
                        download_link TEXT NOT NULL,
                        enable_tracking BOOLEAN NOT NULL,
                        track_usage BOOLEAN NOT NULL,
                        track_location BOOLEAN NOT NULL,
                        track_cm BOOLEAN NOT NULL,
                        track_intr INTEGER NOT NULL,
                        registered_date TEXT NOT NULL
                    )
                ''')

                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_app_list_name_type_version
                    ON app_list (app_name, app_type, current_version)
                ''')

                self.logger.info("App list table initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize app list table: {e}")
            raise DatabaseError(f"Failed to initialize app list table: {e}")
    
    def init_all_tables(self):
        """Initialize all database tables."""
        try:
            self.logger.info("Initializing all database tables...")
            self.init_app_usage_table()
            self.init_app_list_table()
            self.logger.info("All database tables initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database tables: {e}")
            raise DatabaseError(f"Failed to initialize database tables: {e}")

    def close(self):
        """Close all database connections."""
        if self._pool:
            self._pool.close_all()
            self._pool = None

# ============================================================================
# SECTION 4: GLOBAL INSTANCES & CONVENIENCE FUNCTIONS
# ============================================================================

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for backward compatibility
def get_db_connection():
    """Get a database connection (backward compatible)."""
    return db_manager.get_connection()

def get_db_path():
    """Get the database path (backward compatible)."""
    return db_manager.db_path

def init_db():
    """Initialize all database tables (backward compatible)."""
    db_manager.init_all_tables()

# Context managers for easier use
def get_db_context():
    """Get a database connection context manager."""
    return db_manager.get_db_connection()

def get_db_transaction():
    """Get a database transaction context manager."""
    return db_manager.get_db_transaction()

if __name__ == "__main__":
    # Run this file directly to initialize the database
    init_db()
