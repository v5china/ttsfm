"""
HTTP Request Handlers

This module contains the API endpoint handlers for the TTS server.
"""

import json
import time
import logging
import asyncio
import aiohttp
from aiohttp import web
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def handle_openai_speech(request: web.Request, queue, proxy_manager=None, session=None, use_proxy=False) -> web.Response:
    """Handle POST requests to /v1/audio/speech (OpenAI compatible API)."""
    try:
        # Check if queue is full
        if queue.full():
            return web.Response(
                text=json.dumps({
                    "error": "Queue is full. Please try again later.",
                    "queue_size": queue.qsize()
                }),
                status=429,  # Too Many Requests
                content_type="application/json"
            )

        # Read JSON data
        body = await request.json()
        
        # Map OpenAI format to our internal format
        openai_fm_data = {}
        content_type = "audio/mpeg"
        
        # Required parameters
        if 'input' not in body or 'voice' not in body:
            return web.Response(
                text=json.dumps({"error": "Missing required parameters: input and voice"}),
                status=400,
                content_type="application/json"
            )
        
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
            content_type = format_mapping.get(body['response_format'], 'audio/mpeg')
        
        # Create response future
        response_future = asyncio.Future()
        
        # Create task data
        task_data = {
            'data': openai_fm_data,
            'content_type': content_type,
            'response_future': response_future,
            'timestamp': time.time()
        }
        
        # Add to queue
        await queue.put(task_data)
        logger.info(f"Added task to queue. Current size: {queue.qsize()}")
        
        # Wait for response
        return await response_future
                
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return web.Response(
            text=json.dumps({"error": str(e)}),
            status=500,
            content_type="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
            
async def process_tts_request(task_data: Dict[str, Any], session, proxy_manager=None, use_proxy=False) -> web.Response:
    """Process a single TTS request."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Sending request to OpenAI.fm with data: {task_data['data']}")
            
            headers = {
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://www.openai.fm",
                "Referer": "https://www.openai.fm/",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Get proxy if enabled
            proxy = None
            if use_proxy and proxy_manager:
                proxy = await proxy_manager.get_proxy()
                if proxy:
                    logger.info(f"Using proxy: {proxy}")
                else:
                    logger.warning("No proxy available, proceeding without proxy")
            
            request_kwargs = {
                "data": task_data['data'],
                "headers": headers
            }
            
            if proxy:
                request_kwargs["proxy"] = proxy
            
            async with session.post(
                "https://www.openai.fm/api/generate",
                **request_kwargs
            ) as response:
                if response.status == 403:
                    logger.warning("Received 403 Forbidden from OpenAI.fm")
                    if use_proxy and proxy_manager:
                        logger.info("Rotating proxy and retrying")
                        retry_count += 1
                        await asyncio.sleep(1)
                        continue
                
                audio_data = await response.read()
                
                if response.status != 200:
                    logger.error(f"Error from OpenAI.fm: {response.status}")
                    error_msg = f"Error from upstream service: {response.status}"
                    return web.Response(
                        text=json.dumps({"error": error_msg}),
                        status=response.status,
                        content_type="application/json"
                    )
                
                return web.Response(
                    body=audio_data,
                    content_type=task_data['content_type'],
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization"
                    }
                )
        except aiohttp.ClientProxyConnectionError:
            logger.warning(f"Proxy connection error, retrying with new proxy (attempt {retry_count+1}/{max_retries})")
            retry_count += 1
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error processing TTS request: {str(e)}")
            return web.Response(
                text=json.dumps({"error": str(e)}),
                status=500,
                content_type="application/json"
            )
            
    # If we've exhausted retries
    logger.error("Exhausted retries for TTS request")
    return web.Response(
        text=json.dumps({"error": "Failed to process request after multiple retries"}),
        status=500,
        content_type="application/json"
    )

async def handle_queue_size(request: web.Request, queue) -> web.Response:
    """Handle GET requests to /api/queue-size."""
    return web.json_response({
        "queue_size": queue.qsize(),
        "max_queue_size": queue.maxsize
    }, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    })
        
async def handle_static(request: web.Request) -> web.Response:
    """Handle static file requests.
    
    Args:
        request: The incoming request
        
    Returns:
        web.Response: The response to send back
    """
    try:
        # Get file path from request
        file_path = request.match_info['tail']
        if not file_path:
            file_path = 'index.html'
            
        # Construct full path - look in static directory
        full_path = Path(__file__).parent.parent / 'static' / file_path
        
        # Check if file exists
        if not full_path.exists():
            return web.Response(text="Not found", status=404)
            
        # Read file
        with open(full_path, 'rb') as f:
            content = f.read()
            
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
        
        # Return response
        return web.Response(
            body=content,
            content_type=content_type,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )
        
    except Exception as e:
        logger.error(f"Error serving static file: {str(e)}")
        return web.Response(text=str(e), status=500) 