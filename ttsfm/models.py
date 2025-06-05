"""
Data models and types for the TTSFM package.

This module defines the core data structures used throughout the package,
including request/response models, enums, and error types.
"""

from enum import Enum
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime


class Voice(str, Enum):
    """Available voice options for TTS generation."""
    ALLOY = "alloy"
    ASH = "ash"
    BALLAD = "ballad"
    CORAL = "coral"
    ECHO = "echo"
    FABLE = "fable"
    NOVA = "nova"
    ONYX = "onyx"
    SAGE = "sage"
    SHIMMER = "shimmer"
    VERSE = "verse"


class AudioFormat(str, Enum):
    """Supported audio output formats."""
    MP3 = "mp3"
    OPUS = "opus"
    AAC = "aac"
    FLAC = "flac"
    WAV = "wav"
    PCM = "pcm"


@dataclass
class TTSRequest:
    """
    Request model for TTS generation.

    Attributes:
        input: Text to convert to speech
        voice: Voice to use for generation
        response_format: Audio format for output
        instructions: Optional instructions for voice modulation
        model: Model to use (for OpenAI compatibility, usually ignored)
        speed: Speech speed (for OpenAI compatibility, usually ignored)
        max_length: Maximum allowed text length (default: 4096 characters)
        validate_length: Whether to validate text length (default: True)
    """
    input: str
    voice: Union[Voice, str] = Voice.ALLOY
    response_format: Union[AudioFormat, str] = AudioFormat.MP3
    instructions: Optional[str] = None
    model: Optional[str] = None
    speed: Optional[float] = None
    max_length: int = 4096
    validate_length: bool = True
    
    def __post_init__(self):
        """Validate and normalize fields after initialization."""
        # Ensure voice is a valid Voice enum
        if isinstance(self.voice, str):
            try:
                self.voice = Voice(self.voice.lower())
            except ValueError:
                raise ValueError(f"Invalid voice: {self.voice}. Must be one of {list(Voice)}")

        # Ensure response_format is a valid AudioFormat enum
        if isinstance(self.response_format, str):
            try:
                self.response_format = AudioFormat(self.response_format.lower())
            except ValueError:
                raise ValueError(f"Invalid format: {self.response_format}. Must be one of {list(AudioFormat)}")

        # Validate input text
        if not self.input or not self.input.strip():
            raise ValueError("Input text cannot be empty")

        # Validate text length if enabled
        if self.validate_length:
            text_length = len(self.input)
            if text_length > self.max_length:
                raise ValueError(
                    f"Input text is too long ({text_length} characters). "
                    f"Maximum allowed length is {self.max_length} characters. "
                    f"Consider splitting your text into smaller chunks or disable "
                    f"length validation with validate_length=False."
                )

        # Validate max_length parameter
        if self.max_length <= 0:
            raise ValueError("max_length must be a positive integer")

        # Validate speed if provided
        if self.speed is not None and (self.speed < 0.25 or self.speed > 4.0):
            raise ValueError("Speed must be between 0.25 and 4.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary for API calls."""
        data = {
            "input": self.input,
            "voice": self.voice.value if isinstance(self.voice, Voice) else self.voice,
            "response_format": self.response_format.value if isinstance(self.response_format, AudioFormat) else self.response_format
        }
        
        if self.instructions:
            data["instructions"] = self.instructions
        
        if self.model:
            data["model"] = self.model
            
        if self.speed is not None:
            data["speed"] = self.speed
            
        return data


@dataclass
class TTSResponse:
    """
    Response model for TTS generation.
    
    Attributes:
        audio_data: Generated audio as bytes
        content_type: MIME type of the audio data
        format: Audio format used
        size: Size of audio data in bytes
        duration: Estimated duration in seconds (if available)
        metadata: Additional response metadata
    """
    audio_data: bytes
    content_type: str
    format: AudioFormat
    size: int
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        if self.size is None:
            self.size = len(self.audio_data)
    
    def save_to_file(self, filename: str) -> str:
        """
        Save audio data to a file.
        
        Args:
            filename: Target filename (extension will be added if missing)
            
        Returns:
            str: Final filename used
        """
        import os
        
        # Add extension if not present
        if not filename.endswith(f".{self.format.value}"):
            filename = f"{filename}.{self.format.value}"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
        
        # Write audio data
        with open(filename, "wb") as f:
            f.write(self.audio_data)
        
        return filename


@dataclass
class TTSError:
    """
    Error information from TTS API.
    
    Attributes:
        code: Error code
        message: Human-readable error message
        type: Error type/category
        details: Additional error details
        timestamp: When the error occurred
    """
    code: str
    message: str
    type: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class APIError(TTSError):
    """API-specific error information."""
    status_code: int = 500
    headers: Optional[Dict[str, str]] = None


@dataclass
class NetworkError(TTSError):
    """Network-related error information."""
    timeout: Optional[float] = None
    retry_count: int = 0


@dataclass
class ValidationError(TTSError):
    """Validation error information."""
    field: Optional[str] = None
    value: Optional[Any] = None


# Content type mappings for audio formats
CONTENT_TYPE_MAP = {
    AudioFormat.MP3: "audio/mpeg",
    AudioFormat.OPUS: "audio/opus",
    AudioFormat.AAC: "audio/aac",
    AudioFormat.FLAC: "audio/flac",
    AudioFormat.WAV: "audio/wav",
    AudioFormat.PCM: "audio/pcm"
}

# Reverse mapping for content type to format
FORMAT_FROM_CONTENT_TYPE = {v: k for k, v in CONTENT_TYPE_MAP.items()}


def get_content_type(format: Union[AudioFormat, str]) -> str:
    """Get MIME content type for audio format."""
    if isinstance(format, str):
        format = AudioFormat(format.lower())
    return CONTENT_TYPE_MAP.get(format, "audio/mpeg")


def get_format_from_content_type(content_type: str) -> AudioFormat:
    """Get audio format from MIME content type."""
    return FORMAT_FROM_CONTENT_TYPE.get(content_type, AudioFormat.MP3)
