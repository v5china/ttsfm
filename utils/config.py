"""
Configuration Utilities

This module provides utilities for loading and managing configuration settings.
"""

import os
import argparse
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from environment variables and command line arguments.
    
    Returns:
        argparse.Namespace: The configuration settings
    """
    # Load environment variables
    load_dotenv()
    
    # Get default values from environment variables
    default_host = os.getenv("HOST", "localhost")
    default_port = int(os.getenv("PORT", "7000"))
    default_verify_ssl = os.getenv("VERIFY_SSL", "true").lower() != "false"
    default_use_proxy = os.getenv("USE_PROXY", "true").lower() == "true"
    default_proxy_api = os.getenv("PROXY_API_URL", "https://proxy.scdn.io/api/get_proxy.php")
    default_proxy_protocol = os.getenv("PROXY_PROTOCOL", "http")
    default_proxy_batch_size = int(os.getenv("PROXY_BATCH_SIZE", "5"))
    default_max_queue_size = int(os.getenv("MAX_QUEUE_SIZE", "100"))
    
    parser = argparse.ArgumentParser(description="Run the TTS API server")
    parser.add_argument("--host", type=str, default=default_host, help="Host to bind to")
    parser.add_argument("--port", type=int, default=default_port, help="Port to bind to")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL certificate verification (insecure, use only for testing)")
    parser.add_argument("--use-proxy", action="store_true", default=default_use_proxy, help="Use proxy pool for IP rotation")
    parser.add_argument("--proxy-api", type=str, default=default_proxy_api, help="Proxy API URL")
    parser.add_argument("--proxy-protocol", type=str, default=default_proxy_protocol, help="Proxy protocol (http, https, socks4, socks5, all)")
    parser.add_argument("--proxy-batch-size", type=int, default=default_proxy_batch_size, help="Number of proxies to fetch at once")
    parser.add_argument("--max-queue-size", type=int, default=default_max_queue_size, help="Maximum number of tasks in queue")
    parser.add_argument("--test-connection", action="store_true", help="Test connection to OpenAI.fm and exit")
    
    args = parser.parse_args()
    
    # Apply global SSL settings if needed
    if args.no_verify_ssl or not default_verify_ssl:
        import ssl
        # Disable SSL verification globally in Python
        ssl._create_default_https_context = ssl._create_unverified_context
        logger.warning("SSL certificate verification disabled GLOBALLY. This is insecure!")
    
    return args

async def test_connection(session):
    """Test connection to OpenAI.fm.
    
    Args:
        session: aiohttp.ClientSession to use for requests
    """
    logger.info("Testing connection to OpenAI.fm...")
    
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