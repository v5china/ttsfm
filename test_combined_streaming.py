#!/usr/bin/env python3
"""
Combined Chunks Streaming - Truly seamless audio

This version combines all chunks into one file before playing
for completely seamless audio.
"""

import asyncio
import socketio
import subprocess
import os
import time
from datetime import datetime
import tempfile

# Configuration
WEBSOCKET_URL = "http://192.168.1.100:8000"
OUTPUT_DIR = "websocket_audio_output"

# Test text - make it longer to really test seamless transitions
LONG_TEXT = """
In the beginning, there was silence. Then came the first words spoken by artificial intelligence, breaking through the barriers of traditional text-to-speech synthesis. These early systems, while functional, lacked the nuance and natural flow that human ears had grown accustomed to over millennia of evolutionary adaptation.

The challenge was not merely technical but fundamentally experiential. How could machines learn to speak with the same emotional resonance, the same subtle inflections, and the same seamless continuity that characterizes human communication? The answer lay not in perfecting individual sounds, but in understanding the complex orchestration of timing, rhythm, and flow.

Modern streaming synthesis represents a paradigm shift in this journey. By breaking down lengthy passages into manageable segments while maintaining acoustic coherence across boundaries, we achieve something previously thought impossible: truly natural-sounding artificial speech that flows as smoothly as a mountain stream over polished stones.

This is the future of voice technology, where the boundaries between human and artificial speech blur into irrelevance, leaving only the pure transmission of meaning from mind to mind.
"""

class CombinedStreamingClient:
    def __init__(self, output_dir):
        self.sio = socketio.AsyncClient()
        self.output_dir = output_dir
        self.chunks = {}  # Store all chunks
        self.total_chunks = 0
        self.is_complete = False
        self.start_time = None
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Register event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('stream_started', self.on_stream_started)
        self.sio.on('audio_chunk', self.on_audio_chunk)
        self.sio.on('stream_complete', self.on_stream_complete)
        self.sio.on('stream_error', self.on_stream_error)
    
    async def on_connect(self):
        print("✅ Connected to server")
    
    async def on_stream_started(self, data):
        print(f"🎬 Stream started: {data['request_id']}")
        self.start_time = time.time()
    
    async def on_audio_chunk(self, data):
        chunk_index = data['chunk_index']
        self.total_chunks = data['total_chunks']
        
        # Store chunk
        audio_bytes = bytes.fromhex(data['audio_data'])
        self.chunks[chunk_index] = audio_bytes
        
        print(f"📦 Received chunk {chunk_index + 1}/{self.total_chunks}: {len(audio_bytes)/1024:.1f}KB")
    
    async def on_stream_complete(self, data):
        total_time = time.time() - self.start_time if self.start_time else 0
        print(f"✅ All chunks received in {total_time:.2f}s")
        self.is_complete = True
        
        # Combine and play all chunks
        await self.combine_and_play()
    
    async def on_stream_error(self, data):
        print(f"❌ Error: {data.get('error')}")
        self.is_complete = True
    
    async def combine_and_play(self):
        """Combine all chunks into one seamless audio file"""
        print("\n🔧 Combining chunks for seamless playback...")
        
        # Create temporary files for each chunk in order
        temp_files = []
        for i in range(self.total_chunks):
            if i in self.chunks:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.opus')
                temp_file.write(self.chunks[i])
                temp_file.close()
                temp_files.append(temp_file.name)
        
        if not temp_files:
            print("❌ No chunks to combine")
            return
        
        # Method 1: Binary concatenation (works for some formats)
        if len(temp_files) == 1:
            # Single chunk, just play it
            combined_file = temp_files[0]
        else:
            # Multiple chunks - combine them
            print(f"   🔗 Combining {len(temp_files)} chunks...")
            combined_file = f"{self.output_dir}/combined_seamless.opus"
            
            # Simple binary concatenation for OPUS (may work)
            with open(combined_file, 'wb') as outfile:
                for temp_file in temp_files:
                    with open(temp_file, 'rb') as infile:
                        outfile.write(infile.read())
            
            # If that doesn't work well, try ffmpeg method
            if os.path.exists(combined_file):
                # Verify the combined file is valid
                test_cmd = ['ffprobe', '-v', 'quiet', combined_file]
                if subprocess.run(test_cmd, capture_output=True).returncode != 0:
                    print("   🔧 Binary concat failed, trying ffmpeg...")
                    await self.ffmpeg_combine(temp_files, combined_file)
        
        # Play the combined file
        print(f"🎵 Playing seamless audio...")
        cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', combined_file]
        
        process = subprocess.Popen(cmd)
        process.wait()
        
        print("✅ Seamless playback complete!")
        
        # Cleanup
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    async def ffmpeg_combine(self, temp_files, output_file):
        """Use ffmpeg to properly combine audio files"""
        # Create concat file
        concat_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        for temp_file in temp_files:
            concat_file.write(f"file '{temp_file}'\n")
        concat_file.close()
        
        # Use ffmpeg to concatenate
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', concat_file.name,
            '-c', 'copy',  # Copy without re-encoding
            '-y', output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, stderr=subprocess.DEVNULL)
        os.unlink(concat_file.name)
        
        return result.returncode == 0
    
    async def test_combined_streaming(self, text, voice='nova', format_type='opus'):
        """Test combined streaming"""
        print(f"🔌 Connecting to {WEBSOCKET_URL}...")
        await self.sio.connect(WEBSOCKET_URL)
        await asyncio.sleep(0.5)
        
        request_id = f"combined_{int(time.time() * 1000)}"
        
        print(f"\n📤 Testing combined streaming...")
        print(f"   Text length: {len(text)} characters")
        print(f"   Voice: {voice}")
        print(f"   Format: {format_type}")
        print("-" * 60)
        
        # Send request with smaller chunks for more seams to test
        await self.sio.emit('generate_stream', {
            'request_id': request_id,
            'text': text,
            'voice': voice,
            'format': format_type,
            'chunk_size': 300,  # Smaller chunks = more potential gaps to eliminate
            'instructions': 'Smooth, natural narrative voice with consistent pacing'
        })
        
        # Wait for completion
        timeout = 45
        start = time.time()
        while not self.is_complete and (time.time() - start) < timeout:
            await asyncio.sleep(0.5)
        
        if not self.is_complete:
            print("⏱️  Timeout waiting for chunks")
        
        await self.sio.disconnect()

async def main():
    print("="*70)
    print("   🎵 COMBINED STREAMING TEST")
    print("="*70)
    print("\nThis combines all chunks into one file for truly seamless playback")
    print("="*70)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{OUTPUT_DIR}/combined_{timestamp}"
    
    client = CombinedStreamingClient(output_dir)
    
    try:
        await client.test_combined_streaming(LONG_TEXT)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✅ Test complete! Audio saved in: {output_dir}/")

if __name__ == "__main__":
    asyncio.run(main())