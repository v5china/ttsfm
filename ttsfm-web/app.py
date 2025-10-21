"""
TTSFM Web Application

A Flask web application that provides a user-friendly interface
for the TTSFM text-to-speech package.
"""

import logging
import os
import time

try:
    from .websocket_handler import WebSocketTTSHandler
except ImportError:  # pragma: no cover - fallback when run as script
    from websocket_handler import WebSocketTTSHandler

from collections import defaultdict, deque
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Dict, Iterator, List, Optional
from urllib.parse import urljoin, urlparse

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError
from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for,
)
from flask_cors import CORS
from flask_socketio import SocketIO

# Import i18n support
from i18n import init_i18n, set_locale

# Import the TTSFM package
try:
    from ttsfm import AudioFormat, TTSClient, TTSException, Voice
    from ttsfm.audio import combine_audio_chunks
    from ttsfm.exceptions import APIException, NetworkException, ValidationException
    from ttsfm.models import get_supported_format
    from ttsfm.utils import split_text_by_length
except ImportError:
    # Fallback for development when package is not installed
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from ttsfm import AudioFormat, TTSClient, TTSException, Voice
    from ttsfm.audio import combine_audio_chunks
    from ttsfm.exceptions import APIException, NetworkException, ValidationException
    from ttsfm.models import get_supported_format
    from ttsfm.utils import split_text_by_length

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

APP_ROOT = Path(__file__).resolve().parent
INSTANCE_PATH = APP_ROOT / "instance"

# Create Flask app
app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static",
    root_path=str(APP_ROOT),
    instance_path=str(INSTANCE_PATH),
)
app.secret_key = os.getenv("SECRET_KEY", "ttsfm-secret-key-change-in-production")
CORS(app)

# Configuration (moved up for socketio initialization)


def _default_host() -> str:
    """Choose a sensible default bind host.

    Docker containers need to listen on all interfaces so port mappings work,
    while local installs can continue to use localhost.
    """

    # Common indicator that we're running inside a Docker container
    if os.path.exists("/.dockerenv"):
        return "0.0.0.0"

    return "localhost"


HOST = os.getenv("HOST", _default_host())
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Initialize SocketIO with proper async mode
# Using eventlet for production, threading for development
async_mode = "eventlet" if not DEBUG else "threading"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)

# Initialize i18n support
init_i18n(app)

# API Key configuration
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"

ARGON2_HASH_PREFIXES = ("$argon2i$", "$argon2d$", "$argon2id$")
PASSWORD_HASHER = PasswordHasher()


def _hash_key(value: str) -> str:
    """Hash an API key value with Argon2."""
    if not value:
        raise ValueError("API key value must not be empty.")
    return PASSWORD_HASHER.hash(value)


def _load_api_key_hashes() -> List[str]:
    """Load configured API keys and normalize them to Argon2 hashes."""
    plain_keys: List[str] = []
    prehashed_entries: List[str] = []

    hashed_env = os.getenv("TTSFM_API_KEY_HASHES")
    if hashed_env:
        prehashed_entries.extend([item.strip() for item in hashed_env.split(",") if item.strip()])

    multi_keys = os.getenv("TTSFM_API_KEYS")
    if multi_keys:
        plain_keys.extend([item.strip() for item in multi_keys.split(",") if item.strip()])

    single_key = os.getenv("TTSFM_API_KEY")
    if single_key:
        plain_keys.append(single_key.strip())

    hashes: List[str] = []
    for entry in prehashed_entries:
        if entry.startswith(ARGON2_HASH_PREFIXES):
            hashes.append(entry)
        elif entry:
            logger.warning("Ignoring unsupported API key hash format; expected Argon2 hashes.")

    for key in plain_keys:
        if key:
            hashes.append(_hash_key(key))

    return hashes


API_KEY_HASHES = _load_api_key_hashes()
API_KEYS_CONFIGURED = bool(API_KEY_HASHES)

RATE_LIMIT_WINDOW = int(os.getenv("TTSFM_AUTH_WINDOW_SECONDS", "60"))
RATE_LIMIT_ATTEMPTS = int(os.getenv("TTSFM_AUTH_MAX_ATTEMPTS", "5"))
_FAILED_AUTH_ATTEMPTS: Dict[str, deque] = defaultdict(deque)


def create_tts_client() -> TTSClient:
    """Factory returning an isolated TTS client per request."""
    default_prompt = os.getenv("TTSFM_DEFAULT_PROMPT", "false").lower() == "true"
    return TTSClient(use_default_prompt=default_prompt)


# Initialize WebSocket handler

websocket_handler = WebSocketTTSHandler(socketio, create_tts_client)

logger.info("Initialized web app with TTSFM using openai.fm free service")
logger.info(f"WebSocket support enabled with {async_mode} async mode")

# API Key validation decorator


def require_api_key(f):
    """Decorator to require API key for protected endpoints."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip API key check if not required
        if not REQUIRE_API_KEY:
            return f(*args, **kwargs)

        # Check if API key is configured
        if not API_KEYS_CONFIGURED:
            logger.warning("API key protection is enabled but no API keys are configured")
            return jsonify({"error": "Authentication service is unavailable"}), 500

        # Get API key from request headers - prioritize Authorization header
        # (OpenAI compatible)
        provided_key = None

        # 1. Check Authorization header first (OpenAI standard)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            provided_key = auth_header[7:]  # Remove 'Bearer ' prefix

        # 2. Check X-API-Key header as fallback
        if not provided_key:
            provided_key = request.headers.get("X-API-Key")

        # 3. Check API key from query parameters as fallback
        if not provided_key:
            provided_key = request.args.get("api_key")

        # 4. Check API key from JSON body as fallback
        if not provided_key and request.is_json:
            data = request.get_json(silent=True)
            if data:
                provided_key = data.get("api_key")

        client_ip = request.remote_addr or "unknown"

        if _is_rate_limited(client_ip):
            logger.warning("Authentication rate limit exceeded for %s", client_ip)
            return jsonify({"error": "Too many authentication attempts"}), 429

        # Validate API key
        if not _is_valid_api_key(provided_key):
            _register_failed_attempt(client_ip)
            logger.warning("Invalid API key attempt from %s", client_ip)
            return jsonify({"error": "Authentication failed"}), 401

        _reset_failed_attempts(client_ip)

        return f(*args, **kwargs)

    return decorated_function


def _is_valid_api_key(provided: Optional[str]) -> bool:
    if not provided:
        return False

    for stored_hash in API_KEY_HASHES:
        if not stored_hash.startswith(ARGON2_HASH_PREFIXES):
            logger.warning("Unsupported API key hash format encountered; ignoring entry.")
            continue

        try:
            PASSWORD_HASHER.verify(stored_hash, provided)
        except InvalidHash:
            logger.warning("Skipping invalid API key hash entry in configuration.")
            continue
        except VerificationError:
            continue
        else:
            return True

    return False


def _register_failed_attempt(ip: str) -> None:
    attempts = _FAILED_AUTH_ATTEMPTS[ip]
    now = time.monotonic()
    attempts.append(now)
    _trim_attempts(attempts, now)


def _reset_failed_attempts(ip: str) -> None:
    _FAILED_AUTH_ATTEMPTS.pop(ip, None)


def _trim_attempts(attempts: deque, now: float) -> None:
    while attempts and now - attempts[0] > RATE_LIMIT_WINDOW:
        attempts.popleft()


def _is_rate_limited(ip: str) -> bool:
    attempts = _FAILED_AUTH_ATTEMPTS[ip]
    now = time.monotonic()
    _trim_attempts(attempts, now)
    return len(attempts) >= RATE_LIMIT_ATTEMPTS


def _chunk_bytes(data: bytes, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
    view = memoryview(data)
    for offset in range(0, len(view), chunk_size):
        yield bytes(view[offset : offset + chunk_size])


def _is_safe_url(target: Optional[str]) -> bool:
    """Validate that a target URL is safe for redirection.

    Allows only relative URLs or absolute URLs that match this server's host
    and http/https schemes. Prevents open redirects to external domains.
    """
    if not target:
        return False

    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or target.startswith("//"):
        return False
    if not parsed.path.startswith("/"):
        return False
    joined = urljoin(request.host_url, target)
    host = urlparse(request.host_url)
    j = urlparse(joined)
    return j.scheme in ("http", "https") and j.netloc == host.netloc


@app.route("/set-language/<lang_code>")
def set_language(lang_code):
    """Set the user's language preference."""
    if set_locale(lang_code):
        # Redirect back only if the referrer is safe; otherwise go home
        target = request.referrer
        if _is_safe_url(target):
            return redirect(target)
        return redirect(url_for("index"))
    else:
        # Invalid language code, redirect to home
        return redirect(url_for("index"))


@app.route("/")
def index():
    """Serve the main web interface."""
    return render_template("index.html")


@app.route("/playground")
def playground():
    """Serve the interactive playground."""
    return render_template("playground.html")


@app.route("/docs")
def docs():
    """Serve the API documentation."""
    return render_template("docs.html")


@app.route("/websocket-demo")
def websocket_demo():
    """Serve the WebSocket streaming demo page."""
    return render_template("websocket_demo.html")


@app.route("/api/voices", methods=["GET"])
def get_voices():
    """Get list of available voices."""
    try:
        voices = [
            {
                "id": voice.value,
                "name": voice.value.title(),
                "description": f"{voice.value.title()} voice",
            }
            for voice in Voice
        ]

        return jsonify({"voices": voices, "count": len(voices)})

    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return jsonify({"error": "Failed to get voices"}), 500


@app.route("/api/formats", methods=["GET"])
def get_formats():
    """Get list of supported audio formats."""
    try:
        formats = [
            {
                "id": "mp3",
                "name": "MP3",
                "mime_type": "audio/mpeg",
                "description": "MP3 audio format - good quality, small file size",
                "quality": "Good",
                "file_size": "Small",
                "use_case": "Web, mobile apps, general use",
            },
            {
                "id": "opus",
                "name": "OPUS",
                "mime_type": "audio/opus",
                "description": "OPUS audio format - excellent quality, small file size",
                "quality": "Excellent",
                "file_size": "Small",
                "use_case": "Web streaming, VoIP",
            },
            {
                "id": "aac",
                "name": "AAC",
                "mime_type": "audio/aac",
                "description": "AAC audio format - good quality, medium file size",
                "quality": "Good",
                "file_size": "Medium",
                "use_case": "Apple devices, streaming",
            },
            {
                "id": "flac",
                "name": "FLAC",
                "mime_type": "audio/flac",
                "description": "FLAC audio format - lossless quality, large file size",
                "quality": "Lossless",
                "file_size": "Large",
                "use_case": "High-quality archival",
            },
            {
                "id": "wav",
                "name": "WAV",
                "mime_type": "audio/wav",
                "description": "WAV audio format - lossless quality, large file size",
                "quality": "Lossless",
                "file_size": "Large",
                "use_case": "Professional audio",
            },
            {
                "id": "pcm",
                "name": "PCM",
                "mime_type": "audio/pcm",
                "description": "PCM audio format - raw audio data, large file size",
                "quality": "Raw",
                "file_size": "Large",
                "use_case": "Audio processing",
            },
        ]

        return jsonify({"formats": formats, "count": len(formats)})

    except Exception as e:
        logger.error(f"Error getting formats: {e}")
        return jsonify({"error": "Failed to get formats"}), 500


@app.route("/api/validate-text", methods=["POST"])
@require_api_key
def validate_text():
    """Validate text length and provide splitting suggestions."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        text = data.get("text", "").strip()
        max_length = data.get("max_length", 1000)

        if not text:
            return jsonify({"error": "Text is required"}), 400

        text_length = len(text)
        is_valid = text_length <= max_length

        result = {
            "text_length": text_length,
            "max_length": max_length,
            "is_valid": is_valid,
            "needs_splitting": not is_valid,
        }

        if not is_valid:
            # Provide splitting suggestions
            chunks = split_text_by_length(text, max_length, preserve_words=True)
            result.update(
                {
                    "suggested_chunks": len(chunks),
                    "chunk_preview": [
                        chunk[:100] + "..." if len(chunk) > 100 else chunk for chunk in chunks[:3]
                    ],
                }
            )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Text validation error: {e}")
        return jsonify({"error": "Text validation failed"}), 500


@app.route("/api/generate", methods=["POST"])
@require_api_key
def generate_speech():
    """Generate speech from text using the TTSFM package."""
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Extract parameters
        text = data.get("text", "").strip()
        voice = data.get("voice", Voice.ALLOY.value)
        response_format = data.get("format", AudioFormat.MP3.value)
        instructions = data.get("instructions", "").strip() or None
        max_length = data.get("max_length", 1000)
        validate_length = data.get("validate_length", True)

        # Validate required fields
        if not text:
            return jsonify({"error": "Text is required"}), 400

        # Validate voice
        try:
            voice_enum = Voice(voice.lower())
        except ValueError:
            voice_options = ", ".join(v.value for v in Voice)
            return (
                jsonify({"error": (f"Invalid voice: {voice}. Must be one of: {voice_options}")}),
                400,
            )

        # Validate format
        try:
            format_enum = AudioFormat(response_format.lower())
        except ValueError:
            format_options = ", ".join(fmt.value for fmt in AudioFormat)
            return (
                jsonify(
                    {
                        "error": (
                            "Invalid format: "
                            f"{response_format}. Must be one of: {format_options}"
                        )
                    }
                ),
                400,
            )

        effective_format = get_supported_format(format_enum)
        if len(text) > max_length and effective_format is AudioFormat.MP3:
            effective_format = AudioFormat.WAV

        logger.info(
            "Generating speech: text='%s...', voice=%s, requested_format=%s (effective=%s)",
            text[:50],
            voice,
            response_format,
            effective_format.value,
        )

        client = create_tts_client()
        response = client.generate_speech(
            text=text,
            voice=voice_enum,
            response_format=format_enum,
            instructions=instructions,
            max_length=max_length,
            validate_length=validate_length,
        )

        headers = {
            "Content-Disposition": f'attachment; filename="speech.{response.format.value}"',
            "X-Audio-Format": response.format.value,
            "X-Audio-Size": str(response.size),
            "X-Requested-Format": format_enum.value,
            "X-Effective-Format": effective_format.value,
        }

        return Response(
            stream_with_context(_chunk_bytes(response.audio_data)),
            mimetype=response.content_type,
            headers=headers,
            direct_passthrough=True,
        )

    except ValidationException as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": "Invalid input parameters"}), 400

    except APIException as e:
        logger.error(f"API error: {e}")
        return jsonify(
            {"error": "TTS service error", "status_code": getattr(e, "status_code", 500)}
        ), getattr(e, "status_code", 500)

    except NetworkException as e:
        logger.error(f"Network error: {e}")
        return jsonify({"error": "TTS service is currently unavailable"}), 503

    except TTSException as e:
        logger.error(f"TTS error: {e}")
        return jsonify({"error": "Text-to-speech generation failed"}), 500

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/generate-combined", methods=["POST"])
@require_api_key
def generate_speech_combined():
    """Generate speech from long text and return a single combined audio file."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        text = data.get("text", "").strip()
        voice = data.get("voice", Voice.ALLOY.value)
        response_format = data.get("format", AudioFormat.MP3.value)
        instructions = data.get("instructions", "").strip() or None
        max_length = data.get("max_length", 1000)
        preserve_words = data.get("preserve_words", True)

        if not text:
            return jsonify({"error": "Text is required"}), 400

        try:
            voice_enum = Voice(voice.lower())
            format_enum = AudioFormat(response_format.lower())
        except ValueError as e:
            logger.warning(f"Invalid voice or format: {e}")
            return jsonify({"error": "Invalid voice or format specified"}), 400

        effective_format = get_supported_format(format_enum)

        # Check if text needs splitting
        if len(text) <= max_length:
            client = create_tts_client()

            response = client.generate_speech(
                text=text,
                voice=voice_enum,
                response_format=format_enum,
                instructions=instructions,
                max_length=max_length,
                validate_length=True,
            )

            single_headers = {
                "Content-Disposition": (
                    f'attachment; filename="combined_speech.{response.format.value}"'
                ),
                "X-Audio-Format": response.format.value,
                "X-Audio-Size": str(response.size),
                "X-Chunks-Combined": "1",
                "X-Requested-Format": format_enum.value,
                "X-Effective-Format": effective_format.value,
            }

            return Response(
                stream_with_context(_chunk_bytes(response.audio_data)),
                mimetype=response.content_type,
                headers=single_headers,
                direct_passthrough=True,
            )

        # Text is long, split and combine
        try:
            voice_enum = Voice(voice.lower())
            format_enum = AudioFormat(response_format.lower())
        except ValueError as e:
            logger.warning(f"Invalid voice or format: {e}")
            return jsonify({"error": "Invalid voice or format specified"}), 400

        logger.info(
            "Combining long text (%s chars) using format %s",
            len(text),
            effective_format.value,
        )

        # Generate speech chunks
        try:
            client = create_tts_client()

            responses = client.generate_speech_long_text(
                text=text,
                voice=voice_enum,
                response_format=effective_format,
                instructions=instructions,
                max_length=max_length,
                preserve_words=preserve_words,
            )
        except Exception as e:
            logger.error(f"Long text generation failed: {e}")
            return jsonify({"error": "Long text generation failed"}), 500

        if not responses:
            return jsonify({"error": "No valid text chunks found"}), 400

        logger.info(
            "Generated %s chunks, combining into single audio file",
            len(responses),
        )

        # Extract audio data from responses
        audio_chunks = [resp.audio_data for resp in responses]

        # Combine audio chunks
        try:
            actual_format = responses[0].format
            combined_audio = combine_audio_chunks(audio_chunks, actual_format.value)
        except Exception as e:
            logger.error(f"Failed to combine audio chunks: {e}")
            return jsonify({"error": "Failed to combine audio chunks"}), 500

        if not combined_audio:
            return jsonify({"error": "Failed to generate combined audio"}), 500

        # Determine content type
        # Use content type from first chunk
        content_type = responses[0].content_type

        logger.info(
            "Successfully combined %s chunks into single audio file (%s bytes)",
            len(responses),
            len(combined_audio),
        )

        combined_headers = {
            "Content-Disposition": (
                f'attachment; filename="combined_speech.{actual_format.value}"'
            ),
            "X-Audio-Format": actual_format.value,
            "X-Audio-Size": str(len(combined_audio)),
            "X-Chunks-Combined": str(len(responses)),
            "X-Original-Text-Length": str(len(text)),
            "X-Auto-Combine": "true",
            "X-Powered-By": "TTSFM-OpenAI-Compatible",
            "X-Requested-Format": format_enum.value,
            "X-Effective-Format": effective_format.value,
        }

        return Response(
            stream_with_context(_chunk_bytes(combined_audio)),
            mimetype=content_type,
            headers=combined_headers,
            direct_passthrough=True,
        )

    except ValidationException as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": "Invalid input parameters"}), 400

    except APIException as e:
        logger.error(f"API error: {e}")
        return jsonify(
            {"error": "TTS service error", "status_code": getattr(e, "status_code", 500)}
        ), getattr(e, "status_code", 500)

    except NetworkException as e:
        logger.error(f"Network error: {e}")
        return jsonify({"error": "TTS service is currently unavailable"}), 503

    except TTSException as e:
        logger.error(f"TTS error: {e}")
        return jsonify({"error": "Text-to-speech generation failed"}), 500

    except Exception as e:
        logger.error(f"Combined generation error: {e}")
        return jsonify({"error": "Combined audio generation failed"}), 500


@app.route("/api/status", methods=["GET"])
def get_status():
    """Get service status."""
    try:
        # Try to make a simple request to check if the TTS service is available
        client = create_tts_client()

        client.generate_speech(text="test", voice=Voice.ALLOY, response_format=AudioFormat.MP3)

        return jsonify(
            {
                "status": "online",
                "tts_service": "openai.fm (free)",
                "package_version": "3.3.1",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "tts_service": "openai.fm (free)",
                    "error": "Service status check failed",
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            503,
        )


@app.route("/api/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    return jsonify(
        {"status": "healthy", "package_version": "3.3.4", "timestamp": datetime.now().isoformat()}
    )


@app.route("/api/websocket/status", methods=["GET"])
def websocket_status():
    """Get WebSocket server status and active connections."""
    return jsonify(
        {
            "websocket_enabled": True,
            "async_mode": async_mode,
            "active_sessions": websocket_handler.get_active_sessions_count(),
            "transport_options": ["websocket", "polling"],
            "endpoint": f"ws{'s' if request.is_secure else ''}://{request.host}/socket.io/",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/auth-status", methods=["GET"])
def auth_status():
    """Get authentication status and requirements."""
    return jsonify(
        {
            "api_key_required": REQUIRE_API_KEY,
            "api_key_configured": API_KEYS_CONFIGURED if REQUIRE_API_KEY else None,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/translations/<lang_code>", methods=["GET"])
def get_translations(lang_code):
    """Get translations for a specific language."""
    try:
        if hasattr(app, "language_manager"):
            translations = app.language_manager.translations.get(lang_code, {})
            return jsonify(translations)
        else:
            return jsonify({}), 404
    except Exception as e:
        logger.error(f"Error getting translations for {lang_code}: {e}")
        return jsonify({"error": "Failed to get translations"}), 500


# OpenAI-compatible API endpoints


@app.route("/v1/audio/speech", methods=["POST"])
@require_api_key
def openai_speech():
    """OpenAI-compatible speech generation endpoint with auto-combine feature."""
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {
                        "error": {
                            "message": "No JSON data provided",
                            "type": "invalid_request_error",
                            "code": "missing_data",
                        }
                    }
                ),
                400,
            )

        # Extract OpenAI-compatible parameters
        input_text = data.get("input", "").strip()
        voice = data.get("voice", "alloy")
        response_format = data.get("response_format", "mp3")
        instructions = data.get("instructions", "").strip() or None

        # TTSFM-specific parameters
        # New parameter: auto-combine long text (default: True)
        auto_combine = data.get("auto_combine", True)
        # Custom parameter for chunk size
        max_length = data.get("max_length", 1000)

        # Validate required fields
        if not input_text:
            return (
                jsonify(
                    {
                        "error": {
                            "message": "Input text is required",
                            "type": "invalid_request_error",
                            "code": "missing_input",
                        }
                    }
                ),
                400,
            )

        # Validate voice
        try:
            voice_enum = Voice(voice.lower())
        except ValueError:
            voice_options = ", ".join(v.value for v in Voice)
            return (
                jsonify(
                    {
                        "error": {
                            "message": (f"Invalid voice: {voice}. Must be one of: {voice_options}"),
                            "type": "invalid_request_error",
                            "code": "invalid_voice",
                        }
                    }
                ),
                400,
            )

        # Validate format
        try:
            format_enum = AudioFormat(response_format.lower())
        except ValueError:
            format_options = ", ".join(fmt.value for fmt in AudioFormat)
            return (
                jsonify(
                    {
                        "error": {
                            "message": (
                                "Invalid response_format: "
                                f"{response_format}. Must be one of: {format_options}"
                            ),
                            "type": "invalid_request_error",
                            "code": "invalid_format",
                        }
                    }
                ),
                400,
            )

        effective_format = get_supported_format(format_enum)

        logger.info(
            "OpenAI API: Generating speech: text='%s...', voice=%s, "
            "requested_format=%s (effective=%s), auto_combine=%s",
            input_text[:50],
            voice,
            response_format,
            effective_format.value,
            auto_combine,
        )

        client = create_tts_client()

        # Check if text exceeds limit and auto_combine is enabled
        if len(input_text) > max_length and auto_combine:
            # Long text with auto-combine enabled: split and combine
            logger.info(
                "Long text detected (%s chars); auto-combining with format %s",
                len(input_text),
                effective_format.value,
            )

            # Generate speech chunks
            responses = client.generate_speech_long_text(
                text=input_text,
                voice=voice_enum,
                response_format=effective_format,
                instructions=instructions,
                max_length=max_length,
                preserve_words=True,
            )

            if not responses:
                return (
                    jsonify(
                        {
                            "error": {
                                "message": "No valid text chunks found",
                                "type": "processing_error",
                                "code": "no_chunks",
                            }
                        }
                    ),
                    400,
                )

            # Extract audio data and combine
            audio_chunks = [resp.audio_data for resp in responses]
            actual_format = responses[0].format
            combined_audio = combine_audio_chunks(audio_chunks, actual_format.value)

            if not combined_audio:
                return (
                    jsonify(
                        {
                            "error": {
                                "message": "Failed to combine audio chunks",
                                "type": "processing_error",
                                "code": "combine_failed",
                            }
                        }
                    ),
                    500,
                )

            content_type = responses[0].content_type

            logger.info(
                "Successfully combined %s chunks into single audio file",
                len(responses),
            )

            headers = {
                "Content-Type": content_type,
                "X-Audio-Format": actual_format.value,
                "X-Audio-Size": str(len(combined_audio)),
                "X-Chunks-Combined": str(len(responses)),
                "X-Original-Text-Length": str(len(input_text)),
                "X-Auto-Combine": "true",
                "X-Powered-By": "TTSFM-OpenAI-Compatible",
                "X-Requested-Format": format_enum.value,
                "X-Effective-Format": effective_format.value,
            }

            return Response(
                stream_with_context(_chunk_bytes(combined_audio)),
                mimetype=content_type,
                headers=headers,
                direct_passthrough=True,
            )

        else:
            # Short text or auto_combine disabled: use regular generation
            if len(input_text) > max_length and not auto_combine:
                # Text is too long but auto_combine is disabled - return error
                return (
                    jsonify(
                        {
                            "error": {
                                "message": (
                                    f"Input text is too long ({len(input_text)} characters). "
                                    f"Maximum allowed length is {max_length} characters. "
                                    "Enable the auto_combine parameter to split and combine "
                                    "long input automatically."
                                ),
                                "type": "invalid_request_error",
                                "code": "text_too_long",
                            }
                        }
                    ),
                    400,
                )

            # Generate speech using the TTSFM package
            response = client.generate_speech(
                text=input_text,
                voice=voice_enum,
                response_format=format_enum,
                instructions=instructions,
                max_length=max_length,
                validate_length=True,
            )

            headers = {
                "Content-Type": response.content_type,
                "X-Audio-Format": response.format.value,
                "X-Audio-Size": str(response.size),
                "X-Chunks-Combined": "1",
                "X-Auto-Combine": str(auto_combine).lower(),
                "X-Powered-By": "TTSFM-OpenAI-Compatible",
                "X-Requested-Format": format_enum.value,
                "X-Effective-Format": effective_format.value,
            }

            return Response(
                stream_with_context(_chunk_bytes(response.audio_data)),
                mimetype=response.content_type,
                headers=headers,
                direct_passthrough=True,
            )

    except ValidationException as e:
        logger.warning(f"OpenAI API validation error: {e}")
        return (
            jsonify(
                {
                    "error": {
                        "message": "Invalid request parameters",
                        "type": "invalid_request_error",
                        "code": "validation_error",
                    }
                }
            ),
            400,
        )

    except APIException as e:
        logger.error(f"OpenAI API error: {e}")
        return jsonify(
            {
                "error": {
                    "message": "Text-to-speech generation failed",
                    "type": "api_error",
                    "code": "tts_error",
                }
            }
        ), getattr(e, "status_code", 500)

    except NetworkException as e:
        logger.error(f"OpenAI API network error: {e}")
        return (
            jsonify(
                {
                    "error": {
                        "message": "TTS service is currently unavailable",
                        "type": "service_unavailable_error",
                        "code": "service_unavailable",
                    }
                }
            ),
            503,
        )

    except Exception as e:
        logger.error(f"OpenAI API unexpected error: {e}")
        return (
            jsonify(
                {
                    "error": {
                        "message": "An unexpected error occurred",
                        "type": "internal_error",
                        "code": "internal_error",
                    }
                }
            ),
            500,
        )


@app.route("/v1/models", methods=["GET"])
def openai_models():
    """OpenAI-compatible models endpoint."""
    return jsonify(
        {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4o-mini-tts",
                    "object": "model",
                    "created": 1699564800,
                    "owned_by": "ttsfm",
                    "permission": [],
                    "root": "gpt-4o-mini-tts",
                    "parent": None,
                }
            ],
        }
    )


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info(f"Starting TTSFM web application on {HOST}:{PORT}")
    logger.info("Using openai.fm free TTS service")
    logger.info(f"Debug mode: {DEBUG}")

    # Log API key protection status
    if REQUIRE_API_KEY:
        if API_KEYS_CONFIGURED:
            logger.info("🔒 API key protection is ENABLED")
            logger.info("All TTS generation requests require a valid API key")
        else:
            logger.warning(
                "⚠️ API key protection is enabled but TTSFM_API_KEY(S) are not configured!"
            )
            logger.warning("Please set the TTSFM_API_KEY or TTSFM_API_KEYS environment variables")
    else:
        logger.info("🔓 API key protection is DISABLED - all requests are allowed")
        logger.info("Set REQUIRE_API_KEY=true to enable API key protection")

    try:
        logger.info(f"Starting with {async_mode} async mode")
        socketio.run(app, host=HOST, port=PORT, debug=DEBUG)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
    finally:
        logger.info("TTSFM web application shut down")
