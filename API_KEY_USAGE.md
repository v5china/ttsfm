# 🔐 TTSFM API Key Usage Guide

## Quick Start

### 1. Enable API Key Protection

```bash
# Set environment variables
export REQUIRE_API_KEY=true
export TTSFM_API_KEY=your-secret-api-key

# Run TTSFM with protection
docker run -p 8000:8000 \
  -e REQUIRE_API_KEY=true \
  -e TTSFM_API_KEY=your-secret-api-key \
  ghcr.io/dbccccccc/ttsfm:latest
```

### 2. Use with OpenAI Python Client

```python
from openai import OpenAI

# Configure client with your API key
client = OpenAI(
    api_key="your-secret-api-key",
    base_url="http://localhost:8000/v1"
)

# Generate speech (exactly like OpenAI)
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="alloy",
    input="Hello from TTSFM with API key protection!"
)

response.stream_to_file("protected_speech.mp3")
```

### 3. Use with curl

```bash
# Standard Authorization header (OpenAI compatible)
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini-tts",
    "input": "Hello, world!",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3
```

## Authentication Methods

TTSFM accepts API keys in multiple formats (in order of priority):

### 1. Authorization Header (Recommended)
```bash
Authorization: Bearer your-api-key
```

### 2. X-API-Key Header
```bash
X-API-Key: your-api-key
```

### 3. Query Parameter
```bash
?api_key=your-api-key
```

### 4. JSON Body
```json
{"api_key": "your-api-key", ...}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REQUIRE_API_KEY` | `false` | Enable/disable API key protection |
| `TTSFM_API_KEY` | `None` | Your secret API key |

## Protected vs Public Endpoints

### Protected (Require API Key)
- `POST /v1/audio/speech`
- `POST /api/generate`
- `POST /api/generate-combined`

### Public (Always Accessible)
- `GET /` - Web interface
- `GET /playground` - Interactive playground
- `GET /api/health` - Health check
- `GET /api/voices` - Available voices
- `GET /api/formats` - Supported formats
- `GET /api/auth-status` - Authentication status

## Error Responses

When API key is invalid or missing:

```json
{
  "error": {
    "message": "Invalid API key provided",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

## Security Best Practices

1. **Use HTTPS in production**
2. **Keep API keys secret** - never commit to version control
3. **Use environment variables** for configuration
4. **Rotate keys regularly**
5. **Monitor access logs** for suspicious activity

## Disable Protection

To disable API key protection:

```bash
export REQUIRE_API_KEY=false
# or remove the environment variable entirely
```

Then restart the application.
