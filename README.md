# TTSFM

[![Docker Pulls](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square&logo=docker)](https://hub.docker.com/r/dbcccc/ttsfm)
[![License](https://img.shields.io/github/license/dbccccccc/ttsfm?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/dbccccccc/ttsfm?style=social)](https://github.com/dbccccccc/ttsfm)

> ⚠️ **Disclaimer**  
> This project is for learning and testing purposes only. For production environments, please use [OpenAI's official TTS service](https://platform.openai.com/docs/guides/audio).

> ⚠️ **Development Notice**  
> The v2 branch is currently under active development and is not recommended for production use. Please use the latest stable release version instead.

English | [中文](README_CN.md)

## 🌟 Project Introduction

TTSFM is a reverse-engineered API server that is fully compatible with OpenAI's Text-to-Speech (TTS) interface.

> 🎮 Try it now: [Official Demo Site](https://ttsapi.site/)

## 🏗️ Project Structure

```text
ttsfm/
├── main.py              # Application entry
├── server/              # Core services
│   ├── api.py           # OpenAI-compatible API
│   └── handlers.py      # Request handlers
├── utils/               # Utility modules
│   └── config.py        # Configuration management
├── static/              # Frontend resources
│   ├── index.html       # English interface
│   ├── index_zh.html    # Chinese interface
│   ├── script.js        # Frontend JavaScript
│   └── styles.css       # Frontend styles
├── pressure_test.py     # Stress testing script
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
└── .env.example       # Environment variables template
```

## 🚀 Quick Start

### System Requirements
- Python ≥ 3.8
- Or Docker environment

### 🐳 Docker Run (Recommended)

Basic usage:
```bash
docker run -p 7000:7000 dbcccc/ttsfm:latest
```

Custom configuration using environment variables:
```bash
docker run -d \
  -p 7000:7000 \
  -e HOST=0.0.0.0 \
  -e PORT=7000 \
  -e VERIFY_SSL=true \
  -e MAX_QUEUE_SIZE=100 \
  -e RATE_LIMIT_REQUESTS=30 \
  -e RATE_LIMIT_WINDOW=60 \
  dbcccc/ttsfm:latest
```

Available environment variables:
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 7000)
- `VERIFY_SSL`: Whether to verify SSL certificates (default: true)
- `MAX_QUEUE_SIZE`: Maximum number of tasks in queue (default: 100)
- `RATE_LIMIT_REQUESTS`: Maximum number of requests per time window (default: 30)
- `RATE_LIMIT_WINDOW`: Time window in seconds for rate limiting (default: 60)

> 💡 **Tip**  
> MacOS users experiencing port conflicts can use alternative ports:  
> `docker run -p 5051:7000 dbcccc/ttsfm:latest`

> 💡 **Important**  
> Always use the `latest` tag for the most stable version. The v2 branch is under development and not recommended for production use.

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

## 🤝 Contributing

We welcome all forms of contributions! You can participate by:

- Submitting [Issues](https://github.com/dbccccccc/ttsfm/issues) to report problems
- Creating [Pull Requests](https://github.com/dbccccccc/ttsfm/pulls) to improve code
- Sharing usage experiences and suggestions

📜 Project licensed under [MIT License](LICENSE)

## 📈 Project Activity

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://star-history.com/#dbccccccc/ttsfm&Date)