"""
This module provides a server that's compatible with OpenAI's TTS API format.
Main entry point for the Flask application.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from flask import Flask, request, jsonify, send_file, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from celery.result import AsyncResult
from celery_worker import celery, process_tts_request
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
import os.path
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# App configuration from environment variables
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", "7000"))
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() != "false"
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "100"))

# Security configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size

# Create Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Configure CORS with specific routes and security
CORS(app, resources={
    r"/v1/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    },
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "max_age": 3600
    }
})

# Set maximum content length
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Voice samples directory
VOICE_SAMPLES_DIR = Path('voices')

def _sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and other attacks"""
    # Remove any HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove any script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    # Remove any potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()

# Error handlers
@app.errorhandler(HTTPException)
def handle_http_error(error: HTTPException) -> Tuple[Dict[str, str], int]:
    """Handle HTTP errors"""
    logger.warning(f"HTTP error: {error.code} - {error.description}")
    return jsonify({"error": error.description}), error.code

@app.errorhandler(Exception)
def handle_generic_error(error: Exception) -> Tuple[Dict[str, str], int]:
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    return jsonify({"error": "Internal Server Error"}), 500

@app.after_request
def add_security_headers(response: Response) -> Response:
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "script-src 'self' https://cdnjs.cloudflare.com; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "media-src 'self' blob:; "
        "connect-src 'self'"
    )
    return response

@app.route('/')
def index() -> Response:
    """Render the main index page"""
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename: str) -> Response:
    """Serve static files with correct MIME types"""
    if filename.endswith('.css'):
        return send_from_directory('static', filename, mimetype='text/css')
    elif filename.endswith('.js'):
        return send_from_directory('static', filename, mimetype='application/javascript')
    return send_from_directory('static', filename)

def validate_tts_request(body: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[int]]:
    """Validate TTS request parameters"""
    try:
        # Validate required parameters
        if 'input' not in body or 'voice' not in body:
            return None, "Missing required parameters: input and voice", 400
        
        # Sanitize input
        sanitized_input = _sanitize_input(body['input'])
        if not sanitized_input:
            return None, "Input text cannot be empty", 400
        
        # Validate voice parameter
        if not isinstance(body['voice'], str) or not body['voice']:
            return None, "Invalid voice parameter", 400
        
        openai_fm_data = {
            'input': sanitized_input,
            'voice': body['voice']
        }
        
        # Validate and sanitize instructions if provided
        if 'instructions' in body:
            if not isinstance(body['instructions'], str):
                return None, "Instructions must be a string", 400
            openai_fm_data['prompt'] = _sanitize_input(body['instructions'])
        
        # Validate response format
        content_type = "audio/mpeg"
        if 'response_format' in body:
            format_mapping = {
                'mp3': 'audio/mpeg',
                'opus': 'audio/opus',
                'aac': 'audio/aac',
                'flac': 'audio/flac',
                'wav': 'audio/wav',
                'pcm': 'audio/pcm'
            }
            requested_format = body['response_format'].lower()
            if requested_format not in format_mapping:
                return None, f"Unsupported response format: {requested_format}. Supported formats are: {', '.join(format_mapping.keys())}", 400
            content_type = format_mapping[requested_format]
            openai_fm_data['format'] = requested_format
        
        return openai_fm_data, None, None
    except Exception as e:
        logger.error(f"Error validating request: {str(e)}")
        return None, "Invalid request format", 400

def get_queue_details() -> Dict[str, Any]:
    """Get detailed queue counts from Celery workers."""
    details = {
        'active': 0,
        'reserved': 0,
        'scheduled': 0,
        'total_reported_by_workers': 0,
        'error': None
    }
    try:
        i = celery.control.inspect(timeout=1.0) # Add timeout
        if not i:
             details['error'] = "Could not connect to Celery workers for inspection."
             return details
             
        active_tasks = i.active()
        reserved_tasks = i.reserved()
        scheduled_tasks = i.scheduled()
        
        if active_tasks:
            details['active'] = sum(len(tasks) for tasks in active_tasks.values())
        if reserved_tasks:
            details['reserved'] = sum(len(tasks) for tasks in reserved_tasks.values())
        if scheduled_tasks:
            details['scheduled'] = sum(len(tasks) for tasks in scheduled_tasks.values())
            
        details['total_reported_by_workers'] = details['active'] + details['reserved'] + details['scheduled']
            
    except Exception as e:
        logger.error(f"Error calculating queue details: {str(e)}")
        details['error'] = f"Failed to inspect Celery workers: {str(e)}"
        # Reset counts to 0 on error to avoid misleading data
        details['active'] = 0
        details['reserved'] = 0
        details['scheduled'] = 0
        details['total_reported_by_workers'] = 0
        
    return details

@app.route('/v1/audio/speech', methods=['POST'])
def openai_speech() -> Response:
    """Handle POST requests to /v1/audio/speech (OpenAI compatible API)"""
    try:
        # Check queue size from Celery worker reports
        queue_details = get_queue_details()
        current_total = queue_details['total_reported_by_workers']
        
        # Check for inspection errors
        if queue_details['error']:
             logger.warning(f"Could not determine queue size due to inspection error: {queue_details['error']}. Allowing request.")
             # Optionally, you could reject here, but allowing might be safer if inspection is flaky
        
        elif current_total >= MAX_QUEUE_SIZE:
            logger.warning(f"Queue is full based on worker reports. Current total: {current_total}, Max size: {MAX_QUEUE_SIZE}")
            return jsonify({
                "error": "Queue is full. Please try again later.",
                "queue_details": queue_details, # Provide detailed counts
                "max_queue_size_limit": MAX_QUEUE_SIZE
            }), 429

        # Read and validate JSON data
        body = request.get_json()
        openai_fm_data, error, status_code = validate_tts_request(body)
        if error:
            return jsonify({"error": error}), status_code
        
        # Determine content type from validation or default
        validated_content_type = "audio/mpeg" # Default
        if 'response_format' in body:
            format_mapping = {
                'mp3': 'audio/mpeg',
                'opus': 'audio/opus',
                'aac': 'audio/aac',
                'flac': 'audio/flac',
                'wav': 'audio/wav',
                'pcm': 'audio/pcm'
            }
            requested_format = body['response_format'].lower()
            if requested_format in format_mapping:
                validated_content_type = format_mapping[requested_format]

        # Create task data
        task_data = {
            'data': openai_fm_data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Submit task to Celery
        task = process_tts_request.delay(task_data)
        
        # Wait for result with timeout
        try:
            audio_data, error, status_code = task.get(timeout=30)
            if error:
                logger.error(f"Task error: {error}")
                return jsonify({"error": error}), status_code
            
            return Response(
                audio_data,
                mimetype=validated_content_type # Use the correctly determined content type
            )
        except TimeoutError:
            logger.error(f"Task timeout: {task.id}")
            return jsonify({
                "error": "Request timed out. Please try again.",
                "task_id": task.id
            }), 408
                
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return jsonify({"error": "Invalid JSON in request body"}), 400
    except Exception as e:
        logger.error(f"Unexpected error in speech endpoint: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/api/queue-size', methods=['GET'])
def queue_size() -> Response:
    """Handle GET requests to /api/queue-size with detailed counts"""
    try:
        queue_details = get_queue_details()
        
        response_data = {
            "active_tasks": queue_details['active'],
            "reserved_tasks": queue_details['reserved'],
            "scheduled_tasks": queue_details['scheduled'],
            "total_reported_by_workers": queue_details['total_reported_by_workers'],
            "max_queue_size_limit": MAX_QUEUE_SIZE,
            "error": queue_details['error']
        }
        
        # Determine status code based on whether there was an inspection error
        status_code = 500 if queue_details['error'] else 200
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        # This handles errors in the route handler itself, not inspection errors
        logger.error(f"Error in /api/queue-size endpoint: {str(e)}")
        return jsonify({
            "active_tasks": 0,
            "reserved_tasks": 0,
            "scheduled_tasks": 0,
            "total_reported_by_workers": 0,
            "max_queue_size_limit": MAX_QUEUE_SIZE,
            "error": "Failed to process queue status request"
        }), 500

@app.route('/api/voice-sample/<voice>', methods=['GET'])
def voice_sample(voice: str) -> Response:
    """Handle GET requests for voice samples"""
    try:
        if not voice:
            return jsonify({
                "error": "Voice parameter is required"
            }), 400
            
        # Secure the voice parameter and prevent path traversal
        secure_voice = secure_filename(voice)
        if not secure_voice or secure_voice != voice:
            logger.warning(f"Invalid voice parameter: {voice}")
            return jsonify({
                "error": "Invalid voice parameter"
            }), 400
            
        # Normalize and validate the path
        base_path = os.path.abspath(VOICE_SAMPLES_DIR)
        sample_path = os.path.normpath(os.path.join(base_path, f"{secure_voice}_sample.mp3"))
        
        # Ensure the path is within the voice samples directory
        if not sample_path.startswith(base_path):
            logger.warning(f"Path traversal attempt: {sample_path}")
            return jsonify({
                "error": "Invalid path"
            }), 400
            
        if not os.path.exists(sample_path):
            logger.warning(f"Sample not found for voice: {voice}")
            return jsonify({
                "error": f"Sample not found for voice: {voice}"
            }), 404
            
        return send_file(
            sample_path,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name=f"{secure_voice}_sample.mp3"
        )
        
    except Exception as e:
        logger.error(f"Error serving voice sample: {str(e)}")
        return jsonify({
            "error": "Internal Server Error"
        }), 500

@app.route('/api/version', methods=['GET'])
def get_version() -> Response:
    """Handle GET requests for API version"""
    return jsonify({
        "version": "v2.0.0-alpha_x"
    })