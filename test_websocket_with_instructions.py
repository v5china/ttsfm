#!/usr/bin/env python3
"""
Advanced WebSocket TTS Streaming with Intelligent Voice Instructions

This demonstrates how voice instructions can transform TTS output
"""

import asyncio
import socketio
import re
import os
import time
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Configuration
WEBSOCKET_URL = "http://192.168.1.102:8000"
OUTPUT_DIR = "websocket_audio_output"

# Instruction Templates
INSTRUCTION_TEMPLATES = {
    # Emotional tones
    "happy": "Speak with joy and enthusiasm, upbeat tone",
    "sad": "Melancholic, slow, emotional tone",
    "angry": "Frustrated, sharp tone with emphasis",
    "scared": "Nervous, trembling voice, quick pace",
    "mysterious": "Whisper mysteriously, build suspense",
    "excited": "Very enthusiastic, fast-paced, energetic",
    
    # Speaking styles
    "narrator": "Classic storytelling voice, clear and engaging",
    "news": "Professional news anchor, clear and authoritative",
    "teacher": "Patient, clear, educational tone with good pacing",
    "robot": "Mechanical, precise, monotone delivery",
    "child": "Young, innocent, curious tone",
    "elderly": "Wise, slow, thoughtful delivery",
    
    # Special effects
    "whisper": "Whisper the entire text softly",
    "shout": "Loud, urgent delivery",
    "emphasis": "Strong emphasis on CAPITALIZED words",
    "slow": "Very slow and clear pronunciation",
    "fast": "Quick, rapid delivery",
    
    # Content-specific
    "dialogue": "Natural conversational tone",
    "poetry": "Rhythmic, melodic delivery respecting line breaks",
    "technical": "Precise, clear pronunciation of technical terms",
    "meditation": "Calm, soothing, slow pace with pauses"
}

class IntelligentTTSClient:
    def __init__(self, output_dir):
        self.sio = socketio.AsyncClient()
        self.output_dir = output_dir
        self.chunk_count = 0
        self.is_complete = False
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Register handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('stream_started', self.on_stream_started)
        self.sio.on('audio_chunk', self.on_audio_chunk)
        self.sio.on('stream_progress', self.on_stream_progress)
        self.sio.on('stream_complete', self.on_stream_complete)
        self.sio.on('stream_error', self.on_stream_error)
    
    async def on_connect(self):
        print(f"✅ Connected to WebSocket server")
    
    async def on_disconnect(self):
        print("\n❌ Disconnected")
    
    async def on_stream_started(self, data):
        print(f"\n🎬 Stream started: {data['request_id']}")
    
    async def on_audio_chunk(self, data):
        self.chunk_count += 1
        chunk_index = data['chunk_index'] + 1
        
        # Save audio
        audio_bytes = bytes.fromhex(data['audio_data'])
        filename = f"{self.output_dir}/chunk_{chunk_index:02d}.{data['format']}"
        
        with open(filename, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"\n📦 Chunk {chunk_index} - Size: {len(audio_bytes)/1024:.1f}KB")
        print(f"   Text: \"{data.get('chunk_text', '')[:60]}...\"")
    
    async def on_stream_progress(self, data):
        progress = data['progress']
        bar = '█' * (progress // 5) + '░' * (20 - progress // 5)
        print(f"\r⏳ [{bar}] {progress}%", end='', flush=True)
    
    async def on_stream_complete(self, data):
        print(f"\n\n✅ Completed! Total chunks: {data['total_chunks']}")
        self.is_complete = True
    
    async def on_stream_error(self, data):
        print(f"\n❌ Error: {data.get('error')}")
        self.is_complete = True
    
    def analyze_text_content(self, text: str) -> str:
        """Analyze text and determine appropriate voice instruction"""
        
        # Check for dialogue
        if '"' in text or "'" in text:
            return "Natural conversational tone for dialogue"
        
        # Check for questions
        if '?' in text:
            return "Questioning, curious tone"
        
        # Check for exclamations
        if '!' in text:
            return "Excited, emphatic delivery"
        
        # Check for all caps (shouting)
        words = text.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 1]
        if len(caps_words) > len(words) * 0.3:
            return "Urgent, loud delivery"
        
        # Check for parentheses (asides)
        if '(' in text and ')' in text:
            return "Normal tone, but whisper text in parentheses"
        
        # Check for lists or technical content
        if re.search(r'\d+\.|\d+\)|\*|-', text):
            return "Clear, organized delivery for list items"
        
        # Check for emotional keywords
        emotion_patterns = {
            r'\b(sad|cry|tear|mourn|grief)\b': "Melancholic, emotional tone",
            r'\b(happy|joy|laugh|celebrate)\b': "Joyful, upbeat tone",
            r'\b(angry|furious|rage|mad)\b': "Frustrated, sharp tone",
            r'\b(love|romantic|heart|kiss)\b': "Warm, romantic tone",
            r'\b(fear|scared|terrif|horror)\b': "Nervous, suspenseful tone"
        }
        
        for pattern, instruction in emotion_patterns.items():
            if re.search(pattern, text, re.I):
                return instruction
        
        # Default
        return "Clear, natural delivery"
    
    def split_text_with_context(self, text: str, chunk_size: int = 500) -> List[Tuple[str, str]]:
        """Split text into chunks with appropriate instructions for each"""
        chunks_with_instructions = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    instruction = self.analyze_text_content(current_chunk)
                    chunks_with_instructions.append((current_chunk.strip(), instruction))
                current_chunk = para + "\n\n"
        
        if current_chunk:
            instruction = self.analyze_text_content(current_chunk)
            chunks_with_instructions.append((current_chunk.strip(), instruction))
        
        return chunks_with_instructions
    
    async def generate_with_instructions(self, chunks_with_instructions: List[Tuple[str, str]], 
                                       voice: str = 'alloy', format_type: str = 'opus'):
        """Generate TTS with custom instructions for each chunk"""
        
        # Connect
        await self.sio.connect(WEBSOCKET_URL)
        await asyncio.sleep(0.5)
        
        # Process each chunk
        for i, (text, instruction) in enumerate(chunks_with_instructions, 1):
            print(f"\n{'='*70}")
            print(f"📝 Chunk {i}/{len(chunks_with_instructions)}")
            print(f"📋 Instruction: {instruction}")
            print(f"📄 Text: {text[:100]}...")
            print('='*70)
            
            request_id = f"req_{int(time.time() * 1000)}_{i}"
            
            # Note: In the actual implementation, you would send the instruction
            # For now, we'll just demonstrate the concept
            await self.sio.emit('generate_stream', {
                'request_id': request_id,
                'text': text,
                'voice': voice,
                'format': format_type,
                'instructions': instruction,  # This is where the magic happens!
                'chunk_size': len(text)  # Single chunk per instruction
            })
            
            # Wait for this chunk to complete
            self.is_complete = False
            while not self.is_complete:
                await asyncio.sleep(0.1)
            
            # Small delay between chunks
            await asyncio.sleep(0.5)
        
        await self.sio.disconnect()

# Example stories with different instruction needs
EXAMPLE_STORIES = {
    "emotional_journey": """
The letter arrived on a rainy Tuesday morning. Sarah's hands trembled as she recognized the handwriting.

"My dearest Sarah," it began. Her heart skipped. It was from Michael, after all these years.

She read on, tears forming: "I never forgot our summer in Paris. The café where we met still serves the same croissants."

WAIT! Was this real? Could it be? Her mind raced with possibilities.

(She whispered to herself: "He remembered...")

The final line made her gasp: "I'm coming home next week. Can we start again?"

She laughed through her tears. Yes. YES! A thousand times yes!
""",

    "technical_tutorial": """
Chapter 1: Getting Started with Python

Welcome to Python programming! Let's begin with the basics.

1. First, install Python 3.9 or higher
2. Open your terminal and type: python --version
3. You should see something like: Python 3.9.7

IMPORTANT: Always use virtual environments for your projects!

Now, let's write our first program:
print("Hello, World!")

Did you see the output? Congratulations! You're now a Python programmer.

Remember: Practice makes perfect. Code every day, even if just for 15 minutes.
""",

    "children_story": """
Once upon a time, in a magical forest, lived a tiny dragon named Sparkles!

"I want to fly!" said Sparkles, but his wings were still too small.

Every day he practiced. Jump... jump... JUMP! But he always fell down. Ouch!

One morning, something amazing happened. He jumped and... HE FLEW! 

"WHEEEEE!" cried Sparkles, soaring through the clouds. "I'm flying! I'm really flying!"

All his forest friends cheered below. The wise old owl hooted: "We knew you could do it!"

And from that day on, Sparkles flew everywhere, spreading joy and dragon giggles throughout the land.

The End.
"""
}

async def interactive_demo():
    """Interactive demonstration of voice instructions"""
    print("=" * 80)
    print("   🎯 Intelligent TTS with Voice Instructions Demo")
    print("=" * 80)
    print("\nVoice Instructions can transform how text is spoken!")
    print("\nExamples of instructions:")
    print("  • Emotional: happy, sad, angry, excited, mysterious")
    print("  • Style: narrator, teacher, robot, child, news anchor")
    print("  • Effects: whisper, shout, slow, fast, emphasis")
    print("  • Content: dialogue, poetry, technical, meditation")
    print("=" * 80)
    
    # Story selection
    print("\nSelect a demo story:")
    stories = list(EXAMPLE_STORIES.keys())
    for i, story in enumerate(stories, 1):
        print(f"  {i}. {story.replace('_', ' ').title()}")
    
    choice = input("\nYour choice (1-3): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= 3:
        selected_story = stories[int(choice) - 1]
    else:
        selected_story = stories[0]
    
    text = EXAMPLE_STORIES[selected_story]
    
    # Create client
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{OUTPUT_DIR}/instructions_demo_{timestamp}"
    client = IntelligentTTSClient(output_dir)
    
    # Analyze and split text
    print(f"\n📊 Analyzing text for {selected_story.replace('_', ' ')}...")
    chunks_with_instructions = client.split_text_with_context(text, chunk_size=300)
    
    print(f"\n📋 Generated {len(chunks_with_instructions)} chunks with custom instructions:")
    for i, (chunk, instruction) in enumerate(chunks_with_instructions, 1):
        print(f"\nChunk {i}:")
        print(f"  Instruction: {instruction}")
        print(f"  Preview: {chunk[:60]}...")
    
    # Generate with instructions
    proceed = input("\n🎤 Generate speech with these instructions? (y/n): ").lower()
    if proceed == 'y':
        await client.generate_with_instructions(
            chunks_with_instructions,
            voice='nova',  # Nova is good for varied expressions
            format_type='opus'
        )
        print(f"\n✅ Audio saved in: {output_dir}/")
    
    # Custom instruction demo
    print("\n" + "="*80)
    print("💡 Try your own custom instruction!")
    custom_text = input("\nEnter text: ")
    
    if custom_text:
        print("\nSuggested instructions:")
        for key, desc in list(INSTRUCTION_TEMPLATES.items())[:10]:
            print(f"  • {key}: {desc}")
        
        custom_instruction = input("\nEnter instruction (or press Enter for auto): ").strip()
        
        if not custom_instruction:
            custom_instruction = client.analyze_text_content(custom_text)
            print(f"\n🤖 Auto-detected: {custom_instruction}")
        
        # Would generate here...
        print(f"\n📢 Would generate: \"{custom_text[:50]}...\"")
        print(f"   With instruction: {custom_instruction}")

async def main():
    try:
        await interactive_demo()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 Demo completed!")

if __name__ == "__main__":
    asyncio.run(main())