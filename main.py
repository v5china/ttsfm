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
import sys
from typing import Optional
from aiohttp import TCPConnector, ClientTimeout

from utils.config import load_config, test_connection
from server.api import TTSServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_test_session(verify_ssl: bool = True) -> Optional[aiohttp.ClientSession]:
    """Create a session for testing with optimized settings."""
    try:
        if not verify_ssl:
            connector = TCPConnector(
                ssl=False,
                limit=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
        else:
            connector = TCPConnector(
                limit=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            
        timeout = ClientTimeout(
            total=30,
            connect=10,
            sock_read=20
        )
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
    except Exception as e:
        logger.error(f"Failed to create test session: {str(e)}")
        return None

async def main():
    """Main function to start the server."""
    try:
        args = load_config()
        
        # Test connection mode
        if args.test_connection:
            session = await create_test_session(not args.no_verify_ssl)
            if not session:
                logger.error("Failed to create test session")
                sys.exit(1)
                
            try:
                await test_connection(session)
            except Exception as e:
                logger.error(f"Connection test failed: {str(e)}")
                sys.exit(1)
            finally:
                await session.close()
                
            logger.info("Connection test completed successfully")
            return
        
        # Start the server
        server = TTSServer(
            args.host, 
            args.port, 
            verify_ssl=not args.no_verify_ssl,
            max_queue_size=args.max_queue_size
        )
        
        await server.start()
        
        try:
            # Keep the server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            await server.stop()
            logger.info("TTS server stopped gracefully")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            await server.stop()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Process terminated due to error: {str(e)}")
        sys.exit(1) 