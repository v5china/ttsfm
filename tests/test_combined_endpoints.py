#!/usr/bin/env python3
"""
Integration tests for the combined audio endpoints.

Tests the actual HTTP endpoints for combined audio generation.
"""

import unittest
import requests
import json
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock


class TestCombinedAudioEndpoints(unittest.TestCase):
    """Test the combined audio HTTP endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        cls.base_url = "http://localhost:8000"
        cls.timeout = 30  # Timeout for requests
        
        # Test if server is running
        try:
            response = requests.get(f"{cls.base_url}/api/health", timeout=5)
            if response.status_code != 200:
                raise Exception("Server not healthy")
        except Exception as e:
            raise unittest.SkipTest(f"TTSFM web server not running on {cls.base_url}. Start it first: {e}")
    
    def setUp(self):
        """Set up test data for each test."""
        self.short_text = "This is a short test text for TTS generation."
        
        self.long_text = """
        This is a comprehensive test of the combined audio generation functionality.
        The text is intentionally long to trigger the splitting and combination logic.
        It contains multiple sentences that should be processed as separate chunks.
        Each chunk will be converted to speech individually and then combined.
        The final result should be a single, seamless audio file.
        This approach allows for processing of very long texts that exceed normal TTS limits.
        The system intelligently splits at sentence boundaries for natural speech flow.
        """ * 3  # Make it definitely long enough
        
        self.test_voices = ["alloy", "nova", "echo"]
        self.test_formats = ["mp3", "wav"]
    
    def test_native_endpoint_short_text(self):
        """Test /api/generate-combined with short text."""
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": self.short_text,
            "voice": "alloy",
            "format": "mp3",
            "max_length": 4096
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Chunks-Combined'), '1')
        self.assertGreater(len(response.content), 0)
        self.assertEqual(response.headers.get('Content-Type'), 'audio/mpeg')
    
    def test_native_endpoint_long_text(self):
        """Test /api/generate-combined with long text."""
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": self.long_text,
            "voice": "nova",
            "format": "mp3",
            "max_length": 500,  # Small chunks to force splitting
            "preserve_words": True
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 200)
        
        # Should have combined multiple chunks
        chunks_combined = int(response.headers.get('X-Chunks-Combined', '0'))
        self.assertGreater(chunks_combined, 1)
        
        # Should have audio data
        self.assertGreater(len(response.content), 0)
        
        # Should have correct headers
        self.assertEqual(response.headers.get('X-Audio-Format'), 'mp3')
        self.assertEqual(response.headers.get('X-Original-Text-Length'), str(len(self.long_text)))
    
    def test_openai_endpoint_short_text(self):
        """Test /v1/audio/speech-combined with short text."""
        url = f"{self.base_url}/v1/audio/speech-combined"
        payload = {
            "model": "gpt-4o-mini-tts",
            "input": self.short_text,
            "voice": "alloy",
            "response_format": "wav"
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Chunks-Combined'), '1')
        self.assertGreater(len(response.content), 0)
        self.assertEqual(response.headers.get('Content-Type'), 'audio/wav')
    
    def test_openai_endpoint_long_text(self):
        """Test /v1/audio/speech-combined with long text."""
        url = f"{self.base_url}/v1/audio/speech-combined"
        payload = {
            "model": "gpt-4o-mini-tts",
            "input": self.long_text,
            "voice": "echo",
            "response_format": "mp3",
            "max_length": 600
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 200)
        
        chunks_combined = int(response.headers.get('X-Chunks-Combined', '0'))
        self.assertGreater(chunks_combined, 1)
        self.assertGreater(len(response.content), 0)
    
    def test_different_voices(self):
        """Test combined audio with different voices."""
        url = f"{self.base_url}/api/generate-combined"
        
        for voice in self.test_voices:
            with self.subTest(voice=voice):
                payload = {
                    "text": self.long_text,
                    "voice": voice,
                    "format": "mp3",
                    "max_length": 800
                }
                
                response = requests.post(url, json=payload, timeout=self.timeout)
                
                self.assertEqual(response.status_code, 200)
                self.assertGreater(len(response.content), 0)
    
    def test_different_formats(self):
        """Test combined audio with different formats."""
        url = f"{self.base_url}/api/generate-combined"
        
        for format_type in self.test_formats:
            with self.subTest(format=format_type):
                payload = {
                    "text": self.long_text,
                    "voice": "alloy",
                    "format": format_type,
                    "max_length": 700
                }
                
                response = requests.post(url, json=payload, timeout=self.timeout)
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers.get('X-Audio-Format'), format_type)
                self.assertGreater(len(response.content), 0)
    
    def test_custom_instructions(self):
        """Test combined audio with custom instructions."""
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": self.long_text,
            "voice": "nova",
            "format": "mp3",
            "instructions": "Please speak slowly and clearly for educational content.",
            "max_length": 600
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
    
    def test_error_handling_empty_text(self):
        """Test error handling for empty text."""
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": "",
            "voice": "alloy",
            "format": "mp3"
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("error", error_data)
    
    def test_error_handling_invalid_voice(self):
        """Test error handling for invalid voice."""
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": self.short_text,
            "voice": "invalid_voice",
            "format": "mp3"
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("error", error_data)
    
    def test_error_handling_invalid_format(self):
        """Test error handling for invalid format."""
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": self.short_text,
            "voice": "alloy",
            "format": "invalid_format"
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("error", error_data)
    
    def test_openai_error_format(self):
        """Test that OpenAI endpoint returns proper error format."""
        url = f"{self.base_url}/v1/audio/speech-combined"
        payload = {
            "model": "gpt-4o-mini-tts",
            "input": "",  # Empty input should cause error
            "voice": "alloy"
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("error", error_data)
        self.assertIn("message", error_data["error"])
        self.assertIn("type", error_data["error"])
        self.assertIn("code", error_data["error"])
    
    def test_content_disposition_header(self):
        """Test that proper Content-Disposition header is set."""
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": self.short_text,
            "voice": "alloy",
            "format": "mp3"
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 200)
        content_disposition = response.headers.get('Content-Disposition')
        self.assertIsNotNone(content_disposition)
        self.assertIn('attachment', content_disposition)
        self.assertIn('combined_speech.mp3', content_disposition)
    
    def test_audio_file_integrity(self):
        """Test that generated audio files can be saved and are valid."""
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": self.long_text,
            "voice": "alloy",
            "format": "mp3",
            "max_length": 500
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 200)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        try:
            # Check file exists and has content
            self.assertTrue(os.path.exists(temp_file_path))
            file_size = os.path.getsize(temp_file_path)
            self.assertGreater(file_size, 0)
            
            # Check that reported size matches actual size
            reported_size = response.headers.get('Content-Length')
            if reported_size:
                self.assertEqual(int(reported_size), file_size)
        
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_performance_large_text(self):
        """Test performance with large text input."""
        # Create a very long text
        very_long_text = self.long_text * 10  # Very long text
        
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": very_long_text,
            "voice": "alloy",
            "format": "mp3",
            "max_length": 1000
        }
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=120)  # Longer timeout
        processing_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        
        chunks_combined = int(response.headers.get('X-Chunks-Combined', '0'))
        self.assertGreater(chunks_combined, 5)  # Should be many chunks
        
        # Performance check - should complete within reasonable time
        self.assertLess(processing_time, 120)  # Should complete within 2 minutes
        
        print(f"\nPerformance test: {len(very_long_text)} chars -> {chunks_combined} chunks in {processing_time:.2f}s")
    
    def test_unicode_text_handling(self):
        """Test handling of Unicode text."""
        unicode_text = """
        Hello 世界! This is a test with émojis 🎵 and special characters: àáâãäå.
        The system should handle Unicode text properly in the combined audio generation.
        Testing with various scripts: Русский текст, العربية, 日本語, 한국어.
        """ * 3
        
        url = f"{self.base_url}/api/generate-combined"
        payload = {
            "text": unicode_text,
            "voice": "alloy",
            "format": "mp3",
            "max_length": 200
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import threading
        import queue
        
        url = f"{self.base_url}/api/generate-combined"
        results = queue.Queue()
        
        def make_request(thread_id):
            payload = {
                "text": f"This is test request number {thread_id}. " + self.long_text,
                "voice": "alloy",
                "format": "mp3",
                "max_length": 600
            }
            
            try:
                response = requests.post(url, json=payload, timeout=60)
                results.put((thread_id, response.status_code, len(response.content)))
            except Exception as e:
                results.put((thread_id, 500, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(3):  # Test with 3 concurrent requests
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        successful_requests = 0
        while not results.empty():
            thread_id, status_code, content_length = results.get()
            if status_code == 200:
                successful_requests += 1
                self.assertGreater(content_length, 0)
        
        # At least some requests should succeed
        self.assertGreater(successful_requests, 0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
