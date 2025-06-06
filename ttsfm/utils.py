"""
Utility functions for the TTSFM package.

This module provides common utility functions used throughout the package,
including HTTP helpers, validation utilities, and configuration management.
"""

import os
import re
import time
import random
import logging
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urljoin, urlparse


# Configure logging
logger = logging.getLogger(__name__)


def get_user_agent() -> str:
    """
    Generate a realistic User-Agent string.
    
    Returns:
        str: User-Agent string for HTTP requests
    """
    try:
        from fake_useragent import UserAgent
        ua = UserAgent()
        return ua.random
    except ImportError:
        # Fallback if fake_useragent is not available
        return "TTSFM-Client/3.0.0 (Python)"


def get_realistic_headers() -> Dict[str, str]:
    """
    Generate realistic HTTP headers for requests.
    
    Returns:
        Dict[str, str]: HTTP headers dictionary
    """
    user_agent = get_user_agent()
    
    headers = {
        "Accept": "application/json, audio/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "en-CA,en;q=0.7"]),
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Pragma": "no-cache",
        "User-Agent": user_agent,
        "X-Requested-With": "XMLHttpRequest",
    }
    
    # Add browser-specific headers for Chromium-based browsers
    if any(browser in user_agent.lower() for browser in ['chrome', 'edge', 'chromium']):
        version_match = re.search(r'(?:Chrome|Edge|Chromium)/(\d+)', user_agent)
        major_version = version_match.group(1) if version_match else "121"
        
        brands = []
        if 'google chrome' in user_agent.lower():
            brands.extend([
                f'"Google Chrome";v="{major_version}"',
                f'"Chromium";v="{major_version}"',
                '"Not A(Brand";v="99"'
            ])
        elif 'microsoft edge' in user_agent.lower():
            brands.extend([
                f'"Microsoft Edge";v="{major_version}"',
                f'"Chromium";v="{major_version}"',
                '"Not A(Brand";v="99"'
            ])
        else:
            brands.extend([
                f'"Chromium";v="{major_version}"',
                '"Not A(Brand";v="8"'
            ])
        
        headers.update({
            "Sec-Ch-Ua": ", ".join(brands),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": random.choice(['"Windows"', '"macOS"', '"Linux"']),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })
    
    # Randomly add some optional headers
    if random.random() < 0.5:
        headers["Upgrade-Insecure-Requests"] = "1"
    
    return headers


def validate_text_length(text: str, max_length: int = 4096, raise_error: bool = True) -> bool:
    """
    Validate text length against maximum allowed characters.

    Args:
        text: Text to validate
        max_length: Maximum allowed length in characters
        raise_error: Whether to raise an exception if validation fails

    Returns:
        bool: True if text is within limits, False otherwise

    Raises:
        ValueError: If text exceeds max_length and raise_error is True
    """
    if not text:
        return True

    text_length = len(text)

    if text_length > max_length:
        if raise_error:
            raise ValueError(
                f"Text is too long ({text_length} characters). "
                f"Maximum allowed length is {max_length} characters. "
                f"TTS models typically support up to 4096 characters per request."
            )
        return False

    return True


def split_text_by_length(text: str, max_length: int = 4096, preserve_words: bool = True) -> List[str]:
    """
    Split text into chunks that don't exceed the maximum length.

    Args:
        text: Text to split
        max_length: Maximum length per chunk
        preserve_words: Whether to avoid splitting words

    Returns:
        List[str]: List of text chunks
    """
    if not text:
        return []

    if len(text) <= max_length:
        return [text]

    chunks = []

    if preserve_words:
        # Split by sentences first, then by words if needed
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add sentence ending punctuation back
            if not sentence.endswith(('.', '!', '?')):
                sentence += '.'

            # Check if adding this sentence would exceed the limit
            test_chunk = current_chunk + (" " if current_chunk else "") + sentence

            if len(test_chunk) <= max_length:
                current_chunk = test_chunk
            else:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # If single sentence is too long, split by words
                if len(sentence) > max_length:
                    word_chunks = _split_by_words(sentence, max_length)
                    chunks.extend(word_chunks)
                    current_chunk = ""
                else:
                    current_chunk = sentence

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
    else:
        # Simple character-based splitting
        for i in range(0, len(text), max_length):
            chunks.append(text[i:i + max_length])

    return [chunk for chunk in chunks if chunk.strip()]


def _split_by_words(text: str, max_length: int) -> List[str]:
    """
    Split text by words when sentences are too long.

    Args:
        text: Text to split
        max_length: Maximum length per chunk

    Returns:
        List[str]: List of word-based chunks
    """
    words = text.split()
    chunks = []
    current_chunk = ""

    for word in words:
        test_chunk = current_chunk + (" " if current_chunk else "") + word

        if len(test_chunk) <= max_length:
            current_chunk = test_chunk
        else:
            if current_chunk:
                chunks.append(current_chunk)

            # If single word is too long, split it
            if len(word) > max_length:
                for i in range(0, len(word), max_length):
                    chunks.append(word[i:i + max_length])
                current_chunk = ""
            else:
                current_chunk = word

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def sanitize_text(text: str) -> str:
    """
    Sanitize input text for TTS processing.

    Args:
        text: Input text to sanitize

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove script tags and content
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def validate_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def build_url(base_url: str, path: str) -> str:
    """
    Build a complete URL from base URL and path.
    
    Args:
        base_url: Base URL
        path: Path to append
        
    Returns:
        str: Complete URL
    """
    # Ensure base_url ends with /
    if not base_url.endswith('/'):
        base_url += '/'
    
    # Ensure path doesn't start with /
    if path.startswith('/'):
        path = path[1:]
    
    return urljoin(base_url, path)


def get_random_delay(min_delay: float = 1.0, max_delay: float = 5.0) -> float:
    """
    Get a random delay with jitter for rate limiting.
    
    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        float: Random delay in seconds
    """
    base_delay = random.uniform(min_delay, max_delay)
    jitter = random.uniform(0.1, 0.5)
    return base_delay + jitter


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        float: Delay in seconds
    """
    delay = base_delay * (2 ** attempt)
    jitter = random.uniform(0.1, 0.3) * delay
    return min(delay + jitter, max_delay)


def load_config_from_env(prefix: str = "TTSFM_") -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Args:
        prefix: Prefix for environment variables
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            
            # Try to convert to appropriate type
            if value.lower() in ('true', 'false'):
                config[config_key] = value.lower() == 'true'
            elif value.isdigit():
                config[config_key] = int(value)
            elif '.' in value and value.replace('.', '').isdigit():
                config[config_key] = float(value)
            else:
                config[config_key] = value
    
    return config


def setup_logging(level: Union[str, int] = logging.INFO, format_string: Optional[str] = None) -> None:
    """
    Setup logging configuration for the package.
    
    Args:
        level: Logging level
        format_string: Custom format string
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[logging.StreamHandler()]
    )


def estimate_audio_duration(text: str, words_per_minute: float = 150.0) -> float:
    """
    Estimate audio duration based on text length.
    
    Args:
        text: Input text
        words_per_minute: Average speaking rate
        
    Returns:
        float: Estimated duration in seconds
    """
    if not text:
        return 0.0
    
    # Count words (simple whitespace split)
    word_count = len(text.split())
    
    # Calculate duration in seconds
    duration = (word_count / words_per_minute) * 60.0
    
    # Add some buffer for pauses and processing
    return duration * 1.1


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"
