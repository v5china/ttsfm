#!/usr/bin/env python3
"""
Example demonstrating long text splitting functionality in TTSFM.

This example shows how to use the new long text methods to automatically
split and generate speech from text longer than the 4096 character limit.
"""

from ttsfm import TTSClient, Voice, AudioFormat

def main():
    # Create a long text example (over 4096 characters)
    long_text = """
    This is a demonstration of the TTSFM long text functionality. 
    When you have text that exceeds the 4096 character limit, TTSFM can 
    automatically split it into smaller chunks and generate speech for each chunk.
    
    The text splitting is intelligent - it preserves word boundaries by default,
    so you won't get words cut off in the middle. This ensures natural-sounding
    speech across all generated audio files.
    
    You can use this functionality in several ways:
    
    1. Using the TTSClient.generate_speech_long_text() method
    2. Using the TTSClient.generate_speech_batch() method (alias)
    3. Using the convenience function generate_speech_long_text()
    4. Using the CLI with the --split-long-text flag
    
    The method returns a list of TTSResponse objects, one for each chunk.
    You can then save each response to a separate file, or combine them
    if needed for your use case.
    
    This feature is particularly useful for:
    - Converting long articles or documents to speech
    - Processing book chapters or large text files
    - Generating audio for educational content
    - Creating podcasts or audiobooks from text
    
    The splitting algorithm is designed to be smart about where it breaks
    the text, preferring to split at sentence boundaries when possible,
    and always preserving word boundaries unless explicitly disabled.
    """ * 10  # Repeat to make it definitely over 4096 characters

    print(f"Text length: {len(long_text)} characters")
    print("Generating speech from long text...\n")

    # Create client
    client = TTSClient()

    try:
        # Method 1: Using generate_speech_long_text
        print("Method 1: Using generate_speech_long_text()")
        responses = client.generate_speech_long_text(
            text=long_text,
            voice=Voice.ALLOY,
            response_format=AudioFormat.MP3,
            max_length=2000,  # Smaller chunks for demo
            preserve_words=True
        )
        
        print(f"Generated {len(responses)} audio chunks")
        
        # Save each chunk
        for i, response in enumerate(responses, 1):
            filename = f"long_text_part_{i:03d}.mp3"
            response.save_to_file(filename)
            print(f"Saved: {filename}")
        
        print(f"\nTotal audio files generated: {len(responses)}")
        print("You can play these files in sequence to hear the complete text.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
