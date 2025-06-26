"""
TTSFM Combined Audio Tests

Test suite for the combined audio functionality in TTSFM.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ttsfm"))
sys.path.insert(0, str(project_root / "ttsfm-web"))

# Test configuration
TEST_CONFIG = {
    'server_url': 'http://localhost:8000',
    'timeout': 30,
    'max_text_length': 10000,
    'test_voices': ['alloy', 'nova', 'echo'],
    'test_formats': ['mp3', 'wav', 'opus'],
    'performance_thresholds': {
        'text_splitting_time': 1.0,  # seconds
        'audio_combination_time': 5.0,  # seconds
        'end_to_end_time': 30.0,  # seconds
        'memory_overhead_factor': 2.0  # max memory overhead
    }
}

# Test data
SAMPLE_TEXTS = {
    'short': "This is a short test text for TTS generation.",
    'medium': """
    This is a medium-length text that should trigger some splitting behavior.
    It contains multiple sentences and should be processed as separate chunks.
    The system should handle this text efficiently and produce good quality audio.
    """,
    'long': """
    This is a comprehensive test of the combined audio generation functionality.
    The text is intentionally long to trigger the splitting and combination logic.
    It contains multiple sentences that should be processed as separate chunks.
    Each chunk will be converted to speech individually and then combined.
    The final result should be a single, seamless audio file.
    This approach allows for processing of very long texts that exceed normal TTS limits.
    The system intelligently splits at sentence boundaries for natural speech flow.
    Additional sentences are included to ensure the text exceeds typical limits.
    The audio combination process should handle all chunks smoothly.
    Quality should be maintained throughout the entire generated audio file.
    """ * 3,
    'unicode': """
    Hello 世界! This is a test with émojis 🎵 and special characters: àáâãäå.
    Testing with various scripts: Русский текст, العربية, 日本語, 한국어.
    The system should handle Unicode text properly in combined audio generation.
    """,
    'very_long': "This is a sentence for very long text testing. " * 500
}

__all__ = ['TEST_CONFIG', 'SAMPLE_TEXTS']
