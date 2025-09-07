"""
Main FastAPI application entry point for the App Usage REST API.
Includes routers for app usage and app list services.
"""
import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.app_usage.routes import router as app_usage_router
from services.app_list.routes import router as app_list_router
from core.config import settings
from core.database import init_db
from core.exceptions import (
    ApplicationError,
    application_error_handler,
    general_error_handler,
    log_error
)

logger = logging.getLogger(__name__)

# Create FastAPI app with configuration
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="REST API for App Usage tracking and App List management with centralized database",
    debug=settings.DEBUG
)

# Add error handlers
app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(Exception, general_error_handler)

# Enable CORS using configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks."""
    try:
        logger.info("Starting App Usage REST API...")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Debug mode: {settings.DEBUG}")

        # Initialize database
        init_db()
        logger.info("Database initialized successfully")

        logger.info("App Usage REST API started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks on shutdown."""
    try:
        logger.info("Shutting down App Usage REST API...")
        # Close database connections
        from core.database import db_manager
        db_manager.close()
        logger.info("App Usage REST API shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Include routers for each service
def include_routers():
    """Attach all service routers to the main FastAPI app."""
    app.include_router(app_usage_router, prefix=settings.API_PREFIX)
    app.include_router(app_list_router, prefix=settings.API_PREFIX)

include_routers()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION,
        "services": ["app_usage", "app_list"]
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "App Usage REST API",
        "version": settings.API_VERSION,
        "docs_url": "/docs",
        "health_url": "/health",
        "services": {
            "app_usage": f"{settings.API_PREFIX}/app_usage",
            "app_list": f"{settings.API_PREFIX}/app_list"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower()
    )
