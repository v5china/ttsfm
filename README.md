# TTSFM - Text-to-Speech API Client

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/ttsfm.svg)](https://badge.fury.io/py/ttsfm)

A modern Python package for text-to-speech generation with OpenAI-compatible API. TTSFM provides both synchronous and asynchronous clients for easy integration into your applications.

## Features

- 🎯 **OpenAI-Compatible API** - Drop-in replacement for OpenAI TTS API
- ⚡ **Async Support** - High-performance asynchronous client with `asyncio`
- 🔧 **Easy Integration** - Simple, intuitive API design
- 🎵 **Multiple Formats** - Support for MP3, WAV, FLAC, and more
- 🗣️ **Voice Options** - Multiple voice models available
- 🛡️ **Error Handling** - Comprehensive exception hierarchy
- 📦 **Type Hints** - Full type annotation support
- 🌐 **Web Interface** - Optional web application included

## Installation

### Basic Installation

```bash
pip install ttsfm
```

### Installation with Optional Dependencies

```bash
# With development tools
pip install ttsfm[dev]

# With web application support
pip install ttsfm[web]

# With documentation tools
pip install ttsfm[docs]
```

## Quick Start

### 🐳 Docker (Recommended)

```bash
docker run -p 8000:8000 ghcr.io/dbccccccc/ttsfm:latest
```

OpenAI-compatible API:

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini-tts","input":"Hello world!","voice":"alloy"}' \
  --output speech.mp3
```

### 📦 Python Package

```python
from ttsfm import TTSClient, Voice

# Create client (uses free openai.fm service)
client = TTSClient()

# Generate speech
response = client.generate_speech(
    text="Hello! This is a test of the free TTS service.",
    voice=Voice.CORAL
)

# Save the audio file
response.save_to_file("output")  # Saves as output.mp3
```

### OpenAI Python Client Compatibility

```python
from openai import OpenAI

# Point to TTSFM Docker container
client = OpenAI(
    api_key="not-needed",  # TTSFM is free
    base_url="http://localhost:8000/v1"
)

# Generate speech
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="alloy",
    input="Hello from TTSFM!"
)

response.stream_to_file("output.mp3")
```

## Configuration

TTSFM automatically uses the free openai.fm service - no configuration required!

```python
from ttsfm import TTSClient

# Default client (uses openai.fm)
client = TTSClient()

# Optional: Custom timeout and retries
client = TTSClient(timeout=30.0, max_retries=3)
```

### Available Voices

TTSFM supports all 11 OpenAI-compatible voices:

```python
from ttsfm import Voice

# All available voices
voices = [
    Voice.ALLOY,    # Balanced and versatile
    Voice.ASH,      # Clear and articulate
    Voice.BALLAD,   # Smooth and melodic
    Voice.CORAL,    # Warm and friendly
    Voice.ECHO,     # Resonant and clear
    Voice.FABLE,    # Expressive and dynamic
    Voice.NOVA,     # Bright and energetic
    Voice.ONYX,     # Deep and authoritative
    Voice.SAGE,     # Wise and measured
    Voice.SHIMMER,  # Light and airy
    Voice.VERSE     # Rhythmic and flowing
]
```

### Audio Formats

```python
from ttsfm import AudioFormat

# Available formats
formats = [
    AudioFormat.MP3,
    AudioFormat.OPUS,
    AudioFormat.AAC,
    AudioFormat.FLAC,
    AudioFormat.WAV,
    AudioFormat.PCM
]
```



## API Endpoints

When running the Docker container, these endpoints are available:

- **OpenAI-compatible API**: `POST /v1/audio/speech`
- **Models endpoint**: `GET /v1/models`
- **Web interface**: `GET /`
- **Health check**: `GET /api/health`

## Features

- ✅ **Free TTS Service**: Uses reverse-engineered openai.fm (no API keys needed)
- ✅ **OpenAI Compatible**: Drop-in replacement for OpenAI's TTS API
- ✅ **11 Voices**: All OpenAI-compatible voices supported
- ✅ **6 Audio Formats**: MP3, WAV, OPUS, AAC, FLAC, PCM
- ✅ **Docker Ready**: One-command deployment
- ✅ **Web Interface**: Interactive UI included

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 🐛 [Issues](https://github.com/dbccccccc/ttsfm/issues)
- 💬 [Discussions](https://github.com/dbccccccc/ttsfm/discussions)

---

**TTSFM** - Free TTS API using reverse-engineered openai.fm service
