#!/usr/bin/env python3
"""
Specific tests for audio combination functionality.

Tests the audio combination logic with various scenarios and mocking.
"""

import unittest
import io
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ttsfm-web"))


class TestAudioCombinationDetailed(unittest.TestCase):
    """Detailed tests for audio combination functionality."""
    
    def setUp(self):
        """Set up test audio data."""
        # Create realistic MP3 header-like data
        self.mp3_header = b'\xff\xfb\x90\x00'
        self.mp3_chunk1 = self.mp3_header + b'mock_mp3_audio_data_chunk_1' * 20
        self.mp3_chunk2 = self.mp3_header + b'mock_mp3_audio_data_chunk_2' * 20
        
        # Create realistic WAV header
        self.wav_header = (
            b'RIFF' +                    # ChunkID
            b'\x24\x08\x00\x00' +       # ChunkSize (2084 bytes)
            b'WAVE' +                   # Format
            b'fmt ' +                   # Subchunk1ID
            b'\x10\x00\x00\x00' +       # Subchunk1Size (16)
            b'\x01\x00' +               # AudioFormat (PCM)
            b'\x02\x00' +               # NumChannels (2)
            b'\x44\xac\x00\x00' +       # SampleRate (44100)
            b'\x10\xb1\x02\x00' +       # ByteRate
            b'\x04\x00' +               # BlockAlign
            b'\x10\x00' +               # BitsPerSample (16)
            b'data' +                   # Subchunk2ID
            b'\x00\x08\x00\x00'        # Subchunk2Size (2048)
        )
        
        self.wav_audio_data1 = b'wav_audio_sample_data_1' * 50
        self.wav_audio_data2 = b'wav_audio_sample_data_2' * 50
        
        self.wav_chunk1 = self.wav_header + self.wav_audio_data1
        self.wav_chunk2 = self.wav_header + self.wav_audio_data2
    
    @patch('app.AudioSegment')
    def test_pydub_mp3_combination(self, mock_audio_segment):
        """Test MP3 combination using PyDub."""
        from app import combine_audio_chunks
        
        # Mock PyDub AudioSegment
        mock_segment1 = Mock()
        mock_segment2 = Mock()
        mock_combined = Mock()
        
        # Configure mocks
        mock_audio_segment.from_mp3.side_effect = [mock_segment1, mock_segment2]
        mock_segment1.__add__ = Mock(return_value=mock_combined)
        
        # Mock export
        mock_buffer = Mock()
        mock_buffer.getvalue.return_value = b'combined_mp3_audio_data'
        mock_combined.export = Mock()
        
        with patch('io.BytesIO', return_value=mock_buffer):
            chunks = [self.mp3_chunk1, self.mp3_chunk2]
            result = combine_audio_chunks(chunks, "mp3")
        
        # Verify PyDub was called correctly
        self.assertEqual(mock_audio_segment.from_mp3.call_count, 2)
        mock_segment1.__add__.assert_called_once_with(mock_segment2)
        mock_combined.export.assert_called_once_with(mock_buffer, format="mp3")
        self.assertEqual(result, b'combined_mp3_audio_data')
    
    @patch('app.AudioSegment')
    def test_pydub_wav_combination(self, mock_audio_segment):
        """Test WAV combination using PyDub."""
        from app import combine_audio_chunks
        
        # Mock PyDub AudioSegment
        mock_segment1 = Mock()
        mock_segment2 = Mock()
        mock_combined = Mock()
        
        mock_audio_segment.from_wav.side_effect = [mock_segment1, mock_segment2]
        mock_segment1.__add__ = Mock(return_value=mock_combined)
        
        mock_buffer = Mock()
        mock_buffer.getvalue.return_value = b'combined_wav_audio_data'
        mock_combined.export = Mock()
        
        with patch('io.BytesIO', return_value=mock_buffer):
            chunks = [self.wav_chunk1, self.wav_chunk2]
            result = combine_audio_chunks(chunks, "wav")
        
        # Verify PyDub was called correctly
        self.assertEqual(mock_audio_segment.from_wav.call_count, 2)
        mock_combined.export.assert_called_once_with(mock_buffer, format="wav")
        self.assertEqual(result, b'combined_wav_audio_data')
    
    @patch('app.AudioSegment')
    def test_pydub_multiple_chunks(self, mock_audio_segment):
        """Test combining multiple chunks with PyDub."""
        from app import combine_audio_chunks
        
        # Create multiple mock segments
        mock_segments = [Mock() for _ in range(5)]
        mock_audio_segment.from_mp3.side_effect = mock_segments
        
        # Mock the addition chain
        mock_combined = Mock()
        for i, segment in enumerate(mock_segments):
            if i == 0:
                segment.__add__ = Mock(return_value=mock_combined)
            else:
                mock_combined.__add__ = Mock(return_value=mock_combined)
        
        mock_buffer = Mock()
        mock_buffer.getvalue.return_value = b'combined_multiple_chunks'
        mock_combined.export = Mock()
        
        with patch('io.BytesIO', return_value=mock_buffer):
            chunks = [self.mp3_chunk1] * 5  # 5 identical chunks
            result = combine_audio_chunks(chunks, "mp3")
        
        # Verify all chunks were processed
        self.assertEqual(mock_audio_segment.from_mp3.call_count, 5)
        self.assertEqual(result, b'combined_multiple_chunks')
    
    def test_wav_concatenation_fallback(self):
        """Test WAV concatenation fallback when PyDub is not available."""
        from app import _simple_wav_concatenation
        
        chunks = [self.wav_chunk1, self.wav_chunk2]
        result = _simple_wav_concatenation(chunks)
        
        # Should return combined WAV data
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), len(self.wav_chunk1))
        
        # Should start with WAV header
        self.assertTrue(result.startswith(b'RIFF'))
        self.assertIn(b'WAVE', result[:20])
    
    def test_wav_concatenation_single_chunk(self):
        """Test WAV concatenation with single chunk."""
        from app import _simple_wav_concatenation
        
        result = _simple_wav_concatenation([self.wav_chunk1])
        self.assertEqual(result, self.wav_chunk1)
    
    def test_wav_concatenation_empty_chunks(self):
        """Test WAV concatenation with empty chunks."""
        from app import _simple_wav_concatenation
        
        result = _simple_wav_concatenation([])
        self.assertEqual(result, b'')
    
    def test_wav_concatenation_invalid_wav(self):
        """Test WAV concatenation with invalid WAV data."""
        from app import _simple_wav_concatenation
        
        invalid_chunks = [b'not_wav_data', b'also_not_wav']
        result = _simple_wav_concatenation(invalid_chunks)
        
        # Should fall back to simple concatenation
        self.assertEqual(result, b'not_wav_dataalso_not_wav')
    
    @patch('builtins.__import__')
    def test_import_error_fallback(self, mock_import):
        """Test fallback when PyDub import fails."""
        from app import combine_audio_chunks
        
        # Mock import failure for pydub
        def side_effect(name, *args, **kwargs):
            if name == 'pydub':
                raise ImportError("No module named 'pydub'")
            return __import__(name, *args, **kwargs)
        
        mock_import.side_effect = side_effect
        
        chunks = [self.mp3_chunk1, self.mp3_chunk2]
        result = combine_audio_chunks(chunks, "mp3")
        
        # Should fall back to simple concatenation
        self.assertEqual(result, self.mp3_chunk1 + self.mp3_chunk2)
    
    @patch('app.AudioSegment')
    def test_pydub_export_error_fallback(self, mock_audio_segment):
        """Test fallback when PyDub export fails."""
        from app import combine_audio_chunks
        
        # Mock PyDub but make export fail
        mock_segment1 = Mock()
        mock_segment2 = Mock()
        mock_combined = Mock()
        
        mock_audio_segment.from_mp3.side_effect = [mock_segment1, mock_segment2]
        mock_segment1.__add__ = Mock(return_value=mock_combined)
        mock_combined.export.side_effect = Exception("Export failed")
        
        chunks = [self.mp3_chunk1, self.mp3_chunk2]
        result = combine_audio_chunks(chunks, "mp3")
        
        # Should fall back to simple concatenation
        self.assertEqual(result, self.mp3_chunk1 + self.mp3_chunk2)
    
    def test_format_detection_and_handling(self):
        """Test different format detection and handling."""
        from app import combine_audio_chunks
        
        test_formats = ["mp3", "wav", "opus", "aac", "flac", "pcm"]
        chunks = [b'audio_data_1', b'audio_data_2']
        
        for format_type in test_formats:
            with self.subTest(format=format_type):
                result = combine_audio_chunks(chunks, format_type)
                self.assertIsInstance(result, bytes)
                self.assertGreater(len(result), 0)
    
    @patch('app.AudioSegment')
    def test_opus_format_handling(self, mock_audio_segment):
        """Test OPUS format handling (should use WAV processing)."""
        from app import combine_audio_chunks
        
        # OPUS should be treated as WAV in the current implementation
        mock_segment1 = Mock()
        mock_segment2 = Mock()
        mock_combined = Mock()
        
        mock_audio_segment.from_wav.side_effect = [mock_segment1, mock_segment2]
        mock_segment1.__add__ = Mock(return_value=mock_combined)
        
        mock_buffer = Mock()
        mock_buffer.getvalue.return_value = b'combined_opus_as_wav'
        mock_combined.export = Mock()
        
        with patch('io.BytesIO', return_value=mock_buffer):
            chunks = [self.wav_chunk1, self.wav_chunk2]  # Use WAV chunks for OPUS
            result = combine_audio_chunks(chunks, "opus")
        
        # Should use WAV processing for OPUS
        self.assertEqual(mock_audio_segment.from_wav.call_count, 2)
        self.assertEqual(result, b'combined_opus_as_wav')
    
    def test_large_chunk_handling(self):
        """Test handling of large audio chunks."""
        from app import combine_audio_chunks
        
        # Create large chunks (simulate large audio files)
        large_chunk1 = b'large_audio_data_1' * 1000  # ~17KB
        large_chunk2 = b'large_audio_data_2' * 1000  # ~17KB
        
        chunks = [large_chunk1, large_chunk2]
        result = combine_audio_chunks(chunks, "mp3")
        
        # Should handle large chunks without issues
        self.assertIsInstance(result, bytes)
        self.assertGreaterEqual(len(result), len(large_chunk1) + len(large_chunk2))
    
    def test_empty_chunk_filtering(self):
        """Test filtering of empty chunks."""
        from app import combine_audio_chunks
        
        chunks = [b'audio_data_1', b'', b'audio_data_2', b'']
        result = combine_audio_chunks(chunks, "mp3")
        
        # Should handle empty chunks gracefully
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
