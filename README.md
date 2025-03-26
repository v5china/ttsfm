Here's the English translation of your document:

# TTSFM

[![Docker Pulls](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)
[![License](https://img.shields.io/github/license/dbccccccc/ttsfm?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/dbccccccc/ttsfm?style=social)](https://github.com/dbccccccc/ttsfm)

> ⚠️ **Disclaimer**  
> This project is for learning and testing purposes only. For production environments, please use [OpenAI's official TTS service](https://platform.openai.com/docs/guides/audio).

[English](README.md) | Chinese Documentation

## 🌟 Project Introduction

TTSFM is a reverse-engineered API server that is fully compatible with OpenAI's Text-to-Speech (TTS) interface.

> 🎮 Try it now: [Official Demo Site](https://ttsapi.fm)

## 🏗️ Project Structure

```text
ttsfm/
├── main.py              # Application entry
├── server/              # Core services
│   ├── api.py           # OpenAI-compatible API
│   └── handlers.py      # Request handlers
├── proxy/               # Proxy system
│   └── manager.py
├── utils/               # Utility modules
│   └── config.py
├── static/              # Frontend resources
│   ├── index.html       # English interface
│   ├── index_zh.html    # Chinese interface
│   └── ...              # JS/CSS resources
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

### System Requirements
- Python ≥ 3.8
- Or Docker environment

### 🐳 Docker Run (Recommended)
```bash
docker run -p 7000:7000 dbcccc/ttsfm:latest
```

> 💡 **Tip**  
> MacOS users experiencing port conflicts can use alternative ports:  
> `docker run -p 5051:7000 dbcccc/ttsfm:latest`

Below is the simplified manual installation section, retaining only the release package download method:

### 📦 Manual Installation

1. Download the latest release package from [GitHub Releases](https://github.com/dbccccccc/ttsfm/releases)
2. Extract and enter the directory:
```bash
tar -zxvf ttsfm-vX.X.X.tar.gz
cd ttsfm-vX.X.X
```
3. Install dependencies and launch:
```bash
pip install -r requirements.txt
cp .env.example .env  # Edit config as needed
python main.py
```

## 📚 Usage Guide

### Web Interface
Access `http://localhost:7000` to experience the interactive demo

### API Endpoints
| Endpoint | Method | Description |
|------|------|-------------|
| `/v1/audio/speech` | POST | Text-to-Speech |
| `/api/queue-size` | GET | Query task queue |

> 🔍 Complete API documentation is available via the web interface after local deployment

### 🧪 Stress Testing
```bash
# Basic test
python pressure_test.py

# Custom test example
python pressure_test.py -n 50 -c 10 -t long -s
```

**Parameter Explanation**:
- `-n` Total requests
- `-c` Concurrency count
- `-t` Text length (short/medium/long)  
- `-s` Save generated audio

## 🤝 Contributing

We welcome all forms of contributions! You can participate by:

- Submitting [Issues](https://github.com/dbccccccc/ttsfm/issues) to report problems
- Creating [Pull Requests](https://github.com/dbccccccc/ttsfm/pulls) to improve code
- Sharing usage experiences and suggestions

📜 Project licensed under [MIT License](LICENSE)

## 📈 Project Activity

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://star-history.com/#dbccccccc/ttsfm&Date)