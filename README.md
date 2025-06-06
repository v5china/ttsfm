# TTSFM - Text-to-Speech API Client

[![Docker Pulls](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)
[![GitHub Stars](https://img.shields.io/github/stars/dbccccccc/ttsfm?style=social)](https://github.com/dbccccccc/ttsfm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

🎤 **A modern, free Text-to-Speech API client with OpenAI compatibility**

TTSFM provides both synchronous and asynchronous Python clients for text-to-speech generation using the reverse-engineered openai.fm service. No API keys required - completely free to use!

## ✨ Key Features

- 🆓 **Completely Free** - Uses reverse-engineered openai.fm service (no API keys needed)
- 🎯 **OpenAI-Compatible** - Drop-in replacement for OpenAI's TTS API (`/v1/audio/speech`)
- ⚡ **Async & Sync** - Both `asyncio` and synchronous clients available
- 🗣️ **11 Voices** - All OpenAI-compatible voices (alloy, echo, fable, onyx, nova, shimmer, etc.)
- 🎵 **6 Audio Formats** - MP3, WAV, OPUS, AAC, FLAC, PCM support
- 🐳 **Docker Ready** - One-command deployment with web interface
- 🌐 **Web Interface** - Interactive playground for testing voices and formats
- 🔧 **CLI Tool** - Command-line interface for quick TTS generation
- 📦 **Type Hints** - Full type annotation support for better IDE experience
- 🛡️ **Error Handling** - Comprehensive exception hierarchy with retry logic
- 🔄 **Batch Processing** - Generate multiple audio files concurrently
- 📊 **Text Validation** - Automatic text length validation and splitting

## 📦 Installation

### Quick Install

```bash
pip install ttsfm
```

### Installation Options

```bash
# Basic installation (sync client only)
pip install ttsfm

# With web application support
pip install ttsfm[web]

# With development tools
pip install ttsfm[dev]

# With documentation tools
pip install ttsfm[docs]

# Install all optional dependencies
pip install ttsfm[web,dev,docs]
```

### System Requirements

- **Python**: 3.8+ (tested on 3.8, 3.9, 3.10, 3.11, 3.12)
- **OS**: Windows, macOS, Linux
- **Dependencies**: `requests`, `aiohttp`, `fake-useragent`

## 🚀 Quick Start

### 🐳 Docker (Recommended)

Run TTSFM with web interface and OpenAI-compatible API:

```bash
# Using GitHub Container Registry
docker run -p 8000:8000 ghcr.io/dbccccccc/ttsfm:latest

# Using Docker Hub
docker run -p 8000:8000 dbcccc/ttsfm:latest
```

**Available endpoints:**
- 🌐 **Web Interface**: http://localhost:8000
- 🔗 **OpenAI API**: http://localhost:8000/v1/audio/speech
- 📊 **Health Check**: http://localhost:8000/api/health

**Test the API:**

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini-tts","input":"Hello world!","voice":"alloy"}' \
  --output speech.mp3
```

### 📦 Python Package

#### Synchronous Client

```python
from ttsfm import TTSClient, Voice, AudioFormat

# Create client (uses free openai.fm service)
client = TTSClient()

# Generate speech
response = client.generate_speech(
    text="Hello! This is TTSFM - a free TTS service.",
    voice=Voice.CORAL,
    response_format=AudioFormat.MP3
)

# Save the audio file
response.save_to_file("output")  # Saves as output.mp3

# Or get raw audio data
audio_bytes = response.audio_data
print(f"Generated {len(audio_bytes)} bytes of audio")
```

#### Asynchronous Client

```python
import asyncio
from ttsfm import AsyncTTSClient, Voice

async def generate_speech():
    async with AsyncTTSClient() as client:
        response = await client.generate_speech(
            text="Async TTS generation!",
            voice=Voice.NOVA
        )
        response.save_to_file("async_output")

# Run async function
asyncio.run(generate_speech())
```

#### Batch Processing

```python
from ttsfm import AsyncTTSClient, TTSRequest, Voice

async def batch_generate():
    requests = [
        TTSRequest(input="First text", voice=Voice.ALLOY),
        TTSRequest(input="Second text", voice=Voice.ECHO),
        TTSRequest(input="Third text", voice=Voice.NOVA),
    ]

    async with AsyncTTSClient() as client:
        responses = await client.generate_speech_batch(requests)

        for i, response in enumerate(responses):
            response.save_to_file(f"batch_output_{i}")

asyncio.run(batch_generate())
```

#### OpenAI Python Client Compatibility

```python
from openai import OpenAI

# Point to TTSFM Docker container
client = OpenAI(
    api_key="not-needed",  # TTSFM is free
    base_url="http://localhost:8000/v1"
)

# Generate speech (exactly like OpenAI)
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="alloy",
    input="Hello from TTSFM!"
)

response.stream_to_file("output.mp3")
```

### 🖥️ Command Line Interface

```bash
# Basic usage
ttsfm "Hello, world!" --output hello.mp3

# Specify voice and format
ttsfm "Hello, world!" --voice nova --format wav --output hello.wav

# From file
ttsfm --text-file input.txt --output speech.mp3

# Custom service URL
ttsfm "Hello, world!" --url http://localhost:7000 --output hello.mp3

# List available voices
ttsfm --list-voices

# Get help
ttsfm --help
```

## ⚙️ Configuration

TTSFM automatically uses the free openai.fm service - **no configuration or API keys required!**

```python
from ttsfm import TTSClient

# Default client (uses openai.fm)
client = TTSClient()

# Custom configuration
client = TTSClient(
    base_url="https://www.openai.fm",  # Default
    timeout=30.0,                     # Request timeout
    max_retries=3,                    # Retry attempts
    verify_ssl=True                   # SSL verification
)

# For custom TTS services
custom_client = TTSClient(
    base_url="http://your-tts-service.com",
    api_key="your-api-key-if-needed"
)
```

## 🗣️ Available Voices

TTSFM supports all **11 OpenAI-compatible voices**:

| Voice | Description | Best For |
|-------|-------------|----------|
| `alloy` | Balanced and versatile | General purpose, neutral tone |
| `ash` | Clear and articulate | Professional, business content |
| `ballad` | Smooth and melodic | Storytelling, audiobooks |
| `coral` | Warm and friendly | Customer service, tutorials |
| `echo` | Resonant and clear | Announcements, presentations |
| `fable` | Expressive and dynamic | Creative content, entertainment |
| `nova` | Bright and energetic | Marketing, upbeat content |
| `onyx` | Deep and authoritative | News, serious content |
| `sage` | Wise and measured | Educational, informative |
| `shimmer` | Light and airy | Casual, conversational |
| `verse` | Rhythmic and flowing | Poetry, artistic content |

```python
from ttsfm import Voice

# Use enum values
response = client.generate_speech("Hello!", voice=Voice.CORAL)

# Or use string values
response = client.generate_speech("Hello!", voice="coral")

# Test different voices
for voice in Voice:
    response = client.generate_speech(f"This is {voice.value} voice", voice=voice)
    response.save_to_file(f"test_{voice.value}")
```

## 🎵 Audio Formats

TTSFM supports **6 audio formats** with different quality and compression options:

| Format | Extension | Quality | File Size | Use Case |
|--------|-----------|---------|-----------|----------|
| `mp3` | `.mp3` | Good | Small | Web, mobile apps |
| `opus` | `.opus` | Excellent | Small | Web streaming, VoIP |
| `aac` | `.aac` | Good | Medium | Apple devices, streaming |
| `flac` | `.flac` | Lossless | Large | High-quality archival |
| `wav` | `.wav` | Lossless | Large | Professional audio |
| `pcm` | `.pcm` | Raw | Large | Audio processing |

```python
from ttsfm import AudioFormat

# Generate in different formats
formats = [
    AudioFormat.MP3,   # Most common
    AudioFormat.OPUS,  # Best compression
    AudioFormat.AAC,   # Apple compatible
    AudioFormat.FLAC,  # Lossless
    AudioFormat.WAV,   # Uncompressed
    AudioFormat.PCM    # Raw audio
]

for fmt in formats:
    response = client.generate_speech(
        text="Testing audio format",
        response_format=fmt
    )
    response.save_to_file(f"test.{fmt.value}")
```



## 🌐 Web Interface

TTSFM includes a **beautiful web interface** for testing and experimentation:

![Web Interface](https://img.shields.io/badge/Web%20Interface-Available-brightgreen?style=flat-square)

**Features:**
- 🎮 **Interactive Playground** - Test voices and formats in real-time
- 📝 **Text Validation** - Character count and length validation
- 🎛️ **Advanced Options** - Voice instructions, auto-split long text
- 📊 **Audio Player** - Built-in player with duration and file size info
- 📥 **Download Support** - Download individual or batch audio files
- 🎲 **Random Text** - Generate random sample text for testing
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

Access at: http://localhost:8000 (when running Docker container)

## 🔗 API Endpoints

When running the Docker container, these endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/playground` | GET | Interactive TTS playground |
| `/v1/audio/speech` | POST | OpenAI-compatible TTS API |
| `/v1/models` | GET | List available models |
| `/api/health` | GET | Health check endpoint |
| `/api/voices` | GET | List available voices |
| `/api/formats` | GET | List supported audio formats |
| `/api/validate-text` | POST | Validate text length |

### OpenAI-Compatible API

```bash
# Generate speech
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini-tts",
    "input": "Hello, this is a test!",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3

# List models
curl http://localhost:8000/v1/models

# Health check
curl http://localhost:8000/api/health
```

## 🐳 Docker Deployment

### Quick Start

```bash
# Run with default settings
docker run -p 8000:8000 ghcr.io/dbccccccc/ttsfm:latest

# Run with custom port
docker run -p 3000:8000 ghcr.io/dbccccccc/ttsfm:latest

# Run in background
docker run -d -p 8000:8000 --name ttsfm ghcr.io/dbccccccc/ttsfm:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  ttsfm:
    image: ghcr.io/dbccccccc/ttsfm:latest
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Available Images

| Registry | Image | Description |
|----------|-------|-------------|
| GitHub Container Registry | `ghcr.io/dbccccccc/ttsfm:latest` | Latest stable release |
| Docker Hub | `dbcccc/ttsfm:latest` | Mirror on Docker Hub |
| GitHub Container Registry | `ghcr.io/dbccccccc/ttsfm:v3.0.0` | Specific version |

## 🛠️ Advanced Usage

### Error Handling

```python
from ttsfm import TTSClient, TTSException, APIException, NetworkException

client = TTSClient()

try:
    response = client.generate_speech("Hello, world!")
    response.save_to_file("output")
except NetworkException as e:
    print(f"Network error: {e}")
except APIException as e:
    print(f"API error: {e}")
except TTSException as e:
    print(f"TTS error: {e}")
```

### Text Validation and Splitting

```python
from ttsfm.utils import validate_text_length, split_text_by_length

# Validate text length
text = "Your long text here..."
is_valid, length = validate_text_length(text, max_length=4096)

if not is_valid:
    # Split long text into chunks
    chunks = split_text_by_length(text, max_length=4000)

    # Generate speech for each chunk
    for i, chunk in enumerate(chunks):
        response = client.generate_speech(chunk)
        response.save_to_file(f"output_part_{i}")
```

### Custom Headers and User Agents

```python
from ttsfm import TTSClient

# Client automatically uses realistic headers
client = TTSClient()

# Headers include:
# - Realistic User-Agent strings
# - Accept headers for audio content
# - Connection keep-alive
# - Accept-Encoding for compression
```

## 🔧 Development

### Local Development

```bash
# Clone repository
git clone https://github.com/dbccccccc/ttsfm.git
cd ttsfm

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run web application
cd ttsfm-web
python app.py
```

### Building Docker Image

```bash
# Build image
docker build -t ttsfm:local .

# Run local image
docker run -p 8000:8000 ttsfm:local
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📊 Performance

### Benchmarks

- **Latency**: ~1-3 seconds for typical text (depends on openai.fm service)
- **Throughput**: Supports concurrent requests with async client
- **Text Limits**: Up to 4096 characters per request (configurable)
- **Audio Quality**: High-quality synthesis comparable to OpenAI

### Optimization Tips

```python
# Use async client for better performance
async with AsyncTTSClient() as client:
    # Process multiple requests concurrently
    tasks = [
        client.generate_speech(f"Text {i}")
        for i in range(10)
    ]
    responses = await asyncio.gather(*tasks)

# Reuse client instances
client = TTSClient()
for text in texts:
    response = client.generate_speech(text)  # Reuses connection
```

## 🔒 Security & Privacy

- **No API Keys Required**: Uses free openai.fm service
- **No Data Storage**: Audio is generated on-demand, not stored
- **HTTPS Support**: Secure connections to TTS service
- **No Tracking**: TTSFM doesn't collect or store user data
- **Open Source**: Full source code available for audit

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### Latest Changes (v3.0.0)

- 🆕 Complete rewrite with OpenAI compatibility
- 🆕 Async client with batch processing
- 🆕 Web interface with interactive playground
- 🆕 Docker container with health checks
- 🆕 CLI tool for command-line usage
- 🆕 Comprehensive error handling
- 🆕 Type hints and better documentation

## 🤝 Support & Community

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/dbccccccc/ttsfm/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/dbccccccc/ttsfm/discussions)
- 👤 **Author**: [@dbcccc](https://github.com/dbccccccc)
- ⭐ **Star the Project**: If you find TTSFM useful, please star it on GitHub!

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI**: For the original TTS API design
- **openai.fm**: For providing the free TTS service
- **Community**: Thanks to all users and contributors who help improve TTSFM

---

<div align="center">

**TTSFM** - Free Text-to-Speech API with OpenAI Compatibility

[![GitHub](https://img.shields.io/badge/GitHub-dbccccccc/ttsfm-blue?style=flat-square&logo=github)](https://github.com/dbccccccc/ttsfm)
[![PyPI](https://img.shields.io/badge/PyPI-ttsfm-blue?style=flat-square&logo=pypi)](https://pypi.org/project/ttsfm/)
[![Docker](https://img.shields.io/badge/Docker-dbcccc/ttsfm-blue?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)

Made with ❤️ by [@dbcccc](https://github.com/dbccccccc)

</div>
