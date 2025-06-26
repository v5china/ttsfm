#!/usr/bin/env python3
"""
Example demonstrating the new combined audio functionality in TTSFM.

This example shows how to use the new combined audio endpoints to generate
a single audio file from long text that exceeds the standard character limits.
"""

import requests
import json
import time
from pathlib import Path

def example_combined_audio_api():
    """Example using the native TTSFM combined audio API."""
    
    print("🎵 TTSFM Combined Audio API Example")
    print("=" * 50)
    
    # Long text example - a sample article about AI
    long_text = """
    Artificial Intelligence has revolutionized the way we interact with technology and process information. 
    From simple chatbots to complex machine learning algorithms, AI has become an integral part of our daily lives.
    
    The field of AI encompasses various subdomains including natural language processing, computer vision, 
    robotics, and machine learning. Each of these areas contributes to creating intelligent systems that 
    can understand, learn, and adapt to new situations.
    
    Natural Language Processing, or NLP, focuses on enabling computers to understand and generate human language. 
    This technology powers virtual assistants, translation services, and text-to-speech systems like the one 
    you're listening to right now. The ability to convert text to natural-sounding speech has opened up new 
    possibilities for accessibility and content consumption.
    
    Machine learning algorithms learn patterns from data and make predictions or decisions without being 
    explicitly programmed for every scenario. This capability has led to breakthroughs in image recognition, 
    recommendation systems, and autonomous vehicles.
    
    Computer vision enables machines to interpret and understand visual information from the world around them. 
    This technology is used in medical imaging, security systems, and augmented reality applications.
    
    Robotics combines AI with physical systems to create machines that can interact with the physical world. 
    From manufacturing robots to household assistants, robotics is transforming industries and daily life.
    
    The future of AI holds even more exciting possibilities. As we continue to advance these technologies, 
    we can expect to see more sophisticated AI systems that can understand context, show creativity, and 
    work collaboratively with humans to solve complex problems.
    
    However, with these advances come important considerations about ethics, privacy, and the responsible 
    development of AI systems. It's crucial that we develop AI in a way that benefits humanity while 
    addressing potential risks and challenges.
    
    The integration of AI into various sectors including healthcare, education, finance, and entertainment 
    continues to create new opportunities and transform existing processes. As we move forward, the key 
    will be to harness the power of AI while ensuring it serves the greater good of society.
    """ * 2  # Repeat to ensure it's over the character limit
    
    print(f"📝 Text length: {len(long_text):,} characters")
    print(f"🎯 Target: Generate single combined audio file")
    print()
    
    # API endpoint
    url = "http://localhost:8000/api/generate-combined"
    
    # Request payload
    payload = {
        "text": long_text,
        "voice": "nova",  # Use Nova voice for this example
        "format": "mp3",
        "max_length": 1500,  # Smaller chunks for demonstration
        "preserve_words": True,
        "instructions": "Please speak clearly and at a moderate pace, suitable for educational content."
    }
    
    try:
        print("🚀 Sending request to combined audio endpoint...")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # Allow time for processing
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            # Save the combined audio file
            output_file = "ai_article_combined.mp3"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            # Extract metadata from headers
            chunks_combined = response.headers.get('X-Chunks-Combined', 'Unknown')
            audio_size = response.headers.get('X-Audio-Size', len(response.content))
            original_length = response.headers.get('X-Original-Text-Length', len(long_text))
            audio_format = response.headers.get('X-Audio-Format', 'mp3')
            
            print("✅ SUCCESS!")
            print(f"   📁 File saved: {output_file}")
            print(f"   📊 File size: {len(response.content):,} bytes")
            print(f"   🧩 Chunks combined: {chunks_combined}")
            print(f"   📝 Original text: {original_length} characters")
            print(f"   🎵 Audio format: {audio_format.upper()}")
            print(f"   ⏱️  Processing time: {processing_time:.2f} seconds")
            
            # Calculate estimated duration (rough approximation)
            estimated_duration = int(long_text.split()) / 150 * 60  # ~150 words per minute
            print(f"   🕐 Estimated duration: {estimated_duration:.1f} seconds")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure TTSFM web server is running on http://localhost:8000")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long. Try with shorter text or increase timeout.")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def example_openai_compatible():
    """Example using the OpenAI-compatible combined audio endpoint."""
    
    print("\n🤖 OpenAI-Compatible Combined Audio Example")
    print("=" * 50)
    
    # Shorter text for this example
    text = """
    Welcome to the future of text-to-speech technology. This demonstration showcases 
    the ability to generate high-quality, natural-sounding speech from text using 
    advanced AI models. The system can handle long texts by intelligently splitting 
    them into manageable chunks and then combining the resulting audio into a single, 
    seamless file. This approach ensures that you get the best of both worlds: 
    the ability to process long content while maintaining the natural flow and 
    quality of the generated speech.
    """ * 8  # Make it long enough to require splitting
    
    print(f"📝 Text length: {len(text):,} characters")
    
    # OpenAI-compatible endpoint
    url = "http://localhost:8000/v1/audio/speech-combined"
    
    payload = {
        "model": "gpt-4o-mini-tts",
        "input": text,
        "voice": "alloy",
        "response_format": "wav",
        "max_length": 800,  # Small chunks for demo
        "instructions": "Speak in a friendly, professional tone suitable for a technology demonstration."
    }
    
    try:
        print("🚀 Sending request to OpenAI-compatible endpoint...")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=90
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            output_file = "demo_openai_combined.wav"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            chunks_combined = response.headers.get('X-Chunks-Combined', 'Unknown')
            
            print("✅ SUCCESS!")
            print(f"   📁 File saved: {output_file}")
            print(f"   📊 File size: {len(response.content):,} bytes")
            print(f"   🧩 Chunks combined: {chunks_combined}")
            print(f"   ⏱️  Processing time: {processing_time:.2f} seconds")
            print(f"   🎵 Format: WAV (high quality)")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def compare_with_batch_processing():
    """Compare combined audio with batch processing."""
    
    print("\n📊 Comparison: Combined vs Batch Processing")
    print("=" * 50)
    
    sample_text = """
    This is a comparison between the batch processing endpoint and the new combined audio endpoint. 
    The batch processing endpoint returns multiple separate audio files, one for each chunk of text. 
    This is useful when you want to process each chunk individually or when you need fine-grained 
    control over the audio segments. On the other hand, the combined audio endpoint takes those 
    same chunks and merges them into a single, seamless audio file, which is perfect for creating 
    audiobooks, podcasts, or any content where you want a continuous listening experience.
    """ * 3
    
    print(f"📝 Sample text: {len(sample_text)} characters")
    print()
    
    # Test batch processing
    print("🔄 Testing batch processing...")
    batch_url = "http://localhost:8000/api/generate-batch"
    batch_payload = {
        "text": sample_text,
        "voice": "echo",
        "format": "mp3",
        "max_length": 500
    }
    
    try:
        batch_response = requests.post(batch_url, json=batch_payload, timeout=60)
        if batch_response.status_code == 200:
            batch_data = batch_response.json()
            print(f"   ✅ Batch: {batch_data['total_chunks']} separate audio files")
        else:
            print(f"   ❌ Batch failed: {batch_response.status_code}")
    except Exception as e:
        print(f"   ❌ Batch error: {e}")
    
    # Test combined processing
    print("🎵 Testing combined processing...")
    combined_url = "http://localhost:8000/api/generate-combined"
    combined_payload = {
        "text": sample_text,
        "voice": "echo",
        "format": "mp3",
        "max_length": 500
    }
    
    try:
        combined_response = requests.post(combined_url, json=combined_payload, timeout=60)
        if combined_response.status_code == 200:
            chunks = combined_response.headers.get('X-Chunks-Combined', 'Unknown')
            size = len(combined_response.content)
            print(f"   ✅ Combined: {chunks} chunks merged into 1 file ({size:,} bytes)")
            
            # Save for comparison
            with open("comparison_combined.mp3", "wb") as f:
                f.write(combined_response.content)
                
        else:
            print(f"   ❌ Combined failed: {combined_response.status_code}")
    except Exception as e:
        print(f"   ❌ Combined error: {e}")

if __name__ == "__main__":
    print("🎵 TTSFM Combined Audio Examples")
    print("=" * 60)
    print("This script demonstrates the new combined audio functionality.")
    print("Make sure the TTSFM web server is running on http://localhost:8000")
    print()
    
    # Run examples
    example_combined_audio_api()
    example_openai_compatible()
    compare_with_batch_processing()
    
    print("\n🎉 Examples completed!")
    print("\nGenerated files:")
    print("- ai_article_combined.mp3 (long article example)")
    print("- demo_openai_combined.wav (OpenAI-compatible example)")
    print("- comparison_combined.mp3 (comparison example)")
    print("\nYou can play these files to hear the combined audio results!")
