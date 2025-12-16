# TTSFM - Text-to-Speech API Client

> **Language / 语言**: [English](README.md) | [中文](README.zh.md)

[![Docker Pulls](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)
[![GitHub Stars](https://img.shields.io/github/stars/dbccccccc/ttsfm?style=social)](https://github.com/dbccccccc/ttsfm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
![ghcr pulls](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fghcr-badge.elias.eu.org%2Fapi%2Fdbccccccc%2Fttsfm%2Fttsfm&query=downloadCount&label=ghcr+pulls&logo=github)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://www.star-history.com/#dbccccccc/ttsfm&Date)

## Overview

TTSFM is a free, OpenAI-compatible text-to-speech API service that provides a complete solution for converting text to natural-sounding speech based on OpenAI's GPT-4o mini TTS. Built on top of the openai.fm backend, it offers a powerful Python SDK, RESTful API endpoints, and an intuitive web playground for easy testing and integration.

**What TTSFM Can Do:**
- 🎤 **Multiple Voices**: Choose from 11 OpenAI-compatible voices (alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse)
- 🎵 **Flexible Audio Formats**: Support for 6 audio formats (MP3, WAV, OPUS, AAC, FLAC, PCM)
- ⚡ **Speed Control**: Adjust playback speed from 0.25x to 4.0x for different use cases
- 📝 **Long Text Support**: Automatic text splitting and audio combining for content of any length
- 🔄 **Real-time Streaming**: WebSocket support for streaming audio generation
- 🐍 **Python SDK**: Easy-to-use synchronous and asynchronous clients
- 🌐 **Web Playground**: Interactive web interface for testing and experimentation
- 🐳 **Docker Ready**: Pre-built Docker images for instant deployment
- 🔍 **Smart Detection**: Automatic capability detection and helpful error messages
- 🤖 **OpenAI Compatible**: Drop-in replacement for OpenAI's TTS API

**Key Features in v3.4.0:**
- 🎯 Image variant detection (full vs slim Docker images)
- 🔍 Runtime capabilities API for feature availability checking
- ⚡ Speed adjustment with ffmpeg-based audio processing
- 🎵 Real format conversion for all 6 audio formats
- 📊 Enhanced error handling with clear, actionable messages
- 🐳 Dual Docker images optimized for different use cases

> **⚠️ Disclaimer**: This project is intended for **educational and research purposes only**. It is a reverse-engineered implementation of the openai.fm service and should not be used for commercial purposes or in production environments. Users are responsible for ensuring compliance with applicable laws and terms of service.

## Installation

### Python package

```bash
pip install ttsfm        # core client
pip install ttsfm[web]   # core client + web/server dependencies
```

### Docker image

TTSFM offers two Docker image variants to suit different needs:

#### Full variant (recommended)
```bash
docker run -p 8000:8000 dbcccc/ttsfm:latest
```

**Includes ffmpeg for advanced features:**
- ✅ All 6 audio formats (MP3, WAV, OPUS, AAC, FLAC, PCM)
- ✅ Speed adjustment (0.25x - 4.0x)
- ✅ Format conversion with ffmpeg
- ✅ MP3 auto-combine for long text
- ✅ WAV auto-combine for long text

#### Slim variant - ~100MB
```bash
docker run -p 8000:8000 dbcccc/ttsfm:slim
```

**Minimal image without ffmpeg:**
- ✅ Basic TTS functionality
- ✅ 2 audio formats (MP3, WAV only)
- ✅ WAV auto-combine for long text
- ❌ No speed adjustment
- ❌ No format conversion
- ❌ No MP3 auto-combine

The container exposes the web playground at `http://localhost:8000` and an OpenAI-compatible endpoint at `/v1/audio/speech`.

**Check available features:**
```bash
curl http://localhost:8000/api/capabilities
```

## Quick start

### Python client

```python
from ttsfm import TTSClient, AudioFormat, Voice

client = TTSClient()

# Basic usage
response = client.generate_speech(
    text="Hello from TTSFM!",
    voice=Voice.ALLOY,
    response_format=AudioFormat.MP3,
)
response.save_to_file("hello")  # -> hello.mp3

# With speed adjustment (requires ffmpeg)
response = client.generate_speech(
    text="This will be faster!",
    voice=Voice.NOVA,
    response_format=AudioFormat.MP3,
    speed=1.5,  # 1.5x speed (0.25 - 4.0)
)
response.save_to_file("fast")  # -> fast.mp3
```

### CLI

```bash
ttsfm "Hello, world" --voice nova --format mp3 --output hello.mp3
```

### REST API (OpenAI-compatible)

```bash
# Basic request
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello world!",
    "voice": "alloy",
    "response_format": "mp3"
  }' --output speech.mp3

# With speed adjustment (requires full image)
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello world!",
    "voice": "alloy",
    "response_format": "mp3",
    "speed": 1.5
  }' --output speech_fast.mp3
```

**Available voices:** alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse
**Available formats:** mp3, wav (always) + opus, aac, flac, pcm (full image only)
**Speed range:** 0.25 - 4.0 (requires full image)

## Learn more

- Browse the full API reference and operational notes in the [web documentation](http://localhost:8000/docs) (or see `ttsfm-web/templates/docs.html`).
- Read the [architecture overview](docs/architecture.md) for component diagrams.
- Contributions are welcome—see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

TTSFM is released under the [MIT License](LICENSE).
