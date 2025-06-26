#!/usr/bin/env python3
"""
Test script for the new combined audio endpoint.

This script demonstrates how to use the new /api/generate-combined endpoint
to generate a single audio file from long text.
"""

import requests
import json
import sys
import os

def test_combined_endpoint():
    """Test the combined audio generation endpoint."""
    
    # Configuration
    base_url = "http://localhost:8000"
    endpoint = "/api/generate-combined"
    
    # Long text example (over 4096 characters)
    long_text = """
    This is a comprehensive test of the TTSFM combined audio generation functionality. 
    When you have text that exceeds the standard 4096 character limit, the new combined 
    endpoint will automatically split the text into smaller chunks, generate speech for 
    each chunk separately, and then combine all the audio chunks into a single, seamless 
    audio file.
    
    The text splitting algorithm is intelligent and preserves natural speech boundaries. 
    It first tries to split at sentence boundaries (periods, exclamation marks, question marks), 
    then falls back to word boundaries if sentences are too long, and only splits at character 
    boundaries as a last resort.
    
    This approach ensures that the generated speech sounds natural and flows smoothly from 
    one chunk to the next. The audio combination process uses advanced audio processing 
    techniques to merge the chunks without introducing artifacts or gaps.
    
    Key features of the combined audio generation:
    
    1. Automatic text splitting with intelligent boundary detection
    2. Parallel processing of audio chunks for faster generation
    3. Seamless audio combination using professional audio processing
    4. Support for all audio formats (MP3, WAV, OPUS, AAC, FLAC, PCM)
    5. Fallback mechanisms for environments without advanced audio libraries
    6. OpenAI-compatible API endpoints for easy integration
    7. Comprehensive error handling and logging
    8. Metadata headers indicating the number of chunks combined
    
    The system is designed to handle various use cases:
    - Converting long articles or blog posts to audio
    - Generating audiobooks from text chapters
    - Creating podcast content from written scripts
    - Processing educational materials for audio learning
    - Converting documentation to spoken format
    
    Performance considerations:
    - The system processes chunks concurrently when possible
    - Audio combination is optimized for minimal memory usage
    - Fallback methods ensure compatibility across different environments
    - Progress tracking and detailed logging for monitoring
    
    This functionality makes TTSFM suitable for enterprise applications that need to 
    process large volumes of text content into high-quality audio output.
    """ * 3  # Repeat to ensure it's definitely over 4096 characters
    
    print(f"Testing combined audio generation with {len(long_text)} characters of text")
    print(f"Endpoint: {base_url}{endpoint}")
    print()
    
    # Test data
    test_data = {
        "text": long_text,
        "voice": "alloy",
        "format": "mp3",
        "max_length": 2000,  # Smaller chunks for testing
        "preserve_words": True
    }
    
    try:
        print("Sending request to combined audio endpoint...")
        response = requests.post(
            f"{base_url}{endpoint}",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120  # Longer timeout for processing
        )
        
        if response.status_code == 200:
            # Success - save the audio file
            audio_data = response.content
            filename = "test_combined_output.mp3"
            
            with open(filename, 'wb') as f:
                f.write(audio_data)
            
            # Get metadata from headers
            chunks_combined = response.headers.get('X-Chunks-Combined', 'Unknown')
            audio_size = response.headers.get('X-Audio-Size', len(audio_data))
            original_text_length = response.headers.get('X-Original-Text-Length', len(long_text))
            
            print("✅ SUCCESS!")
            print(f"   Audio file saved: {filename}")
            print(f"   File size: {len(audio_data):,} bytes")
            print(f"   Chunks combined: {chunks_combined}")
            print(f"   Original text length: {original_text_length} characters")
            print(f"   Audio format: {response.headers.get('X-Audio-Format', 'mp3')}")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error message: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the server.")
        print("   Make sure the TTSFM web application is running on http://localhost:8000")
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out.")
        print("   The server might be processing a large request. Try again or increase timeout.")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_openai_compatible_endpoint():
    """Test the OpenAI-compatible combined endpoint."""
    
    base_url = "http://localhost:8000"
    endpoint = "/v1/audio/speech-combined"
    
    # Shorter text for OpenAI endpoint test
    text = """
    This is a test of the OpenAI-compatible combined audio endpoint. 
    This endpoint follows the OpenAI API format but adds the ability to handle long text 
    by automatically splitting and combining audio chunks. It's perfect for applications 
    that need OpenAI compatibility but want to process longer text content.
    """ * 5
    
    print(f"\nTesting OpenAI-compatible endpoint with {len(text)} characters")
    print(f"Endpoint: {base_url}{endpoint}")
    
    test_data = {
        "model": "gpt-4o-mini-tts",
        "input": text,
        "voice": "nova",
        "response_format": "mp3",
        "max_length": 1000
    }
    
    try:
        print("Sending request to OpenAI-compatible endpoint...")
        response = requests.post(
            f"{base_url}{endpoint}",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            audio_data = response.content
            filename = "test_openai_combined.mp3"
            
            with open(filename, 'wb') as f:
                f.write(audio_data)
            
            chunks_combined = response.headers.get('X-Chunks-Combined', 'Unknown')
            
            print("✅ SUCCESS!")
            print(f"   Audio file saved: {filename}")
            print(f"   File size: {len(audio_data):,} bytes")
            print(f"   Chunks combined: {chunks_combined}")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("TTSFM Combined Audio Endpoint Test")
    print("=" * 50)
    
    test_combined_endpoint()
    test_openai_compatible_endpoint()
    
    print("\nTest completed!")
    print("\nIf successful, you should have two audio files:")
    print("- test_combined_output.mp3 (from /api/generate-combined)")
    print("- test_openai_combined.mp3 (from /v1/audio/speech-combined)")
