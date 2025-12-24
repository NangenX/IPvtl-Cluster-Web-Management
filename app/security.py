"""
Security module for API authentication.

Provides API Key authentication mechanism using X-API-Key header.
Authentication can be enabled/disabled via configuration.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# Define the API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Verify the API key from the request header.
    
    Args:
        api_key: The API key from X-API-Key header
        
    Returns:
        True if authentication is disabled or key is valid
        
    Raises:
        HTTPException: If authentication is enabled and key is invalid or missing
    """
    # If authentication is disabled, allow all requests
    if not settings.API_KEY_ENABLED:
        return True
    
    # If authentication is enabled, verify the key
    if not api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Include 'X-API-Key' header in your request.",
        )
    
    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: key length={len(api_key)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    
    logger.debug("API key verified successfully")
    return True
