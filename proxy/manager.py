"""
Proxy Manager Module

This module provides functionality for managing a pool of proxies for rotating IP addresses.
"""

import asyncio
import aiohttp
import logging
import random
from typing import Optional

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