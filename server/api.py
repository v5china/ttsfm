"""
TTS API Server

This module provides a server that's compatible with OpenAI's TTS API format.
"""

import asyncio
import aiohttp
import logging
import ssl
from aiohttp import web
from typing import Optional

from server.handlers import handle_openai_speech, handle_queue_size, handle_static, process_tts_request
from proxy.manager import ProxyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TTSServer:
    """Server that's compatible with OpenAI's TTS API."""
    
    def __init__(self, host: str = "localhost", port: int = 7000, 
                 max_queue_size: int = 100, verify_ssl: bool = True,
                 use_proxy: bool = False, proxy_api: str = "https://proxy.scdn.io/api/get_proxy.php",
                 proxy_protocol: str = "http", proxy_batch_size: int = 5):
        """Initialize the TTS server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            max_queue_size: Maximum number of tasks in queue
            verify_ssl: Whether to verify SSL certificates when connecting to external services
            use_proxy: Whether to use a proxy pool for requests
            proxy_api: URL of the proxy pool API
            proxy_protocol: Proxy protocol to use (http, https, socks4, socks5, all)
            proxy_batch_size: Number of proxies to fetch at once
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
        self.proxy_manager = ProxyManager(
            api_url=proxy_api,
            protocol=proxy_protocol,
            batch_size=proxy_batch_size
        ) if use_proxy else None
        
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
            proxy_manager=self.proxy_manager, 
            session=self.session,
            use_proxy=self.use_proxy
        )
        
    async def _handle_queue_size(self, request):
        """Handler for queue size endpoint."""
        return await handle_queue_size(request, self.queue)
        
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
                        response = await process_tts_request(
                            task_data, 
                            self.session, 
                            proxy_manager=self.proxy_manager, 
                            use_proxy=self.use_proxy
                        )
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