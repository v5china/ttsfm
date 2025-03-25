# TTSFM

[![Docker Image](https://img.shields.io/docker/pulls/dbcccc/ttsfm?style=flat-square)](https://hub.docker.com/r/dbcccc/ttsfm)
[![License](https://img.shields.io/github/license/dbccccccc/ttsfm?style=flat-square)](LICENSE)

> **Disclaimer**: This project is for learning and testing purposes only. For production use, please use the official OpenAI TTS service at https://platform.openai.com/docs/guides/audio

[English](README.md) | [中文](README_CN.md)

TTSFM is a reverse-engineered API server that mirrors OpenAI's TTS service, providing a compatible interface for text-to-speech conversion with multiple voice options.

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- OR Docker

### Installation

#### Option 1: Using Docker (Recommended)
```bash
docker pull dbcccc/ttsfm:latest
docker run -p 7000:7000 dbcccc/ttsfm:latest
```

Note:
For Apple macOS, if port 7000 is occupied by the Control Center, you can use an alternative local port like 5051:  
For Intel chips:
```bash
docker pull dbcccc/ttsfm:latest
docker run -p 5051:7000 dbcccc/ttsfm:latest
```
For Apple Silicon (M-series) chips, in the repository's current directory:
```bash
docker build -t ttsfm .
docker run -p 5051:7000 ttsfm
```
For Mac, access the web interface at `http://localhost:5051`.

#### Option 2: Manual Installation
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

#### Option 1: Using Docker
1. The server will start automatically after running the docker command
2. Access the web interface at `http://localhost:7000`

#### Option 2: Manual Usage
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

### Pressure Testing
The project includes a pressure test script to evaluate server performance under load. To use it:

```bash
# Basic test (10 requests, 2 concurrent connections)
python pressure_test.py

# Test with more requests and higher concurrency
python pressure_test.py -n 50 -c 10

# Test with different text lengths
python pressure_test.py -t short  # Short text
python pressure_test.py -t medium # Medium text (default)
python pressure_test.py -t long   # Long text

# Save generated audio files
python pressure_test.py -s

# Custom server URL
python pressure_test.py -u http://localhost:7000
```

Options:
- `-n, --num-requests`: Total number of requests to send (default: 10)
- `-c, --concurrency`: Number of concurrent connections (default: 2)
- `-t, --text-length`: Length of text to use (short/medium/long)
- `-s, --save-audio`: Save generated audio files to test_output directory
- `-u, --url`: Custom server URL (default: http://localhost:7000)

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dbccccccc/ttsfm&type=Date)](https://www.star-history.com/#dbccccccc/ttsfm&Date)
