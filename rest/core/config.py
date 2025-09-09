"""
Application configuration management for REST API.
"""
import os
import logging
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import validator, Field
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, validator, Field

class Settings(BaseSettings):
    """Application settings and configuration with validation."""

    # Database settings
    DATABASE_NAME: str = Field(default="app_usage.db", description="Database filename")
    DATABASE_URL: Optional[str] = Field(default=None, description="Full database URL (overrides DATABASE_NAME)")
    DATABASE_MAX_CONNECTIONS: int = Field(default=10, ge=1, le=100, description="Maximum database connections")

    # API settings
    API_TITLE: str = Field(default="App Usage REST API", description="API title")
    API_VERSION: str = Field(default="1.0.0", description="API version")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")

    # Authentication settings
    API_KEY: str = Field(default="CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w", description="API key for authentication")
    API_KEY_NAME: str = Field(default="X-API-Key-725d9439", description="API key header name")

    # CORS settings
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000", "null"], description="Allowed CORS origins")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")
    CORS_ALLOW_METHODS: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], description="Allowed CORS methods")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="Allowed CORS headers")

    # Environment settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Server settings
    HOST: str = Field(default="127.0.0.1", description="Server host")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Server port")

    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @validator('CORS_ALLOW_METHODS', pre=True)
    def parse_cors_methods(cls, v):
        """Parse CORS methods from string or list."""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [method.strip().upper() for method in v.split(",") if method.strip()]
        return v

    @validator('CORS_ALLOW_HEADERS', pre=True)
    def parse_cors_headers(cls, v):
        """Parse CORS headers from string or list."""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [header.strip() for header in v.split(",") if header.strip()]
        return v

    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_environments = ['development', 'testing', 'staging', 'production']
        if v not in allowed_environments:
            raise ValueError(f'Environment must be one of: {allowed_environments}')
        return v

    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    def configure_logging(self):
        """Configure logging based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        if self.is_production:
            # In production, we might want to configure more sophisticated logging
            pass

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Global settings instance
try:
    settings = Settings()
    settings.configure_logging()
except Exception as e:
    # Fallback to basic configuration if settings fail to load
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to load settings: {e}")
    logger.info("Using default settings")
    settings = Settings()
