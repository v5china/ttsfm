"""
Main TTS client implementation.

This module provides the primary TTSClient class for synchronous
text-to-speech generation with OpenAI-compatible API.
"""

import json
import time
import uuid
import logging
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    TTSRequest, TTSResponse, Voice, AudioFormat,
    get_content_type, get_format_from_content_type
)
from .exceptions import (
    TTSException, APIException, NetworkException, ValidationException,
    create_exception_from_response
)
from .utils import (
    get_realistic_headers, sanitize_text, validate_url, build_url,
    exponential_backoff, estimate_audio_duration, format_file_size,
    validate_text_length, split_text_by_length
)


logger = logging.getLogger(__name__)


class TTSClient:
    """
    Synchronous TTS client for text-to-speech generation.
    
    This client provides a simple interface for generating speech from text
    using OpenAI-compatible TTS services.
    
    Attributes:
        base_url: Base URL for the TTS service
        api_key: API key for authentication (if required)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        verify_ssl: Whether to verify SSL certificates
    """
    
    def __init__(
        self,
        base_url: str = "https://www.openai.fm",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        verify_ssl: bool = True,
        **kwargs
    ):
        """
        Initialize the TTS client.
        
        Args:
            base_url: Base URL for the TTS service
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            verify_ssl: Whether to verify SSL certificates
            **kwargs: Additional configuration options
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        
        # Validate base URL
        if not validate_url(self.base_url):
            raise ValidationException(f"Invalid base URL: {self.base_url}")
        
        # Setup HTTP session with retry strategy
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],  # Updated parameter name
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update(get_realistic_headers())
        
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
        
        logger.info(f"Initialized TTS client with base URL: {self.base_url}")
    
    def generate_speech(
        self,
        text: str,
        voice: Union[Voice, str] = Voice.ALLOY,
        response_format: Union[AudioFormat, str] = AudioFormat.MP3,
        instructions: Optional[str] = None,
        max_length: int = 4096,
        validate_length: bool = True,
        **kwargs
    ) -> TTSResponse:
        """
        Generate speech from text.

        Args:
            text: Text to convert to speech
            voice: Voice to use for generation
            response_format: Audio format for output
            instructions: Optional instructions for voice modulation
            max_length: Maximum allowed text length in characters (default: 4096)
            validate_length: Whether to validate text length (default: True)
            **kwargs: Additional parameters

        Returns:
            TTSResponse: Generated audio response

        Raises:
            TTSException: If generation fails
            ValueError: If text exceeds max_length and validate_length is True
        """
        # Create and validate request
        request = TTSRequest(
            input=sanitize_text(text),
            voice=voice,
            response_format=response_format,
            instructions=instructions,
            max_length=max_length,
            validate_length=validate_length,
            **kwargs
        )

        return self._make_request(request)
    
    def generate_speech_from_request(self, request: TTSRequest) -> TTSResponse:
        """
        Generate speech from a TTSRequest object.

        Args:
            request: TTS request object

        Returns:
            TTSResponse: Generated audio response
        """
        return self._make_request(request)

    def generate_speech_batch(
        self,
        text: str,
        voice: Union[Voice, str] = Voice.ALLOY,
        response_format: Union[AudioFormat, str] = AudioFormat.MP3,
        instructions: Optional[str] = None,
        max_length: int = 4096,
        preserve_words: bool = True,
        **kwargs
    ) -> List[TTSResponse]:
        """
        Generate speech from long text by splitting it into chunks.

        This method automatically splits text that exceeds max_length into
        smaller chunks and generates speech for each chunk separately.

        Args:
            text: Text to convert to speech
            voice: Voice to use for generation
            response_format: Audio format for output
            instructions: Optional instructions for voice modulation
            max_length: Maximum length per chunk (default: 4096)
            preserve_words: Whether to avoid splitting words (default: True)
            **kwargs: Additional parameters

        Returns:
            List[TTSResponse]: List of generated audio responses

        Raises:
            TTSException: If generation fails for any chunk
        """

        # Sanitize text first
        clean_text = sanitize_text(text)

        # Split text into chunks
        chunks = split_text_by_length(clean_text, max_length, preserve_words)

        if not chunks:
            raise ValueError("No valid text chunks found after processing")

        responses = []

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} characters)")

            # Create request for this chunk (disable length validation since we already split)
            request = TTSRequest(
                input=chunk,
                voice=voice,
                response_format=response_format,
                instructions=instructions,
                max_length=max_length,
                validate_length=False,  # We already split the text
                **kwargs
            )

            response = self._make_request(request)
            responses.append(response)

        return responses
    
    def _make_request(self, request: TTSRequest) -> TTSResponse:
        """
        Make the actual HTTP request to the openai.fm TTS service.

        Args:
            request: TTS request object

        Returns:
            TTSResponse: Generated audio response

        Raises:
            TTSException: If request fails
        """
        url = build_url(self.base_url, "api/generate")

        # Prepare form data for openai.fm API
        form_data = {
            'input': request.input,
            'voice': request.voice.value,
            'generation': str(uuid.uuid4())
        }

        # Add prompt/instructions if provided
        if request.instructions:
            form_data['prompt'] = request.instructions
        else:
            # Default prompt for better quality
            form_data['prompt'] = (
                "Affect/personality: Natural and clear\n\n"
                "Tone: Friendly and professional, creating a pleasant listening experience.\n\n"
                "Pronunciation: Clear, articulate, and steady, ensuring each word is easily understood "
                "while maintaining a natural, conversational flow.\n\n"
                "Pause: Brief, purposeful pauses between sentences to allow time for the listener "
                "to process the information.\n\n"
                "Emotion: Warm and engaging, conveying the intended message effectively."
            )

        logger.info(f"Generating speech for text: '{request.input[:50]}...' with voice: {request.voice}")

        # Make request with retries
        for attempt in range(self.max_retries + 1):
            try:
                # Add random delay for rate limiting (except first attempt)
                if attempt > 0:
                    delay = exponential_backoff(attempt - 1)
                    logger.info(f"Retrying request after {delay:.2f}s (attempt {attempt + 1})")
                    time.sleep(delay)

                # Use multipart form data as required by openai.fm
                response = self.session.post(
                    url,
                    data=form_data,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                
                # Handle different response types
                if response.status_code == 200:
                    return self._process_openai_fm_response(response, request)
                else:
                    # Try to parse error response
                    try:
                        error_data = response.json()
                    except (json.JSONDecodeError, ValueError):
                        error_data = {"error": {"message": response.text or "Unknown error"}}
                    
                    # Create appropriate exception
                    exception = create_exception_from_response(
                        response.status_code,
                        error_data,
                        f"TTS request failed with status {response.status_code}"
                    )
                    
                    # Don't retry for certain errors
                    if response.status_code in [400, 401, 403, 404]:
                        raise exception
                    
                    # For retryable errors, continue to next attempt
                    if attempt == self.max_retries:
                        raise exception
                    
                    logger.warning(f"Request failed with status {response.status_code}, retrying...")
                    continue
                    
            except requests.exceptions.Timeout:
                if attempt == self.max_retries:
                    raise NetworkException(
                        f"Request timed out after {self.timeout}s",
                        timeout=self.timeout,
                        retry_count=attempt
                    )
                logger.warning(f"Request timed out, retrying...")
                continue
                
            except requests.exceptions.ConnectionError as e:
                if attempt == self.max_retries:
                    raise NetworkException(
                        f"Connection error: {str(e)}",
                        retry_count=attempt
                    )
                logger.warning(f"Connection error, retrying...")
                continue
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise NetworkException(
                        f"Request error: {str(e)}",
                        retry_count=attempt
                    )
                logger.warning(f"Request error, retrying...")
                continue
        
        # This should never be reached, but just in case
        raise TTSException("Maximum retries exceeded")
    
    def _process_openai_fm_response(self, response: requests.Response, request: TTSRequest) -> TTSResponse:
        """
        Process a successful response from the openai.fm TTS service.

        Args:
            response: HTTP response object
            request: Original TTS request

        Returns:
            TTSResponse: Processed response object
        """
        # Get content type from response headers
        content_type = response.headers.get("content-type", "audio/mpeg")

        # Get audio data
        audio_data = response.content

        if not audio_data:
            raise APIException("Received empty audio data from openai.fm")

        # Determine format from content type
        if "audio/mpeg" in content_type or "audio/mp3" in content_type:
            actual_format = AudioFormat.MP3
        elif "audio/wav" in content_type:
            actual_format = AudioFormat.WAV
        elif "audio/opus" in content_type:
            actual_format = AudioFormat.OPUS
        elif "audio/aac" in content_type:
            actual_format = AudioFormat.AAC
        elif "audio/flac" in content_type:
            actual_format = AudioFormat.FLAC
        else:
            # Default to MP3 for openai.fm
            actual_format = AudioFormat.MP3

        # Estimate duration based on text length (rough approximation)
        estimated_duration = estimate_audio_duration(request.input)

        # Create response object
        tts_response = TTSResponse(
            audio_data=audio_data,
            content_type=content_type,
            format=actual_format,
            size=len(audio_data),
            duration=estimated_duration,
            metadata={
                "response_headers": dict(response.headers),
                "status_code": response.status_code,
                "url": str(response.url),
                "service": "openai.fm",
                "voice": request.voice.value,
                "original_text": request.input[:100] + "..." if len(request.input) > 100 else request.input
            }
        )

        logger.info(
            f"Successfully generated {format_file_size(len(audio_data))} "
            f"of {actual_format.value.upper()} audio from openai.fm using voice '{request.voice.value}'"
        )

        return tts_response
    
    def close(self):
        """Close the HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
