#!/usr/bin/env python3
"""
Optimized WebSocket TTS Streaming with OPUS format

Uses OPUS format for excellent quality with small file sizes - perfect for streaming!
"""

import asyncio
import socketio
import subprocess
import os
import time
from datetime import datetime
import platform

# Configuration
WEBSOCKET_URL = "http://192.168.1.102:8000"
OUTPUT_DIR = "websocket_audio_output"

# Test text - let's use a longer one for better testing
LONG_TEST_TEXT = """
The sun was setting over the distant mountains, painting the sky in brilliant shades of orange, pink, and purple. Sarah stood at the edge of the cliff, her hair dancing in the gentle evening breeze. She had been hiking for hours, following the winding trail that led through dense forests and across babbling brooks. The journey had been challenging, but the view from this vantage point made every step worthwhile.

Below her, the valley stretched out like a vast green carpet, dotted with tiny houses that looked like miniature toys from this height. A river snaked through the landscape, its waters glinting like liquid silver in the fading light. She could hear the distant call of an eagle soaring high above, its majestic wings cutting through the air with effortless grace.

As she reached into her backpack for her water bottle, Sarah reflected on the events that had brought her to this moment. Six months ago, she had been stuck in a corporate job that drained her soul, spending countless hours in a gray cubicle staring at spreadsheets. The decision to quit hadn't been easy, but something inside her had whispered that life held more than quarterly reports and board meetings.

Her friends had thought she was crazy when she announced her plan to hike the entire Pacific Crest Trail. "You're throwing away your career," they had warned. But Sarah knew that sometimes you had to take risks to find what truly mattered. She had sold most of her possessions, keeping only the essentials, and set out on this adventure with nothing but determination and a well-worn map.

The first few weeks had been the hardest. Her feet had blistered, her muscles had ached, and there were nights when she questioned her decision as she lay in her tent listening to the rain patter against the fabric. But gradually, her body had adapted, growing stronger with each passing day. More importantly, her mind had found a peace she hadn't experienced in years.

She had met fascinating people along the way - fellow hikers from around the world, each with their own stories and reasons for being on the trail. There was Marcus, the retired teacher from Germany who was fulfilling a lifelong dream. There was Yuki, the young artist from Japan who sketched the landscapes they passed through. And there was Elena, the grandmother from Spain who proved that age was just a number when it came to pursuing adventures.

Now, as Sarah watched the sun dip lower toward the horizon, she felt a profound sense of gratitude wash over her. The corporate world seemed like a distant memory, a previous life that belonged to someone else. Out here, surrounded by nature's grandeur, she had discovered who she really was beneath all the societal expectations and self-imposed limitations.
"""

class OptimizedStreamingClient:
    def __init__(self, output_dir):
        self.sio = socketio.AsyncClient()
        self.output_dir = output_dir
        self.chunk_queue = asyncio.Queue()
        self.is_playing = False
        self.chunk_count = 0
        self.total_size = 0
        self.start_time = None
        self.is_complete = False
        self.player_task = None
        self.format_info = {
            'mp3': {'quality': 'Good', 'size': 'Small', 'players': ['mpg123', 'ffplay', 'afplay']},
            'opus': {'quality': 'Excellent', 'size': 'Small', 'players': ['opusdec', 'ffplay', 'mpv']},
            'aac': {'quality': 'Good', 'size': 'Medium', 'players': ['ffplay', 'afplay', 'mpv']},
            'flac': {'quality': 'Lossless', 'size': 'Large', 'players': ['flac', 'ffplay', 'afplay']},
            'wav': {'quality': 'Lossless', 'size': 'Large', 'players': ['aplay', 'afplay', 'ffplay']},
            'pcm': {'quality': 'Raw', 'size': 'Large', 'players': ['aplay', 'ffplay']}
        }
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Register event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('stream_started', self.on_stream_started)
        self.sio.on('audio_chunk', self.on_audio_chunk)
        self.sio.on('stream_progress', self.on_stream_progress)
        self.sio.on('stream_complete', self.on_stream_complete)
        self.sio.on('stream_error', self.on_stream_error)
    
    async def on_connect(self):
        print(f"✅ Connected to WebSocket server")
        print(f"   Session ID: {self.sio.sid}")
    
    async def on_disconnect(self):
        print("\n❌ Disconnected from WebSocket server")
    
    async def on_stream_started(self, data):
        print(f"\n🎬 Stream started!")
        print(f"   Request ID: {data['request_id']}")
        self.start_time = time.time()
        
        # Start the audio player task
        self.player_task = asyncio.create_task(self.audio_player_task())
    
    async def on_audio_chunk(self, data):
        self.chunk_count += 1
        chunk_index = data['chunk_index'] + 1
        total_chunks = data['total_chunks']
        
        # Convert hex string back to bytes
        try:
            audio_bytes = bytes.fromhex(data['audio_data'])
            chunk_size = len(audio_bytes)
            self.total_size += chunk_size
            
            # Save to file
            format_ext = data['format']
            filename = f"{self.output_dir}/chunk_{chunk_index:02d}_of_{total_chunks}.{format_ext}"
            
            with open(filename, 'wb') as f:
                f.write(audio_bytes)
            
            # Add to playback queue
            await self.chunk_queue.put((chunk_index, filename, format_ext))
            
            # Get format info
            format_details = self.format_info.get(format_ext, {})
            
            print(f"\n📦 Chunk {chunk_index}/{total_chunks} received")
            print(f"   Format: {format_ext} ({format_details.get('quality', 'Unknown')} quality, {format_details.get('size', 'Unknown')} size)")
            print(f"   Size: {chunk_size:,} bytes ({chunk_size/1024:.1f} KB)")
            print(f"   Duration: {data.get('duration', 0):.2f}s")
            print(f"   Generation time: {data.get('generation_time', 0):.2f}s")
            
            # Show text preview
            chunk_text = data.get('chunk_text', '')
            if chunk_text:
                print(f"   Text: \"{chunk_text}\"")
                
        except Exception as e:
            print(f"\n❌ Error processing chunk {chunk_index}: {e}")
    
    async def on_stream_progress(self, data):
        progress = data['progress']
        chunks_completed = data.get('chunks_completed', 0)
        total_chunks = data.get('total_chunks', 0)
        
        # Create progress bar
        bar_length = 40
        filled_length = int(bar_length * progress / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print(f"\r⏳ Streaming: [{bar}] {progress}% - {chunks_completed}/{total_chunks} chunks - {elapsed:.1f}s", end='', flush=True)
    
    async def on_stream_complete(self, data):
        total_time = time.time() - self.start_time if self.start_time else 0
        
        print(f"\n\n✅ Stream completed!")
        print(f"   Total chunks: {data['total_chunks']}")
        print(f"   Total size: {self.total_size:,} bytes ({self.total_size/1024:.1f} KB / {self.total_size/1024/1024:.2f} MB)")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average speed: {self.total_size/1024/total_time:.1f} KB/s")
        
        self.is_complete = True
        
        # Signal end of stream to player
        await self.chunk_queue.put(None)
    
    async def on_stream_error(self, data):
        print(f"\n\n❌ Stream error: {data.get('error', 'Unknown error')}")
        self.is_complete = True
        await self.chunk_queue.put(None)
    
    async def audio_player_task(self):
        """Background task to play audio chunks as they arrive"""
        print("\n🎵 Audio player started, waiting for chunks...")
        
        while True:
            try:
                # Wait for next chunk
                item = await self.chunk_queue.get()
                
                if item is None:  # End signal
                    print("\n🏁 Audio player finished")
                    break
                
                chunk_index, filename, format_ext = item
                
                # Play the chunk
                print(f"\n🔊 Playing chunk {chunk_index}...")
                await self.play_audio_file(filename, format_ext)
                
            except Exception as e:
                print(f"\n❌ Player error: {e}")
    
    async def play_audio_file(self, filename, format_ext):
        """Play audio file using appropriate player for the format"""
        try:
            system = platform.system()
            
            # Get recommended players for this format
            format_players = self.format_info.get(format_ext, {}).get('players', [])
            
            # Platform-specific player selection
            if system == "Darwin":  # macOS
                # macOS has afplay which works with most formats
                if 'afplay' in format_players:
                    cmd = ["afplay", filename]
                else:
                    cmd = ["ffplay", "-nodisp", "-autoexit", filename]
            
            elif system == "Linux":
                # Try format-specific players first
                cmd = None
                for player in format_players:
                    if subprocess.run(["which", player], capture_output=True).returncode == 0:
                        if player == "ffplay":
                            cmd = [player, "-nodisp", "-autoexit", filename]
                        elif player == "opusdec":
                            # For OPUS, decode to stdout and pipe to aplay
                            cmd = ["sh", "-c", f"opusdec {filename} - | aplay -q"]
                        else:
                            cmd = [player, filename]
                        break
                
                if not cmd:
                    print(f"   ⚠️  No suitable player found for {format_ext}. File saved: {filename}")
                    return
            
            elif system == "Windows":
                # Windows Media Player
                cmd = ["powershell", "-c", f"(New-Object Media.SoundPlayer '{filename}').PlaySync()"]
            
            else:
                print(f"   ⚠️  Unsupported OS. File saved: {filename}")
                return
            
            # Play the audio
            print(f"   ▶️  Playing with: {' '.join(cmd[:2])}...")
            process = await asyncio.create_subprocess_exec(
                *cmd if isinstance(cmd[0], str) else cmd[0],
                shell=isinstance(cmd[0], str) and ' ' in cmd[0],
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
            print(f"   ✅ Finished playing chunk")
            
        except Exception as e:
            print(f"   ⚠️  Error playing audio: {e}")
            print(f"   File saved: {filename}")
    
    async def test_streaming(self, text, voice='alloy', format_type='opus', chunk_size=512):
        """Test WebSocket streaming with optimal settings"""
        # Connect to server
        print(f"🔌 Connecting to {WEBSOCKET_URL}...")
        await self.sio.connect(WEBSOCKET_URL)
        
        # Wait for connection
        await asyncio.sleep(0.5)
        
        # Generate request ID
        import random
        import string
        request_id = f"req_{int(time.time() * 1000)}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
        
        format_details = self.format_info.get(format_type, {})
        
        print(f"\n📤 Requesting TTS generation...")
        print(f"   Request ID: {request_id}")
        print(f"   Text length: {len(text)} characters")
        print(f"   Expected chunks: ~{(len(text) + chunk_size - 1) // chunk_size}")
        print(f"   Voice: {voice}")
        print(f"   Format: {format_type} ({format_details.get('quality', 'Unknown')} quality, {format_details.get('size', 'Unknown')} size)")
        print(f"   Chunk size: {chunk_size} characters")
        print("-" * 70)
        
        # Send generation request
        await self.sio.emit('generate_stream', {
            'request_id': request_id,
            'text': text,
            'voice': voice,
            'format': format_type,
            'chunk_size': chunk_size
        })
        
        # Wait for completion
        try:
            wait_time = 0
            while self.sio.connected and not self.is_complete and wait_time < 180:  # 3 minute timeout
                await asyncio.sleep(0.5)
                wait_time += 0.5
            
            if wait_time >= 180:
                print("\n\n⏱️  Timeout after 3 minutes")
            
            # Wait for the audio player to finish all chunks
            if self.player_task:
                print("\n\n🎵 Waiting for audio playback to complete...")
                try:
                    await self.player_task
                except Exception as e:
                    print(f"Player task error: {e}")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped by user")
        finally:
            if self.sio.connected:
                await self.sio.disconnect()

async def main():
    print("=" * 80)
    print("   🎯 TTSFM Optimized WebSocket Streaming Test - Real-time Audio Playback")
    print("=" * 80)
    print("\nFormat Comparison:")
    print("Format  | Quality    | File Size | Best For")
    print("--------|------------|-----------|---------------------------")
    print("OPUS    | Excellent  | Small     | Streaming (recommended)")
    print("MP3     | Good       | Small     | General use")
    print("AAC     | Good       | Medium    | Apple devices")
    print("WAV     | Lossless   | Large     | Professional (not for streaming)")
    print("=" * 80)
    
    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{OUTPUT_DIR}/{timestamp}"
    
    client = OptimizedStreamingClient(output_dir)
    
    try:
        # Format selection
        formats = ['opus', 'mp3', 'aac', 'wav']
        print("\nSelect audio format:")
        for i, fmt in enumerate(formats, 1):
            info = client.format_info.get(fmt, {})
            print(f"  {i}. {fmt.upper()} - {info.get('quality', 'Unknown')} quality, {info.get('size', 'Unknown')} size")
        
        fmt_choice = input("\nFormat choice (1-4, default=1 for OPUS): ").strip()
        
        if fmt_choice.isdigit() and 1 <= int(fmt_choice) <= 4:
            selected_format = formats[int(fmt_choice) - 1]
        else:
            selected_format = 'opus'  # Default to OPUS for best streaming
        
        # Voice selection
        voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        print("\nSelect voice:")
        for i, voice in enumerate(voices, 1):
            print(f"  {i}. {voice}")
        
        voice_choice = input("\nVoice choice (1-6, default=1): ").strip()
        
        if voice_choice.isdigit() and 1 <= int(voice_choice) <= 6:
            selected_voice = voices[int(voice_choice) - 1]
        else:
            selected_voice = 'alloy'
        
        # Chunk size selection
        print("\nSelect chunk size:")
        print("  1. Small (256 chars) - More chunks, smoother streaming")
        print("  2. Medium (512 chars) - Balanced")
        print("  3. Large (1024 chars) - Fewer chunks, less overhead")
        
        size_choice = input("\nChunk size (1-3, default=2): ").strip()
        chunk_sizes = [256, 512, 1024]
        
        if size_choice.isdigit() and 1 <= int(size_choice) <= 3:
            selected_chunk_size = chunk_sizes[int(size_choice) - 1]
        else:
            selected_chunk_size = 512
        
        print(f"\n🎙️  Settings: Voice={selected_voice}, Format={selected_format.upper()}, Chunk size={selected_chunk_size}")
        
        # Test with the long text
        await client.test_streaming(
            LONG_TEST_TEXT, 
            voice=selected_voice, 
            format_type=selected_format,
            chunk_size=selected_chunk_size
        )
        
        print(f"\n📁 Audio files saved in: {output_dir}/")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 Test completed!")

if __name__ == "__main__":
    asyncio.run(main())