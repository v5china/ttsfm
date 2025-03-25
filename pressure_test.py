"""
Pressure Test for the OpenAI TTS API Server

This script sends concurrent requests to the API server to test its performance under load.
"""

import asyncio
import aiohttp
import json
import time
import random
import argparse
import statistics
from datetime import datetime
from pathlib import Path

# Test sample texts of varying lengths
SHORT_TEXT = "Hello, this is a short test message."
MEDIUM_TEXT = "This is a medium length message that contains more words and will generate a longer audio file. It should take more time to process than the shorter message."
LONG_TEXT = """This is a much longer message that will result in a significantly larger audio output. 
It contains multiple sentences and will take more processing time. When we test with longer inputs like this,
we can better evaluate how the server performs under more demanding conditions. This helps identify potential 
bottlenecks in the processing pipeline. The server should be able to handle requests of varying sizes without issues."""

# Available voices to cycle through
VOICES = ["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"]

async def send_request(session, url, voice, text_length, request_num, save_dir=None):
    """Send a single API request and return metrics."""
    
    start_time = time.time()
    request_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # Select the appropriate text based on the length parameter
    if text_length == "short":
        text = SHORT_TEXT
    elif text_length == "medium":
        text = MEDIUM_TEXT
    else:
        text = LONG_TEXT
    
    # Prepare the request payload
    payload = {
        "input": text,
        "model": "tts-1",
        "voice": voice,
        "speed": 1.0
    }
    
    try:
        print(f"[{request_time}] Starting request {request_num} with voice {voice}")
        
        async with session.post(
            url, 
            json=payload, 
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy-api-key"
            }
        ) as response:
            status = response.status
            content_type = response.headers.get('Content-Type', '')
            
            # Read binary audio data
            audio_data = await response.read()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Optionally save the audio file
            if save_dir and status == 200 and audio_data:
                save_path = Path(save_dir) / f"test_{request_num}_{voice}.mp3"
                with open(save_path, 'wb') as f:
                    f.write(audio_data)
                print(f"Saved audio to {save_path}")
            
            # Determine success based on response
            is_success = status == 200 and audio_data and len(audio_data) > 0
            
            result = {
                "request_num": request_num,
                "voice": voice,
                "text_length": text_length,
                "status": status,
                "duration": duration,
                "success": is_success,
                "timestamp": request_time,
                "content_type": content_type,
                "response_size": len(audio_data) if audio_data else 0
            }
            
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Request {request_num} completed: " +
                  f"Status {status}, Size: {len(audio_data)/1024:.1f} KB, Duration: {duration:.2f}s")
            
            return result
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Request {request_num} error: {str(e)}")
        
        return {
            "request_num": request_num,
            "voice": voice,
            "text_length": text_length,
            "status": 0,
            "duration": duration,
            "success": False,
            "timestamp": request_time,
            "error": str(e),
            "response_size": 0
        }

async def run_pressure_test(num_requests, concurrency, server_url, text_length="medium", save_audio=False):
    """Run the pressure test with the specified parameters."""
    
    if not server_url.endswith('/v1/audio/speech'):
        server_url = f"{server_url.rstrip('/')}/v1/audio/speech"
    
    # Create save directory if needed    
    save_dir = None
    if save_audio:
        save_dir = Path('test_output')
        save_dir.mkdir(exist_ok=True)
        
    print(f"Starting pressure test with {num_requests} total requests, {concurrency} concurrent connections")
    print(f"Server URL: {server_url}")
    print(f"Text length: {text_length}")
    if save_audio:
        print(f"Saving audio files to: {save_dir}")
    print("-" * 60)
    
    results = []
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(num_requests):
            # Cycle through different voices
            voice = VOICES[i % len(VOICES)]
            
            # Add a small delay between creating tasks to avoid overwhelming the server at startup
            await asyncio.sleep(0.05)
            
            task = asyncio.create_task(send_request(session, server_url, voice, text_length, i + 1, save_dir))
            tasks.append(task)
            
            # If we've reached the concurrency limit, wait for some tasks to complete
            if len(tasks) >= concurrency:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                results.extend([task.result() for task in done])
                tasks = list(pending)  # Convert the pending set back to a list
        
        # Wait for any remaining tasks
        if tasks:
            done, _ = await asyncio.wait(tasks)
            results.extend([task.result() for task in done])
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print(f"Pressure Test Results ({text_length} text)")
    print("=" * 60)
    
    # Calculate and display statistics
    successful_reqs = [r for r in results if r["success"]]
    failed_reqs = [r for r in results if not r["success"]]
    
    success_rate = len(successful_reqs) / num_requests * 100 if num_requests > 0 else 0
    
    # Calculate response time statistics
    if successful_reqs:
        durations = [r["duration"] for r in successful_reqs]
        avg_duration = statistics.mean(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        median_duration = statistics.median(durations)
        
        # Calculate response size statistics
        sizes = [r["response_size"] for r in successful_reqs]
        avg_size = statistics.mean(sizes) / 1024  # KB
        total_size = sum(sizes) / (1024 * 1024)  # MB
        
        print(f"Success Rate: {success_rate:.1f}% ({len(successful_reqs)}/{num_requests})")
        print(f"Total Test Duration: {total_duration:.2f} seconds")
        print(f"Average Response Time: {avg_duration:.3f} seconds")
        print(f"Median Response Time: {median_duration:.3f} seconds")
        print(f"Min Response Time: {min_duration:.3f} seconds")
        print(f"Max Response Time: {max_duration:.3f} seconds")
        print(f"Average Response Size: {avg_size:.1f} KB")
        print(f"Total Data Transferred: {total_size:.2f} MB")
        print(f"Requests per Second: {num_requests / total_duration:.2f}")
        print(f"Throughput: {(total_size * 8) / total_duration:.2f} Mbps")
    else:
        print(f"Success Rate: 0% (0/{num_requests})")
        print(f"Total Test Duration: {total_duration:.2f} seconds")
    
    # Show error breakdown if there are failures
    if failed_reqs:
        print("\nError Breakdown:")
        error_counts = {}
        for req in failed_reqs:
            error = req.get("error", f"HTTP {req['status']}")
            error_counts[error] = error_counts.get(error, 0) + 1
        
        for error, count in error_counts.items():
            print(f"  {error}: {count} occurrences")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pressure test for OpenAI TTS API Server")
    parser.add_argument("-n", "--num-requests", type=int, default=10, help="Total number of requests to send")
    parser.add_argument("-c", "--concurrency", type=int, default=2, help="Number of concurrent connections")
    parser.add_argument("-u", "--url", type=str, default="http://localhost:7000", help="Server URL")
    parser.add_argument("-t", "--text-length", type=str, choices=["short", "medium", "long"], default="medium", 
                        help="Length of text to use for testing")
    parser.add_argument("-s", "--save-audio", action="store_true", help="Save audio files to test_output directory")
    
    args = parser.parse_args()
    
    asyncio.run(run_pressure_test(
        args.num_requests, 
        args.concurrency, 
        args.url, 
        args.text_length,
        args.save_audio
    )) 