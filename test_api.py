"""
API Test Script for TTSFM

This script tests all API endpoints and functionality of the TTSFM server.
Run with: python test_api.py
"""

import os
import sys
import json
import time
import requests
import unittest
from pathlib import Path
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:7000"
TEST_TEXT = "Hello, this is a test of the TTS API."
TEST_VOICE = "alloy"
TEST_INSTRUCTIONS = "Speak in a cheerful and upbeat tone."

class TestTTSFM(unittest.TestCase):
    """Test suite for TTSFM API endpoints"""

    def setUp(self):
        """Set up test environment"""
        self.session = requests.Session()
        self.test_files_dir = Path("test_output")
        self.test_files_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        # Clean up test files
        for file in self.test_files_dir.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                print(f"Error cleaning up {file}: {e}")

    def test_01_queue_status(self):
        """Test queue status endpoint"""
        print("\nTesting queue status endpoint...")
        response = self.session.get(f"{BASE_URL}/api/queue-size")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("queue_size", data)
        self.assertIn("max_queue_size", data)
        print(f"Queue status: {data['queue_size']}/{data['max_queue_size']}")

    def test_02_voice_samples(self):
        """Test voice sample endpoint"""
        print("\nTesting voice sample endpoint...")
        response = self.session.get(f"{BASE_URL}/api/voice-sample/{TEST_VOICE}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "audio/mpeg")
        
        # Save the sample
        sample_path = self.test_files_dir / f"{TEST_VOICE}_sample.mp3"
        with open(sample_path, "wb") as f:
            f.write(response.content)
        print(f"Saved voice sample to {sample_path}")

    def test_03_basic_tts(self):
        """Test basic TTS generation"""
        print("\nTesting basic TTS generation...")
        response = self.session.post(
            f"{BASE_URL}/v1/audio/speech",
            json={
                "input": TEST_TEXT,
                "voice": TEST_VOICE
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "audio/mpeg")
        
        # Save the audio
        audio_path = self.test_files_dir / "basic_tts.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        print(f"Saved basic TTS to {audio_path}")

    def test_04_tts_with_instructions(self):
        """Test TTS generation with instructions"""
        print("\nTesting TTS with instructions...")
        response = self.session.post(
            f"{BASE_URL}/v1/audio/speech",
            json={
                "input": TEST_TEXT,
                "voice": TEST_VOICE,
                "instructions": TEST_INSTRUCTIONS
            }
        )
        self.assertEqual(response.status_code, 200)
        
        # Save the audio
        audio_path = self.test_files_dir / "tts_with_instructions.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        print(f"Saved TTS with instructions to {audio_path}")

    def test_05_different_formats(self):
        """Test TTS generation with different formats"""
        formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]
        print("\nTesting different audio formats...")
        
        for format in formats:
            print(f"Testing {format} format...")
            response = self.session.post(
                f"{BASE_URL}/v1/audio/speech",
                json={
                    "input": TEST_TEXT,
                    "voice": TEST_VOICE,
                    "response_format": format
                }
            )
            self.assertEqual(response.status_code, 200)
            
            # Save the audio
            audio_path = self.test_files_dir / f"tts_{format}.{format}"
            with open(audio_path, "wb") as f:
                f.write(response.content)
            print(f"Saved {format} format to {audio_path}")

    def test_06_rate_limiting(self):
        """Test rate limiting"""
        print("\nTesting rate limiting...")
        # Make multiple requests quickly
        for i in range(5):
            response = self.session.post(
                f"{BASE_URL}/v1/audio/speech",
                json={
                    "input": f"Rate limit test {i}",
                    "voice": TEST_VOICE
                }
            )
            if response.status_code == 429:
                print("Rate limit hit as expected")
                retry_after = int(response.headers.get("Retry-After", 0))
                print(f"Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                break
            time.sleep(0.5)  # Small delay between requests

    def test_07_error_handling(self):
        """Test error handling"""
        print("\nTesting error handling...")
        
        # Test missing required parameters
        response = self.session.post(
            f"{BASE_URL}/v1/audio/speech",
            json={"voice": TEST_VOICE}  # Missing input
        )
        self.assertEqual(response.status_code, 400)
        print("Missing parameter test passed")

        # Test invalid voice
        response = self.session.post(
            f"{BASE_URL}/v1/audio/speech",
            json={
                "input": TEST_TEXT,
                "voice": "invalid_voice"
            }
        )
        self.assertEqual(response.status_code, 400)
        print("Invalid voice test passed")

        # Test invalid format
        response = self.session.post(
            f"{BASE_URL}/v1/audio/speech",
            json={
                "input": TEST_TEXT,
                "voice": TEST_VOICE,
                "response_format": "invalid_format"
            }
        )
        self.assertEqual(response.status_code, 400)
        print("Invalid format test passed")

def main():
    """Main function to run tests"""
    print("Starting TTSFM API tests...")
    print(f"Base URL: {BASE_URL}")
    print("=" * 50)
    
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    print("\nTest Summary:")
    print("=" * 50)
    print("1. Queue Status: Tested")
    print("2. Voice Samples: Tested")
    print("3. Basic TTS: Tested")
    print("4. TTS with Instructions: Tested")
    print("5. Different Formats: Tested")
    print("6. Rate Limiting: Tested")
    print("7. Error Handling: Tested")
    print("\nCheck the 'test_output' directory for generated audio files.")

if __name__ == "__main__":
    main() 