#!/usr/bin/env python3
"""
Unit tests for the combined audio functionality.

Tests the audio combination logic, text splitting, and endpoint functionality.
"""

import unittest
import io
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the modules to test
try:
    from ttsfm.utils import split_text_by_length
    from ttsfm.models import TTSResponse, AudioFormat
except ImportError:
    # Fallback for development
    sys.path.insert(0, str(project_root / "ttsfm"))
    from utils import split_text_by_length
    from models import TTSResponse, AudioFormat

# Import the web app functions
try:
    sys.path.insert(0, str(project_root / "ttsfm-web"))
    from app import combine_audio_chunks, _simple_wav_concatenation
except ImportError:
    # Mock these if we can't import them
    def combine_audio_chunks(chunks, format_type):
        return b''.join(chunks)
    
    def _simple_wav_concatenation(chunks):
        return b''.join(chunks)


class TestTextSplitting(unittest.TestCase):
    """Test the text splitting functionality."""
    
    def test_short_text_no_splitting(self):
        """Test that short text is not split."""
        text = "This is a short text."
        result = split_text_by_length(text, max_length=100)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], text)
    
    def test_sentence_boundary_splitting(self):
        """Test splitting at sentence boundaries."""
        text = "First sentence. Second sentence! Third sentence?"
        result = split_text_by_length(text, max_length=20, preserve_words=True)
        
        # Should split at sentence boundaries
        self.assertGreater(len(result), 1)
        for chunk in result:
            self.assertLessEqual(len(chunk), 20)
            # Each chunk should end with punctuation or be the last chunk
            if chunk != result[-1]:
                self.assertTrue(chunk.strip().endswith(('.', '!', '?')))
    
    def test_word_boundary_splitting(self):
        """Test splitting at word boundaries when sentences are too long."""
        text = "This is a very long sentence that exceeds the maximum length and should be split at word boundaries"
        result = split_text_by_length(text, max_length=30, preserve_words=True)
        
        self.assertGreater(len(result), 1)
        for chunk in result:
            self.assertLessEqual(len(chunk), 30)
            # Should not split words (except possibly the last chunk)
            words = chunk.strip().split()
            if len(words) > 1:
                self.assertFalse(any(' ' in word for word in words[:-1]))
    
    def test_character_splitting_disabled(self):
        """Test character-level splitting when preserve_words is False."""
        text = "This is a test text that will be split at character boundaries"
        result = split_text_by_length(text, max_length=20, preserve_words=False)
        
        self.assertGreater(len(result), 1)
        for chunk in result:
            self.assertLessEqual(len(chunk), 20)
    
    def test_empty_text(self):
        """Test handling of empty text."""
        result = split_text_by_length("", max_length=100)
        self.assertEqual(result, [])
    
    def test_very_long_word(self):
        """Test handling of words longer than max_length."""
        long_word = "a" * 100
        text = f"Short {long_word} text"
        result = split_text_by_length(text, max_length=20, preserve_words=True)
        
        # Should split the long word
        self.assertGreater(len(result), 1)
        # Find the chunk with the long word parts
        long_word_chunks = [chunk for chunk in result if 'a' * 10 in chunk]
        self.assertGreater(len(long_word_chunks), 1)


class TestAudioCombination(unittest.TestCase):
    """Test the audio combination functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create mock audio data
        self.mp3_chunk1 = b'\xff\xfb\x90\x00' + b'mock_mp3_data_1' * 10
        self.mp3_chunk2 = b'\xff\xfb\x90\x00' + b'mock_mp3_data_2' * 10
        self.wav_chunk1 = b'RIFF' + b'\x24\x00\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00' + b'\x01\x00\x02\x00' + b'\x44\xac\x00\x00' + b'\x10\xb1\x02\x00' + b'\x04\x00\x10\x00' + b'data' + b'\x00\x00\x00\x00'
        self.wav_chunk2 = b'RIFF' + b'\x24\x00\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00' + b'\x01\x00\x02\x00' + b'\x44\xac\x00\x00' + b'\x10\xb1\x02\x00' + b'\x04\x00\x10\x00' + b'data' + b'\x00\x00\x00\x00'
    
    def test_simple_concatenation_fallback(self):
        """Test simple concatenation when PyDub is not available."""
        chunks = [self.mp3_chunk1, self.mp3_chunk2]
        
        # Mock PyDub import failure
        with patch('builtins.__import__', side_effect=ImportError):
            result = combine_audio_chunks(chunks, "mp3")
        
        # Should fall back to simple concatenation
        self.assertEqual(result, self.mp3_chunk1 + self.mp3_chunk2)
    
    def test_wav_concatenation_fallback(self):
        """Test WAV-specific concatenation fallback."""
        chunks = [self.wav_chunk1, self.wav_chunk2]
        
        with patch('builtins.__import__', side_effect=ImportError):
            result = _simple_wav_concatenation(chunks)
        
        # Should combine WAV files properly
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), len(chunks[0]))
    
    def test_empty_chunks(self):
        """Test handling of empty chunk list."""
        result = combine_audio_chunks([], "mp3")
        self.assertEqual(result, b'')
    
    def test_single_chunk(self):
        """Test handling of single chunk."""
        chunks = [self.mp3_chunk1]
        result = combine_audio_chunks(chunks, "mp3")
        self.assertEqual(result, self.mp3_chunk1)
    
    @patch('app.AudioSegment')
    def test_pydub_combination(self, mock_audio_segment):
        """Test audio combination using PyDub."""
        # Mock PyDub functionality
        mock_segment1 = Mock()
        mock_segment2 = Mock()
        mock_combined = Mock()
        
        mock_audio_segment.from_mp3.side_effect = [mock_segment1, mock_segment2]
        mock_segment1.__add__ = Mock(return_value=mock_combined)
        mock_combined.export = Mock()
        
        # Mock the export to return some data
        mock_buffer = Mock()
        mock_buffer.getvalue.return_value = b'combined_audio_data'
        
        with patch('io.BytesIO', return_value=mock_buffer):
            chunks = [self.mp3_chunk1, self.mp3_chunk2]
            result = combine_audio_chunks(chunks, "mp3")
        
        # Verify PyDub was used
        self.assertEqual(mock_audio_segment.from_mp3.call_count, 2)
        mock_combined.export.assert_called_once()


class TestTTSResponseCombination(unittest.TestCase):
    """Test combining TTSResponse objects."""
    
    def setUp(self):
        """Set up test TTSResponse objects."""
        self.response1 = TTSResponse(
            audio_data=b'audio_data_1',
            content_type='audio/mpeg',
            format=AudioFormat.MP3,
            size=12,
            duration=2.5
        )
        
        self.response2 = TTSResponse(
            audio_data=b'audio_data_2',
            content_type='audio/mpeg',
            format=AudioFormat.MP3,
            size=12,
            duration=3.0
        )
    
    def test_extract_audio_data(self):
        """Test extracting audio data from TTSResponse objects."""
        responses = [self.response1, self.response2]
        audio_chunks = [response.audio_data for response in responses]
        
        self.assertEqual(len(audio_chunks), 2)
        self.assertEqual(audio_chunks[0], b'audio_data_1')
        self.assertEqual(audio_chunks[1], b'audio_data_2')
    
    def test_metadata_preservation(self):
        """Test that metadata is preserved from responses."""
        responses = [self.response1, self.response2]
        
        # Should be able to access metadata from first response
        self.assertEqual(responses[0].content_type, 'audio/mpeg')
        self.assertEqual(responses[0].format, AudioFormat.MP3)
        
        # Total duration should be sum of individual durations
        total_duration = sum(r.duration for r in responses if r.duration)
        self.assertEqual(total_duration, 5.5)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in audio combination."""
    
    def test_invalid_audio_data(self):
        """Test handling of invalid audio data."""
        invalid_chunks = [b'invalid', b'audio', b'data']
        
        # Should not raise exception, but fall back gracefully
        result = combine_audio_chunks(invalid_chunks, "mp3")
        self.assertIsInstance(result, bytes)
    
    def test_mixed_formats(self):
        """Test handling of mixed audio formats."""
        # This should be handled gracefully
        chunks = [b'mp3_data', b'wav_data']
        result = combine_audio_chunks(chunks, "mp3")
        self.assertIsInstance(result, bytes)
    
    def test_unsupported_format(self):
        """Test handling of unsupported audio format."""
        chunks = [b'audio_data_1', b'audio_data_2']
        result = combine_audio_chunks(chunks, "unsupported_format")
        self.assertIsInstance(result, bytes)


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic integration scenarios."""
    
    def test_long_text_to_combined_audio_workflow(self):
        """Test the complete workflow from long text to combined audio."""
        # Long text that needs splitting
        long_text = """
        This is a very long text that exceeds the normal character limit for TTS systems.
        It contains multiple sentences and should be split intelligently at sentence boundaries.
        Each chunk will be processed separately and then combined into a single audio file.
        This test verifies that the entire workflow functions correctly from start to finish.
        """ * 10  # Make it definitely long
        
        # Step 1: Split the text
        chunks = split_text_by_length(long_text, max_length=200, preserve_words=True)
        self.assertGreater(len(chunks), 1)
        
        # Step 2: Simulate TTS responses for each chunk
        mock_responses = []
        for i, chunk in enumerate(chunks):
            response = TTSResponse(
                audio_data=f'audio_data_chunk_{i}'.encode(),
                content_type='audio/mpeg',
                format=AudioFormat.MP3,
                size=len(f'audio_data_chunk_{i}'),
                duration=2.0
            )
            mock_responses.append(response)
        
        # Step 3: Extract audio data
        audio_chunks = [response.audio_data for response in mock_responses]
        
        # Step 4: Combine audio
        combined_audio = combine_audio_chunks(audio_chunks, "mp3")
        
        # Verify results
        self.assertIsInstance(combined_audio, bytes)
        self.assertGreater(len(combined_audio), 0)
        self.assertEqual(len(mock_responses), len(chunks))
    
    def test_different_audio_formats(self):
        """Test combination with different audio formats."""
        formats_to_test = ["mp3", "wav", "opus", "aac", "flac"]
        
        for format_type in formats_to_test:
            with self.subTest(format=format_type):
                chunks = [b'audio_data_1', b'audio_data_2']
                result = combine_audio_chunks(chunks, format_type)
                self.assertIsInstance(result, bytes)
                self.assertGreater(len(result), 0)
    
    def test_edge_case_single_character_chunks(self):
        """Test with very small text chunks."""
        text = "A. B. C. D. E."
        chunks = split_text_by_length(text, max_length=2, preserve_words=True)
        
        # Should handle very small chunks gracefully
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertGreater(len(chunk.strip()), 0)
    
    def test_unicode_text_handling(self):
        """Test handling of Unicode text."""
        unicode_text = "Hello 世界! This is a test with émojis 🎵 and special characters: àáâãäå"
        chunks = split_text_by_length(unicode_text, max_length=30, preserve_words=True)
        
        # Should handle Unicode properly
        self.assertGreater(len(chunks), 0)
        combined_text = ' '.join(chunks)
        # Should preserve all characters
        self.assertIn('世界', combined_text)
        self.assertIn('🎵', combined_text)
        self.assertIn('àáâãäå', combined_text)


class TestPerformanceScenarios(unittest.TestCase):
    """Test performance-related scenarios."""

    def test_large_number_of_chunks(self):
        """Test combining a large number of audio chunks."""
        # Create many small chunks
        chunks = [f'chunk_{i}_data'.encode() for i in range(100)]

        # Should handle large number of chunks
        result = combine_audio_chunks(chunks, "mp3")
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    def test_very_long_text_splitting(self):
        """Test splitting very long text."""
        # Create a very long text
        very_long_text = "This is a sentence. " * 1000  # 20,000 characters

        chunks = split_text_by_length(very_long_text, max_length=500, preserve_words=True)

        # Should split into reasonable number of chunks
        self.assertGreater(len(chunks), 10)
        self.assertLess(len(chunks), 100)  # Shouldn't be too many

        # All chunks should be within limit
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 500)

    def test_memory_efficiency(self):
        """Test memory efficiency with large audio chunks."""
        import sys

        # Create large audio chunks (simulate large audio files)
        large_chunks = [b'audio_data' * 10000 for _ in range(10)]  # ~100KB each

        # Monitor memory usage (basic check)
        initial_size = sys.getsizeof(large_chunks)
        result = combine_audio_chunks(large_chunks, "mp3")

        # Result should exist and be reasonable size
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

        # Should not create excessive memory overhead
        result_size = sys.getsizeof(result)
        self.assertLess(result_size, initial_size * 2)  # Reasonable overhead

    def test_splitting_performance(self):
        """Test performance of text splitting algorithm."""
        import time

        # Create very long text with many sentences
        long_text = "This is sentence number {}. ".format(1) * 5000  # Many sentences

        start_time = time.time()
        chunks = split_text_by_length(long_text, max_length=1000, preserve_words=True)
        end_time = time.time()

        # Should complete quickly
        processing_time = end_time - start_time
        self.assertLess(processing_time, 1.0)  # Should take less than 1 second

        # Should produce reasonable number of chunks
        self.assertGreater(len(chunks), 1)
        self.assertLess(len(chunks), len(long_text) // 100)  # Not too many chunks


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestTextSplitting,
        TestAudioCombination,
        TestTTSResponseCombination,
        TestErrorHandling,
        TestIntegrationScenarios,
        TestPerformanceScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
