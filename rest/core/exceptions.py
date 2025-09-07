"""
Custom exceptions and error handling for the REST API.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class ApplicationError(Exception):
    """Base exception for application-specific errors."""
    
    def __init__(self, message: str, error_code: str = "APPLICATION_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(ApplicationError):
    """Exception for database operation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)

class NotFoundError(ApplicationError):
    """Exception for resource not found errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NOT_FOUND", details)

class ValidationError(ApplicationError):
    """Exception for data validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log error with context information."""
    context = context or {}
    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def application_error_handler(request: Request, exc: ApplicationError):
    """Handle application-specific errors."""
    log_error(exc, {"url": str(request.url), "method": request.method})
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

async def general_error_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    log_error(exc, {"url": str(request.url), "method": request.method})
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "details": {},
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

def handle_database_error(func):
    """Decorator to handle database errors in CRUD operations."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database operation failed in {func.__name__}: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    return wrapper
