"""
Authentication and authorization for the REST API.
"""
import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from .config import settings

logger = logging.getLogger(__name__)

# API Key authentication
api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)

class APIKeyAuth:
    """API Key authentication handler."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def __call__(self, api_key: str = Depends(api_key_header)):
        """Validate API key."""
        if api_key is None:
            logger.warning("API key missing in request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        if api_key != self.api_key:
            logger.warning(f"Invalid API key provided: {api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        logger.debug("API key authentication successful")
        return api_key

def get_api_key_dependency():
    """Get the API key dependency for route protection."""
    return APIKeyAuth(settings.API_KEY)

# Create the dependency instance
get_api_key = get_api_key_dependency()
