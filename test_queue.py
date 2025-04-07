"""
Queue Test Script for TTSFM

This script tests the queue functionality by sending 50 concurrent requests.
Run with: python test_queue.py
"""

import requests
import concurrent.futures
import time
import os
from pathlib import Path
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:7000"
TEST_TEXT = "This is a queue test request."
TEST_VOICE = "alloy"
NUM_REQUESTS = 50

# Create test output directory
TEST_OUTPUT_DIR = Path("test_output")
TEST_OUTPUT_DIR.mkdir(exist_ok=True)

def make_request(request_id: int) -> Dict[str, Any]:
    """Make a single TTS request and save the audio file"""
    try:
        response = requests.post(
            f"{BASE_URL}/v1/audio/speech",
            json={
                "input": f"{TEST_TEXT} Request #{request_id}",
                "voice": TEST_VOICE
            }
        )
        
        # Save the audio file if request was successful
        if response.status_code == 200:
            audio_path = TEST_OUTPUT_DIR / f"request_{request_id}.mp3"
            with open(audio_path, "wb") as f:
                f.write(response.content)
        
        return {
            "id": request_id,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "queue_size": response.headers.get("X-Queue-Size", "N/A"),
            "file_saved": response.status_code == 200
        }
    except Exception as e:
        return {
            "id": request_id,
            "error": str(e),
            "success": False,
            "file_saved": False
        }

def main():
    """Main function to run queue tests"""
    print(f"Starting queue test with {NUM_REQUESTS} concurrent requests...")
    print(f"Base URL: {BASE_URL}")
    print(f"Output directory: {TEST_OUTPUT_DIR.absolute()}")
    print("=" * 50)

    # Get initial queue status
    initial_status = requests.get(f"{BASE_URL}/api/queue-size").json()
    print(f"Initial queue status: {initial_status['queue_size']}/{initial_status['max_queue_size']}")

    # Start timer
    start_time = time.time()

    # Send requests concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_REQUESTS) as executor:
        futures = [executor.submit(make_request, i) for i in range(NUM_REQUESTS)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    # Calculate statistics
    end_time = time.time()
    duration = end_time - start_time
    successful = sum(1 for r in results if r["success"])
    failed = NUM_REQUESTS - successful
    files_saved = sum(1 for r in results if r["file_saved"])

    # Print results
    print("\nTest Results:")
    print("=" * 50)
    print(f"Total requests: {NUM_REQUESTS}")
    print(f"Successful requests: {successful}")
    print(f"Failed requests: {failed}")
    print(f"Files saved: {files_saved}")
    print(f"Total time: {duration:.2f} seconds")
    print(f"Average time per request: {duration/NUM_REQUESTS:.2f} seconds")

    # Get final queue status
    final_status = requests.get(f"{BASE_URL}/api/queue-size").json()
    print(f"\nFinal queue status: {final_status['queue_size']}/{final_status['max_queue_size']}")

    # Print detailed results for failed requests
    if failed > 0:
        print("\nFailed Requests:")
        print("=" * 50)
        for result in results:
            if not result["success"]:
                print(f"Request #{result['id']}: Status {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")

    print(f"\nAll generated MP3 files have been saved to: {TEST_OUTPUT_DIR.absolute()}")

if __name__ == "__main__":
    main() 