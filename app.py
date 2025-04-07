"""
This module provides a server that's compatible with OpenAI's TTS API format.
Main entry point for the Flask application.
"""

import os
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from celery.result import AsyncResult
from celery_worker import celery, process_tts_request

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
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Rate limiting per IP
ip_request_counts = defaultdict(list)

# Create Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Configure CORS to allow requests from any origin
CORS(app)

# Voice samples directory
VOICE_SAMPLES_DIR = Path('voices')

def _is_rate_limited(ip):
    """Check if IP is rate limited"""
    now = datetime.now()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    
    # Clean old requests
    ip_request_counts[ip] = [t for t in ip_request_counts[ip] if t > window_start]
    
    # Check if rate limited
    if len(ip_request_counts[ip]) >= RATE_LIMIT_REQUESTS:
        return True
    
    # Add current request
    ip_request_counts[ip].append(now)
    return False

@app.route('/')
def index():
    """Render the main index page"""
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    """Serve static files"""
    if path == '':
        return send_from_directory('static', 'index.html')
    
    full_path = Path('static') / path
    
    if full_path.exists():
        # Determine content type
        content_type = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.gif': 'image/gif',
            '.ico': 'image/x-icon'
        }.get(full_path.suffix, 'application/octet-stream')
        
        return send_file(full_path, mimetype=content_type)
    
    return "Not found", 404

@app.route('/v1/audio/speech', methods=['POST'])
def openai_speech():
    """Handle POST requests to /v1/audio/speech (OpenAI compatible API)"""
    try:
        # Rate limiting check
        client_ip = request.remote_addr
        if _is_rate_limited(client_ip):
            return jsonify({
                "error": "Rate limit exceeded. Please try again later.",
                "retry_after": RATE_LIMIT_WINDOW
            }), 429, {"Retry-After": str(RATE_LIMIT_WINDOW)}

        # Check queue size from Celery
        active_tasks = celery.control.inspect().active()
        if active_tasks and sum(len(tasks) for tasks in active_tasks.values()) >= MAX_QUEUE_SIZE:
            return jsonify({
                "error": "Queue is full. Please try again later.",
                "queue_size": MAX_QUEUE_SIZE
            }), 429

        # Read JSON data
        body = request.get_json()
        
        # Map OpenAI format to our internal format
        openai_fm_data = {}
        content_type = "audio/mpeg"
        
        # Required parameters
        if 'input' not in body or 'voice' not in body:
            return jsonify({
                "error": "Missing required parameters: input and voice"
            }), 400
        
        openai_fm_data['input'] = body['input']
        openai_fm_data['voice'] = body['voice']
        
        # Map 'instructions' to 'prompt' if provided
        if 'instructions' in body:
            openai_fm_data['prompt'] = body['instructions']
        
        # Check for response_format
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
                return jsonify({
                    "error": f"Unsupported response format: {requested_format}. Supported formats are: {', '.join(format_mapping.keys())}"
                }), 400
            content_type = format_mapping[requested_format]
            openai_fm_data['format'] = requested_format
        
        # Create task data
        task_data = {
            'data': openai_fm_data,
            'content_type': content_type,
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip
        }
        
        # Submit task to Celery
        task = process_tts_request.delay(task_data)
        
        # Wait for result with timeout
        try:
            audio_data, error, status_code = task.get(timeout=30)
            
            if error:
                return jsonify({"error": error}), status_code
            
            # Return the audio data
            return Response(
                audio_data,
                mimetype=task_data['content_type'],
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                }
            )
        except TimeoutError:
            return jsonify({
                "error": "Request timed out. Please try again.",
                "task_id": task.id
            }), 408
                
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in request body"}), 400
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/queue-size', methods=['GET'])
def queue_size():
    """Handle GET requests to /api/queue-size"""
    try:
        # Get queue information from Celery
        i = celery.control.inspect()
        active = i.active()
        reserved = i.reserved()
        
        # Calculate current queue size
        current_size = 0
        if active:
            current_size += sum(len(tasks) for tasks in active.values())
        if reserved:
            current_size += sum(len(tasks) for tasks in reserved.values())
        
        return jsonify({
            "queue_size": current_size,
            "max_queue_size": MAX_QUEUE_SIZE
        }), 200, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    except Exception as e:
        logger.error(f"Error getting queue size: {str(e)}")
        return jsonify({
            "queue_size": 0,
            "max_queue_size": MAX_QUEUE_SIZE,
            "error": "Failed to get queue status"
        }), 500, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }

@app.route('/api/voice-sample/<voice>', methods=['GET'])
def voice_sample(voice):
    """Handle GET requests for voice samples"""
    try:
        if not voice:
            return jsonify({
                "error": "Voice parameter is required"
            }), 400
            
        sample_path = VOICE_SAMPLES_DIR / f"{voice}_sample.mp3"
        if not sample_path.exists():
            return jsonify({
                "error": f"Sample not found for voice: {voice}"
            }), 404
            
        return send_file(
            sample_path,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name=f"{voice}_sample.mp3"
        )
        
    except Exception as e:
        logger.error(f"Error serving voice sample: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/api/version', methods=['GET'])
def get_version():
    """Handle GET requests for API version"""
    return jsonify({
        "version": "v2.0.0"
    }), 200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

# Handle OPTIONS requests for CORS
@app.route('/v1/audio/speech', methods=['OPTIONS'])
def handle_options_speech():
    return '', 200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }

@app.route('/api/queue-size', methods=['OPTIONS'])
def handle_options_queue():
    return '', 200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=False) 