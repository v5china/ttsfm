"""
OpenAI TTS API Server

This module provides a server that's compatible with OpenAI's TTS API format.
This is the main entry point for the application.
"""

import asyncio
import aiohttp
import logging
import ssl
import time

from utils.config import load_config, test_connection
from server.api import TTSServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to start the server."""
    args = load_config()
    
    # Test connection mode
    if args.test_connection:
        if args.no_verify_ssl:
            connector = aiohttp.TCPConnector(ssl=False)
            session = aiohttp.ClientSession(connector=connector)
        else:
            session = aiohttp.ClientSession()
            
        try:
            await test_connection(session)
        finally:
            await session.close()
            
        logger.info("Connection test completed")
        return
    
    # Start the server
    server = TTSServer(
        args.host, 
        args.port, 
        verify_ssl=not args.no_verify_ssl, 
        use_proxy=args.use_proxy,
        proxy_api=args.proxy_api,
        proxy_protocol=args.proxy_protocol,
        proxy_batch_size=args.proxy_batch_size,
        max_queue_size=args.max_queue_size
    )
    
    await server.start()
    
    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop()
        logger.info("TTS server stopped")

if __name__ == "__main__":
    asyncio.run(main()) 