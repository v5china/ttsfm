"""
TTSFM - Text-to-Speech for Free using OpenAI.fm

A Python library for generating high-quality text-to-speech audio using the free OpenAI.fm service.
Supports multiple voices and audio formats with a simple, intuitive API.

Features:
- 🎤 6 premium AI voices (alloy, echo, fable, nova, onyx, shimmer)
- 🎵 6 audio formats (MP3, WAV, OPUS, AAC, FLAC, PCM)
- 🚀 Fast and reliable speech generation
- 📝 Comprehensive text processing and validation
- 🔄 Automatic retry with exponential backoff
- 📊 Detailed response metadata and statistics
- 🌐 Both synchronous and asynchronous APIs
- 🎯 OpenAI-compatible API format
- 🔧 Smart format optimization for best quality

Audio Format Support:
- MP3: Good quality, small file size - ideal for web and general use
- WAV: Lossless quality, large file size - ideal for professional use
- OPUS: High-quality compressed audio - ideal for streaming
- AAC: Advanced audio codec - ideal for mobile devices
- FLAC: Lossless compression - ideal for archival
- PCM: Raw audio data - ideal for processing

Example:
    >>> from ttsfm import TTSClient, Voice, AudioFormat
    >>>
    >>> client = TTSClient()
    >>>
    >>> # Generate MP3 audio
    >>> mp3_response = client.generate_speech(
    ...     text="Hello, world!",
    ...     voice=Voice.ALLOY,
    ...     response_format=AudioFormat.MP3
    ... )
    >>> mp3_response.save_to_file("hello")  # Saves as hello.mp3
    >>>
    >>> # Generate WAV audio
    >>> wav_response = client.generate_speech(
    ...     text="High quality audio",
    ...     voice=Voice.NOVA,
    ...     response_format=AudioFormat.WAV
    ... )
    >>> wav_response.save_to_file("audio")  # Saves as audio.wav
    >>>
    >>> # Generate OPUS audio
    >>> opus_response = client.generate_speech(
    ...     text="Compressed audio",
    ...     voice=Voice.ECHO,
    ...     response_format=AudioFormat.OPUS
    ... )
    >>> opus_response.save_to_file("compressed")  # Saves as compressed.wav
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
