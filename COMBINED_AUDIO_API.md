# Combined Audio API Documentation

This document describes the new combined audio generation endpoints that allow you to generate a single audio file from long text by automatically splitting the text into chunks and combining the resulting audio.

## Overview

The combined audio functionality addresses the limitation of TTS services that have character limits (typically 4096 characters). Instead of requiring you to manually split long text and manage multiple audio files, these endpoints:

1. **Automatically split** long text into optimal chunks
2. **Generate speech** for each chunk in parallel
3. **Combine audio chunks** into a single seamless audio file
4. **Return the combined audio** as a single download

## Endpoints

### 1. `/api/generate-combined` (POST)

**Description**: Generate combined audio from long text using TTSFM's native API format.

**Request Body**:
```json
{
  "text": "Your long text content here...",
  "voice": "alloy",
  "format": "mp3",
  "instructions": "Optional voice instructions",
  "max_length": 4096,
  "preserve_words": true
}
```

**Parameters**:
- `text` (string, required): The text to convert to speech
- `voice` (string, optional): Voice to use. Options: `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, `shimmer`, `verse`. Default: `alloy`
- `format` (string, optional): Audio format. Options: `mp3`, `wav`, `opus`, `aac`, `flac`, `pcm`. Default: `mp3`
- `instructions` (string, optional): Custom instructions for voice modulation
- `max_length` (integer, optional): Maximum characters per chunk. Default: `4096`
- `preserve_words` (boolean, optional): Whether to preserve word boundaries when splitting. Default: `true`

**Response**: 
- **Success (200)**: Returns audio file as binary data
- **Error (400/500)**: Returns JSON error message

**Response Headers**:
- `Content-Type`: Audio MIME type (e.g., `audio/mpeg`)
- `Content-Disposition`: Attachment filename
- `Content-Length`: File size in bytes
- `X-Audio-Format`: Audio format used
- `X-Audio-Size`: Audio file size
- `X-Chunks-Combined`: Number of chunks that were combined
- `X-Original-Text-Length`: Original text length in characters

### 2. `/v1/audio/speech-combined` (POST)

**Description**: OpenAI-compatible endpoint for combined audio generation.

**Request Body**:
```json
{
  "model": "gpt-4o-mini-tts",
  "input": "Your long text content here...",
  "voice": "alloy",
  "response_format": "mp3",
  "instructions": "Optional voice instructions",
  "speed": 1.0,
  "max_length": 4096
}
```

**Parameters**:
- `model` (string, optional): Model name (accepted but ignored for compatibility). Default: `gpt-4o-mini-tts`
- `input` (string, required): The text to convert to speech
- `voice` (string, optional): Voice to use (same options as above). Default: `alloy`
- `response_format` (string, optional): Audio format (same options as above). Default: `mp3`
- `instructions` (string, optional): Custom instructions for voice modulation
- `speed` (float, optional): Speech speed (accepted but ignored for compatibility). Default: `1.0`
- `max_length` (integer, optional): Maximum characters per chunk. Default: `4096`

**Response**: Same as `/api/generate-combined`

## Text Splitting Algorithm

The system uses an intelligent text splitting algorithm with the following priority:

1. **Sentence boundaries** (`.`, `!`, `?`) - Preferred for natural speech flow
2. **Word boundaries** (spaces) - Fallback when sentences are too long
3. **Character boundaries** - Last resort for extremely long words

### Example Splitting:

**Input text (150 chars, max_length=100)**:
```
"This is sentence one. This is sentence two! This is a very long sentence that exceeds the limit and needs splitting."
```

**Output chunks**:
```
Chunk 1: "This is sentence one. This is sentence two!"
Chunk 2: "This is a very long sentence that exceeds the limit and needs splitting."
```

## Audio Combination

The system combines audio chunks using:

1. **PyDub library** (preferred): Professional audio processing with format support
2. **Simple WAV concatenation** (fallback): Basic concatenation for WAV files when PyDub is unavailable
3. **Raw concatenation** (last resort): Simple byte concatenation for other formats

### Supported Formats for Combination:
- **MP3**: Full support with PyDub, raw concatenation fallback
- **WAV**: Full support with PyDub, intelligent concatenation fallback
- **OPUS/AAC/FLAC/PCM**: Full support with PyDub, raw concatenation fallback

## Usage Examples

### Python with requests:

```python
import requests

# Long text example
long_text = "Your very long text content here..." * 10

# Using native API
response = requests.post(
    "http://localhost:8000/api/generate-combined",
    json={
        "text": long_text,
        "voice": "nova",
        "format": "mp3",
        "max_length": 2000
    }
)

if response.status_code == 200:
    with open("combined_audio.mp3", "wb") as f:
        f.write(response.content)
    
    chunks_combined = response.headers.get('X-Chunks-Combined')
    print(f"Successfully combined {chunks_combined} chunks")

# Using OpenAI-compatible API
response = requests.post(
    "http://localhost:8000/v1/audio/speech-combined",
    json={
        "model": "gpt-4o-mini-tts",
        "input": long_text,
        "voice": "alloy",
        "response_format": "wav"
    }
)
```

### cURL:

```bash
# Native API
curl -X POST http://localhost:8000/api/generate-combined \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your long text here...",
    "voice": "alloy",
    "format": "mp3",
    "max_length": 4096
  }' \
  --output combined_audio.mp3

# OpenAI-compatible API
curl -X POST http://localhost:8000/v1/audio/speech-combined \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini-tts",
    "input": "Your long text here...",
    "voice": "nova",
    "response_format": "wav"
  }' \
  --output combined_audio.wav
```

## Error Handling

### Common Error Responses:

**400 Bad Request**:
```json
{
  "error": "Text is required"
}
```

**400 Invalid Voice**:
```json
{
  "error": "Invalid voice: invalid_voice. Must be one of: ['alloy', 'ash', ...]"
}
```

**500 Processing Error**:
```json
{
  "error": "Failed to combine audio chunks"
}
```

**503 Service Unavailable**:
```json
{
  "error": "TTS service is currently unavailable"
}
```

## Performance Considerations

- **Chunk processing**: Chunks are processed concurrently for faster generation
- **Memory usage**: Audio combination is optimized for minimal memory footprint
- **Timeout**: Allow longer timeouts for large text processing (recommended: 60-120 seconds)
- **File size**: Combined audio files will be larger than individual chunks

## Installation Requirements

For optimal audio combination, install PyDub:

```bash
pip install pydub
```

**Note**: PyDub is optional. The system will fall back to simpler concatenation methods if PyDub is not available.

## Limitations

1. **Maximum text length**: While there's no hard limit, very long texts (>50,000 characters) may take significant time to process
2. **Audio quality**: Quality depends on the underlying TTS service (openai.fm)
3. **Format support**: Some advanced audio processing features require PyDub
4. **Processing time**: Longer texts require more processing time due to chunking and combination

## Testing

Use the provided test script to verify functionality:

```bash
python test_combined_endpoint.py
```

This will test both endpoints and generate sample audio files for verification.
