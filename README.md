# TTSFM (Text-to-Speech Forwarding Mirror)

[English](README.md) | [中文](README_CN.md)

TTSFM is a reverse-engineered API server that mirrors OpenAI's TTS service, providing a compatible interface for text-to-speech conversion with multiple voice options.

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/ttsfm.git
cd ttsfm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Usage
1. Start the server:
```bash
python server.py
```

2. Access the web interface at `http://localhost:7000`

3. Use the API endpoint

### API Endpoints
Please refer to the deployed webpage for detailed information.
- `POST /v1/audio/speech`: Convert text to speech
- `GET /v1/voices`: List available voices

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://www.star-history.com/#dbccccccc/ttsfm&Date)