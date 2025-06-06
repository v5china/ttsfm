"""
TTSFM - Text-to-Speech API Client

A Python package for interacting with TTS services with OpenAI-compatible API.
Provides both synchronous and asynchronous clients for easy integration.
"""

from .client import TTSClient
from .async_client import AsyncTTSClient
from .models import (
    TTSRequest,
    TTSResponse,
    Voice,
    AudioFormat,
    TTSError,
    APIError,
    NetworkError,
    ValidationError
)
from .exceptions import (
    TTSException,
    APIException,
    NetworkException,
    ValidationException,
    RateLimitException,
    AuthenticationException
)
from .utils import (
    validate_text_length,
    split_text_by_length
)

__version__ = "3.0.0"
__author__ = "dbcccc"
__email__ = "120614547+dbccccccc@users.noreply.github.com"
__description__ = "Text-to-Speech API Client with OpenAI compatibility"
__url__ = "https://github.com/dbccccccc/ttsfm"

# Default client instance for convenience
default_client = None

def create_client(base_url: str = None, api_key: str = None, **kwargs) -> TTSClient:
    """
    Create a new TTS client instance.
    
    Args:
        base_url: Base URL for the TTS service
        api_key: API key for authentication (if required)
        **kwargs: Additional client configuration
        
    Returns:
        TTSClient: Configured client instance
    """
    return TTSClient(base_url=base_url, api_key=api_key, **kwargs)

def create_async_client(base_url: str = None, api_key: str = None, **kwargs) -> AsyncTTSClient:
    """
    Create a new async TTS client instance.
    
    Args:
        base_url: Base URL for the TTS service
        api_key: API key for authentication (if required)
        **kwargs: Additional client configuration
        
    Returns:
        AsyncTTSClient: Configured async client instance
    """
    return AsyncTTSClient(base_url=base_url, api_key=api_key, **kwargs)

def set_default_client(client: TTSClient) -> None:
    """Set the default client instance for convenience functions."""
    global default_client
    default_client = client

def generate_speech(text: str, voice: str = "alloy", **kwargs) -> bytes:
    """
    Convenience function to generate speech using the default client.
    
    Args:
        text: Text to convert to speech
        voice: Voice to use for generation
        **kwargs: Additional generation parameters
        
    Returns:
        bytes: Generated audio data
        
    Raises:
        TTSException: If no default client is set or generation fails
    """
    if default_client is None:
        raise TTSException("No default client set. Use create_client() first.")
    
    return default_client.generate_speech(text=text, voice=voice, **kwargs)

# Export all public components
__all__ = [
    # Main classes
    "TTSClient",
    "AsyncTTSClient",
    
    # Models
    "TTSRequest",
    "TTSResponse", 
    "Voice",
    "AudioFormat",
    "TTSError",
    "APIError",
    "NetworkError",
    "ValidationError",
    
    # Exceptions
    "TTSException",
    "APIException",
    "NetworkException",
    "ValidationException",
    "RateLimitException",
    "AuthenticationException",
    
    # Factory functions
    "create_client",
    "create_async_client",
    "set_default_client",
    "generate_speech",

    # Utility functions
    "validate_text_length",
    "split_text_by_length",
    
    # Package metadata
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "__url__"
]
