"""
OpenAI TTS API Server

This module provides a server that's compatible with OpenAI's TTS API format.
"""

import asyncio
import aiohttp
from aiohttp import web
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import time
import ssl
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProxyManager:
    """Manages a pool of proxies for rotating IP addresses."""
    
    def __init__(self, api_url: str = "https://proxy.scdn.io/api/get_proxy.php", 
                 protocol: str = "http", batch_size: int = 5):
        """Initialize the proxy manager.
        
        Args:
            api_url: URL of the proxy pool API
            protocol: Proxy protocol to use (http, https, socks4, socks5, all)
            batch_size: Number of proxies to fetch at once
        """
        self.api_url = api_url
        self.protocol = protocol
        self.batch_size = batch_size
        self.proxies = []
        self.session = None
        self.lock = asyncio.Lock()
        
    async def initialize(self, session: aiohttp.ClientSession):
        """Initialize the proxy manager with a session.
        
        Args:
            session: aiohttp client session to use for requests
        """
        self.session = session
        await self.refresh_proxies()
        
    async def refresh_proxies(self) -> bool:
        """Fetch new proxies from the API.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.session:
            logger.error("Session not initialized for proxy manager")
            return False
            
        try:
            params = {
                'protocol': self.protocol,
                'count': self.batch_size
            }
            
            async with self.session.get(self.api_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch proxies: HTTP {response.status}")
                    return False
                    
                data = await response.json()
                
                if data.get('code') != 200 or 'data' not in data:
                    logger.error(f"Invalid response from proxy API: {data}")
                    return False
                    
                async with self.lock:
                    self.proxies = data['data']['proxies']
                    logger.info(f"Refreshed proxy pool with {len(self.proxies)} proxies")
                return True
                
        except Exception as e:
            logger.error(f"Error refreshing proxies: {str(e)}")
            return False
            
    async def get_proxy(self) -> Optional[str]:
        """Get a proxy from the pool.
        
        Returns:
            str: Proxy URL or None if no proxies available
        """
        async with self.lock:
            if not self.proxies:
                await self.refresh_proxies()
                if not self.proxies:
                    return None
                    
            # Get and remove a random proxy
            proxy = random.choice(self.proxies)
            self.proxies.remove(proxy)
            
            # Trigger refresh if running low
            if len(self.proxies) <= 1:
                asyncio.create_task(self.refresh_proxies())
                
            return f"{self.protocol}://{proxy}"

class TTSServer:
    """Server that's compatible with OpenAI's TTS API."""
    
    def __init__(self, host: str = "localhost", port: int = 7000, 
                 max_queue_size: int = 100, verify_ssl: bool = True,
                 use_proxy: bool = False):
        """Initialize the TTS server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            max_queue_size: Maximum number of tasks in queue
            verify_ssl: Whether to verify SSL certificates when connecting to external services
            use_proxy: Whether to use a proxy pool for requests
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.verify_ssl = verify_ssl
        self.use_proxy = use_proxy
        
        # Initialize queue system
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.current_task = None
        self.processing_lock = asyncio.Lock()
        
        # Initialize proxy manager if needed
        self.proxy_manager = ProxyManager() if use_proxy else None
        
        # OpenAI compatible endpoint
        self.app.router.add_post('/v1/audio/speech', self.handle_openai_speech)
        self.app.router.add_get('/api/queue-size', self.handle_queue_size)
        self.app.router.add_get('/{tail:.*}', self.handle_static)
        self.session = None
        
    async def start(self):
        """Start the TTS server."""
        # Configure SSL context
        if not self.verify_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            logger.warning("SSL certificate verification disabled. This is insecure and should only be used for testing.")
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(connector=connector)
            logger.info("Created aiohttp session with SSL verification disabled")
        else:
            self.session = aiohttp.ClientSession()
            logger.info("Created aiohttp session with default SSL settings")
            
        # Initialize proxy manager if enabled
        if self.use_proxy and self.proxy_manager:
            await self.proxy_manager.initialize(self.session)
            logger.info("Initialized proxy manager")
            
        # Start the task processor
        asyncio.create_task(self.process_queue())
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"TTS server running at http://{self.host}:{self.port}")
        if not self.verify_ssl:
            logger.warning("Running with SSL verification disabled. Not recommended for production use.")
        if self.use_proxy:
            logger.info("Running with proxy pool enabled for IP rotation")
        
    async def stop(self):
        """Stop the TTS server."""
        if self.session:
            await self.session.close()

    async def process_queue(self):
        """Background task to process the queue."""
        while True:
            try:
                # Get next task from queue
                task_data = await self.queue.get()
                
                async with self.processing_lock:
                    self.current_task = task_data
                    try:
                        # Process the task
                        response = await self.process_tts_request(task_data)
                        # Send response through the response future
                        task_data['response_future'].set_result(response)
                    except Exception as e:
                        task_data['response_future'].set_exception(e)
                    finally:
                        self.current_task = None
                        self.queue.task_done()
                        
            except Exception as e:
                logger.error(f"Error processing queue: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight loop on persistent errors

    async def process_tts_request(self, task_data: Dict[str, Any]) -> web.Response:
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
                if self.use_proxy and self.proxy_manager:
                    proxy = await self.proxy_manager.get_proxy()
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
                
                async with self.session.post(
                    "https://www.openai.fm/api/generate",
                    **request_kwargs
                ) as response:
                    if response.status == 403:
                        logger.warning("Received 403 Forbidden from OpenAI.fm")
                        if self.use_proxy and self.proxy_manager:
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
    
    async def handle_openai_speech(self, request: web.Request) -> web.Response:
        """Handle POST requests to /v1/audio/speech (OpenAI compatible API)."""
        try:
            # Check if queue is full
            if self.queue.full():
                return web.Response(
                    text=json.dumps({
                        "error": "Queue is full. Please try again later.",
                        "queue_size": self.queue.qsize()
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
            await self.queue.put(task_data)
            logger.info(f"Added task to queue. Current size: {self.queue.qsize()}")
            
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
            
    async def handle_queue_size(self, request: web.Request) -> web.Response:
        """Handle GET requests to /api/queue-size."""
        return web.json_response({
            "queue_size": self.queue.qsize(),
            "max_queue_size": self.queue.maxsize
        }, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })
            
    async def handle_static(self, request: web.Request) -> web.Response:
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
                
            # Construct full path
            full_path = Path(__file__).parent / file_path
            
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

async def run_server(host: str = "localhost", port: int = 7000, verify_ssl: bool = True, use_proxy: bool = False):
    """Run the TTS server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        verify_ssl: Whether to verify SSL certificates (disable only for testing)
        use_proxy: Whether to use a proxy pool for requests
    """
    server = TTSServer(host, port, verify_ssl=verify_ssl, use_proxy=use_proxy)
    await server.start()
    
    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop()
        logger.info("TTS server stopped")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the TTS API server")
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=7000, help="Port to bind to")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL certificate verification (insecure, use only for testing)")
    parser.add_argument("--use-proxy", action="store_true", help="Use proxy pool for IP rotation")
    parser.add_argument("--test-connection", action="store_true", help="Test connection to OpenAI.fm and exit")
    
    args = parser.parse_args()
    
    # If SSL verification is disabled, apply it globally
    if args.no_verify_ssl:
        import ssl
        
        # Disable SSL verification globally in Python
        ssl._create_default_https_context = ssl._create_unverified_context
        logger.warning("SSL certificate verification disabled GLOBALLY. This is insecure!")
        
        # Don't create connector here - it needs a running event loop
    
    # Test connection mode
    if args.test_connection:
        async def test_openai_fm():
            logger.info("Testing connection to OpenAI.fm...")
            
            if args.no_verify_ssl:
                connector = aiohttp.TCPConnector(ssl=False)
                session = aiohttp.ClientSession(connector=connector)
                logger.info("Using session with SSL verification disabled")
            else:
                session = aiohttp.ClientSession()
                logger.info("Using session with default SSL settings")
                
            try:
                logger.info("Sending GET request to OpenAI.fm homepage")
                async with session.get("https://www.openai.fm") as response:
                    logger.info(f"Homepage status: {response.status}")
                    if response.status == 200:
                        logger.info("Successfully connected to OpenAI.fm homepage")
                    else:
                        logger.error(f"Failed to connect to OpenAI.fm homepage: {response.status}")
                        
                logger.info("Testing API endpoint with minimal request")
                test_data = {"input": "Test", "voice": "alloy"}
                import urllib.parse
                url_encoded_data = urllib.parse.urlencode(test_data)
                
                async with session.post(
                    "https://www.openai.fm/api/generate",
                    data=url_encoded_data,
                    headers={
                        "Accept": "*/*",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Origin": "https://www.openai.fm",
                        "Referer": "https://www.openai.fm/",
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                ) as response:
                    logger.info(f"API endpoint status: {response.status}")
                    if response.status == 200:
                        data = await response.read()
                        logger.info(f"Successfully received {len(data)} bytes from API")
                    else:
                        text = await response.text()
                        logger.error(f"API request failed: {response.status}, {text}")
                        
            except Exception as e:
                logger.error(f"Connection test failed with error: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                await session.close()
                
        asyncio.run(test_openai_fm())
        logger.info("Connection test completed")
        exit(0)
    
    # Start the server
    asyncio.run(run_server(args.host, args.port, verify_ssl=not args.no_verify_ssl, use_proxy=args.use_proxy)) 