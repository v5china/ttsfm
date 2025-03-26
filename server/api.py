"""
TTS API Server

This module provides a server that's compatible with OpenAI's TTS API format.
"""

import asyncio
import aiohttp
import logging
import ssl
from aiohttp import web, TCPConnector
from typing import Optional
import random
from utils.config import load_config

from server.handlers import handle_openai_speech, handle_queue_size, handle_static, process_tts_request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

class TTSServer:
    """Server that's compatible with OpenAI's TTS API."""
    
    def __init__(self, host: str = config['host'], port: int = config['port'], 
                 max_queue_size: int = config['max_queue_size'], verify_ssl: bool = config['verify_ssl']):
        """Initialize the TTS server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            max_queue_size: Maximum number of tasks in queue
            verify_ssl: Whether to verify SSL certificates when connecting to external services
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.verify_ssl = verify_ssl
        
        # Initialize queue system with rate limiting
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.current_task = None
        self.processing_lock = asyncio.Lock()
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum time between requests in seconds
        
        # Set up routes
        self.setup_routes()
        
        self.session = None
        
    def setup_routes(self):
        """Set up the API routes."""
        # OpenAI compatible endpoint
        self.app.router.add_post('/v1/audio/speech', self._handle_openai_speech)
        self.app.router.add_get('/api/queue-size', self._handle_queue_size)
        self.app.router.add_get('/{tail:.*}', handle_static)
    
    async def _handle_openai_speech(self, request):
        """Handler for OpenAI speech endpoint."""
        return await handle_openai_speech(
            request, 
            self.queue, 
            session=self.session
        )
        
    async def _handle_queue_size(self, request):
        """Handler for queue size endpoint."""
        return await handle_queue_size(request, self.queue)
        
    async def start(self):
        """Start the TTS server."""
        # Configure SSL context and connector with better settings
        if not self.verify_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            logger.warning("SSL certificate verification disabled. This is insecure and should only be used for testing.")
            connector = TCPConnector(
                ssl=False,
                limit=10,  # Limit concurrent connections
                ttl_dns_cache=300,  # Cache DNS results for 5 minutes
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
        else:
            connector = TCPConnector(
                limit=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            
        # Create session with better timeout settings
        timeout = aiohttp.ClientTimeout(
            total=30,
            connect=10,
            sock_read=20
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://www.openai.fm",
                "Referer": "https://www.openai.fm/",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        logger.info("Created aiohttp session with optimized settings")
            
        # Start the task processor
        asyncio.create_task(self.process_queue())
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"TTS server running at http://{self.host}:{self.port}")
        if not self.verify_ssl:
            logger.warning("Running with SSL verification disabled. Not recommended for production use.")
        
    async def stop(self):
        """Stop the TTS server."""
        if self.session:
            await self.session.close()

    async def process_queue(self):
        """Background task to process the queue with rate limiting."""
        while True:
            try:
                # Get next task from queue
                task_data = await self.queue.get()
                
                # Implement rate limiting
                current_time = asyncio.get_event_loop().time()
                time_since_last_request = current_time - self.last_request_time
                if time_since_last_request < self.min_request_interval:
                    await asyncio.sleep(self.min_request_interval - time_since_last_request)
                
                async with self.processing_lock:
                    self.current_task = task_data
                    try:
                        # Process the task
                        response = await process_tts_request(
                            task_data, 
                            self.session
                        )
                        # Send response through the response future
                        task_data['response_future'].set_result(response)
                        self.last_request_time = asyncio.get_event_loop().time()
                    except Exception as e:
                        task_data['response_future'].set_exception(e)
                    finally:
                        self.current_task = None
                        self.queue.task_done()
                        
            except Exception as e:
                logger.error(f"Error processing queue: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight loop on persistent errors 