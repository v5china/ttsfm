"""
TTSFM Web Application

A Flask web application that provides a user-friendly interface
for the TTSFM text-to-speech package.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, send_file, Response, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Import the TTSFM package
try:
    from ttsfm import TTSClient, Voice, AudioFormat, TTSException
    from ttsfm.exceptions import APIException, NetworkException, ValidationException
    from ttsfm.utils import validate_text_length, split_text_by_length
except ImportError:
    # Fallback for development when package is not installed
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from ttsfm import TTSClient, Voice, AudioFormat, TTSException
    from ttsfm.exceptions import APIException, NetworkException, ValidationException
    from ttsfm.utils import validate_text_length, split_text_by_length

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Configuration
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Create TTS client - now uses openai.fm directly, no configuration needed
tts_client = TTSClient()

logger.info("Initialized web app with TTSFM using openai.fm free service")

@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')

@app.route('/playground')
def playground():
    """Serve the interactive playground."""
    return render_template('playground.html')

@app.route('/docs')
def docs():
    """Serve the API documentation."""
    return render_template('docs.html')

@app.route('/api/voices', methods=['GET'])
def get_voices():
    """Get list of available voices."""
    try:
        voices = [
            {
                "id": voice.value,
                "name": voice.value.title(),
                "description": f"{voice.value.title()} voice"
            }
            for voice in Voice
        ]
        
        return jsonify({
            "voices": voices,
            "count": len(voices)
        })
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return jsonify({"error": "Failed to get voices"}), 500

@app.route('/api/formats', methods=['GET'])
def get_formats():
    """Get list of supported audio formats."""
    try:
        formats = [
            {
                "id": fmt.value,
                "name": fmt.value.upper(),
                "mime_type": f"audio/{fmt.value}",
                "description": f"{fmt.value.upper()} audio format"
            }
            for fmt in AudioFormat
        ]
        
        return jsonify({
            "formats": formats,
            "count": len(formats)
        })
        
    except Exception as e:
        logger.error(f"Error getting formats: {e}")
        return jsonify({"error": "Failed to get formats"}), 500

@app.route('/api/validate-text', methods=['POST'])
def validate_text():
    """Validate text length and provide splitting suggestions."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        text = data.get('text', '').strip()
        max_length = data.get('max_length', 4096)

        if not text:
            return jsonify({"error": "Text is required"}), 400

        text_length = len(text)
        is_valid = text_length <= max_length

        result = {
            "text_length": text_length,
            "max_length": max_length,
            "is_valid": is_valid,
            "needs_splitting": not is_valid
        }

        if not is_valid:
            # Provide splitting suggestions
            chunks = split_text_by_length(text, max_length, preserve_words=True)
            result.update({
                "suggested_chunks": len(chunks),
                "chunk_preview": [chunk[:100] + "..." if len(chunk) > 100 else chunk for chunk in chunks[:3]]
            })

        return jsonify(result)

    except Exception as e:
        logger.error(f"Text validation error: {e}")
        return jsonify({"error": "Text validation failed"}), 500

@app.route('/api/generate', methods=['POST'])
def generate_speech():
    """Generate speech from text using the TTSFM package."""
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Extract parameters
        text = data.get('text', '').strip()
        voice = data.get('voice', Voice.ALLOY.value)
        response_format = data.get('format', AudioFormat.MP3.value)
        instructions = data.get('instructions', '').strip() or None
        max_length = data.get('max_length', 4096)
        validate_length = data.get('validate_length', True)
        
        # Validate required fields
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Validate voice
        try:
            voice_enum = Voice(voice.lower())
        except ValueError:
            return jsonify({
                "error": f"Invalid voice: {voice}. Must be one of: {[v.value for v in Voice]}"
            }), 400
        
        # Validate format
        try:
            format_enum = AudioFormat(response_format.lower())
        except ValueError:
            return jsonify({
                "error": f"Invalid format: {response_format}. Must be one of: {[f.value for f in AudioFormat]}"
            }), 400
        
        logger.info(f"Generating speech: text='{text[:50]}...', voice={voice}, format={response_format}")
        
        # Generate speech using the TTSFM package with validation
        response = tts_client.generate_speech(
            text=text,
            voice=voice_enum,
            response_format=format_enum,
            instructions=instructions,
            max_length=max_length,
            validate_length=validate_length
        )
        
        # Return audio data
        return Response(
            response.audio_data,
            mimetype=response.content_type,
            headers={
                'Content-Disposition': f'attachment; filename="speech.{response.format.value}"',
                'Content-Length': str(response.size),
                'X-Audio-Format': response.format.value,
                'X-Audio-Size': str(response.size)
            }
        )
        
    except ValidationException as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
        
    except APIException as e:
        logger.error(f"API error: {e}")
        return jsonify({
            "error": str(e),
            "status_code": getattr(e, 'status_code', 500)
        }), getattr(e, 'status_code', 500)
        
    except NetworkException as e:
        logger.error(f"Network error: {e}")
        return jsonify({
            "error": "TTS service is currently unavailable",
            "details": str(e)
        }), 503
        
    except TTSException as e:
        logger.error(f"TTS error: {e}")
        return jsonify({"error": str(e)}), 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/generate-batch', methods=['POST'])
def generate_speech_batch():
    """Generate speech from long text by splitting into chunks."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        text = data.get('text', '').strip()
        voice = data.get('voice', Voice.ALLOY.value)
        response_format = data.get('format', AudioFormat.MP3.value)
        instructions = data.get('instructions', '').strip() or None
        max_length = data.get('max_length', 4096)
        preserve_words = data.get('preserve_words', True)

        if not text:
            return jsonify({"error": "Text is required"}), 400

        # Validate voice and format
        try:
            voice_enum = Voice(voice.lower())
            format_enum = AudioFormat(response_format.lower())
        except ValueError as e:
            return jsonify({"error": f"Invalid voice or format: {e}"}), 400

        # Split text into chunks
        chunks = split_text_by_length(text, max_length, preserve_words)

        if not chunks:
            return jsonify({"error": "No valid text chunks found"}), 400

        logger.info(f"Processing {len(chunks)} chunks for batch generation")

        # Generate speech for each chunk
        results = []
        for i, chunk in enumerate(chunks):
            try:
                response = tts_client.generate_speech(
                    text=chunk,
                    voice=voice_enum,
                    response_format=format_enum,
                    instructions=instructions,
                    max_length=max_length,
                    validate_length=False  # Already split
                )

                # Convert to base64 for JSON response
                import base64
                audio_b64 = base64.b64encode(response.audio_data).decode('utf-8')

                results.append({
                    "chunk_index": i + 1,
                    "chunk_text": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    "audio_data": audio_b64,
                    "content_type": response.content_type,
                    "size": response.size,
                    "format": response.format.value
                })

            except Exception as e:
                logger.error(f"Failed to generate chunk {i+1}: {e}")
                results.append({
                    "chunk_index": i + 1,
                    "chunk_text": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    "error": str(e)
                })

        return jsonify({
            "total_chunks": len(chunks),
            "successful_chunks": len([r for r in results if "audio_data" in r]),
            "results": results
        })

    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        return jsonify({"error": "Batch generation failed"}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get service status."""
    try:
        # Try to make a simple request to check if the TTS service is available
        test_response = tts_client.generate_speech(
            text="test",
            voice=Voice.ALLOY,
            response_format=AudioFormat.MP3
        )
        
        return jsonify({
            "status": "online",
            "tts_service": "openai.fm (free)",
            "package_version": "3.0.0",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            "status": "error",
            "tts_service": "openai.fm (free)",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

# OpenAI-compatible API endpoints
@app.route('/v1/audio/speech', methods=['POST'])
def openai_speech():
    """OpenAI-compatible speech generation endpoint."""
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                "error": {
                    "message": "No JSON data provided",
                    "type": "invalid_request_error",
                    "code": "missing_data"
                }
            }), 400

        # Extract OpenAI-compatible parameters
        model = data.get('model', 'gpt-4o-mini-tts')  # Accept but ignore model
        input_text = data.get('input', '').strip()
        voice = data.get('voice', 'alloy')
        response_format = data.get('response_format', 'mp3')
        instructions = data.get('instructions', '').strip() or None
        speed = data.get('speed', 1.0)  # Accept but ignore speed

        # Validate required fields
        if not input_text:
            return jsonify({
                "error": {
                    "message": "Input text is required",
                    "type": "invalid_request_error",
                    "code": "missing_input"
                }
            }), 400

        # Validate voice
        try:
            voice_enum = Voice(voice.lower())
        except ValueError:
            return jsonify({
                "error": {
                    "message": f"Invalid voice: {voice}. Must be one of: {[v.value for v in Voice]}",
                    "type": "invalid_request_error",
                    "code": "invalid_voice"
                }
            }), 400

        # Validate format
        try:
            format_enum = AudioFormat(response_format.lower())
        except ValueError:
            return jsonify({
                "error": {
                    "message": f"Invalid response_format: {response_format}. Must be one of: {[f.value for f in AudioFormat]}",
                    "type": "invalid_request_error",
                    "code": "invalid_format"
                }
            }), 400

        logger.info(f"OpenAI API: Generating speech: text='{input_text[:50]}...', voice={voice}, format={response_format}")

        # Generate speech using the TTSFM package
        response = tts_client.generate_speech(
            text=input_text,
            voice=voice_enum,
            response_format=format_enum,
            instructions=instructions,
            max_length=4096,
            validate_length=True
        )

        # Return audio data in OpenAI format
        return Response(
            response.audio_data,
            mimetype=response.content_type,
            headers={
                'Content-Type': response.content_type,
                'Content-Length': str(response.size),
                'X-Audio-Format': response.format.value,
                'X-Audio-Size': str(response.size),
                'X-Powered-By': 'TTSFM-OpenAI-Compatible'
            }
        )

    except ValidationException as e:
        logger.warning(f"OpenAI API validation error: {e}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "invalid_request_error",
                "code": "validation_error"
            }
        }), 400

    except APIException as e:
        logger.error(f"OpenAI API error: {e}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "api_error",
                "code": "tts_error"
            }
        }), getattr(e, 'status_code', 500)

    except NetworkException as e:
        logger.error(f"OpenAI API network error: {e}")
        return jsonify({
            "error": {
                "message": "TTS service is currently unavailable",
                "type": "service_unavailable_error",
                "code": "service_unavailable"
            }
        }), 503

    except Exception as e:
        logger.error(f"OpenAI API unexpected error: {e}")
        return jsonify({
            "error": {
                "message": "An unexpected error occurred",
                "type": "internal_error",
                "code": "internal_error"
            }
        }), 500

@app.route('/v1/models', methods=['GET'])
def openai_models():
    """OpenAI-compatible models endpoint."""
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "gpt-4o-mini-tts",
                "object": "model",
                "created": 1699564800,
                "owned_by": "ttsfm",
                "permission": [],
                "root": "gpt-4o-mini-tts",
                "parent": None
            }
        ]
    })

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

if __name__ == '__main__':
    logger.info(f"Starting TTSFM web application on {HOST}:{PORT}")
    logger.info("Using openai.fm free TTS service")
    logger.info(f"Debug mode: {DEBUG}")
    
    try:
        app.run(
            host=HOST,
            port=PORT,
            debug=DEBUG
        )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
    finally:
        # Clean up TTS client
        tts_client.close()
