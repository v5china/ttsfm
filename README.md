# TTSFM - Text-to-Speech API Client

> **Language / 语言**: [English](README.md) | [中文](README.zh.md)

[![Docker Pulls](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)
[![GitHub Stars](https://img.shields.io/github/stars/dbccccccc/ttsfm?style=social)](https://github.com/dbccccccc/ttsfm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
![ghcr pulls](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fghcr-badge.elias.eu.org%2Fapi%2Fdbccccccc%2Fttsfm%2Fttsfm&query=downloadCount&label=ghcr+pulls&logo=github)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://www.star-history.com/#dbccccccc/ttsfm&Date)

## Overview

TTSFM is a free, OpenAI-compatible text-to-speech stack powered by the openai.fm backend. It ships with Python clients, a REST API, and a web playground.

## Installation

### Python package

```bash
pip install ttsfm        # core client
pip install ttsfm[web]   # client + Flask web app
```

### Docker image

```bash
docker run -p 8000:8000 dbcccc/ttsfm:latest
```

The container exposes the web playground at `http://localhost:8000` and an OpenAI-style endpoint at `/v1/audio/speech`.

## Quick start

### Python client

```python
from ttsfm import TTSClient, AudioFormat, Voice

client = TTSClient()
response = client.generate_speech(
    text="Hello from TTSFM!",
    voice=Voice.ALLOY,
    response_format=AudioFormat.MP3,
)
response.save_to_file("hello")  # -> hello.mp3
```

### CLI

```bash
ttsfm "Hello, world" --voice nova --format mp3 --output hello.mp3
```

### REST API

```bash
curl -X POST http://localhost:8000/v1/audio/speech   -H "Content-Type: application/json"   -d '{"model":"gpt-4o-mini-tts","input":"Hello world!","voice":"alloy"}'   --output speech.mp3
```

## Learn more

- Browse the full API reference and operational notes in the [web documentation](http://localhost:8000/docs) (or see `ttsfm-web/templates/docs.html`).
- Read the [architecture overview](docs/architecture.md) for component diagrams.
- Contributions are welcome—see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

TTSFM is released under the [MIT License](LICENSE).
