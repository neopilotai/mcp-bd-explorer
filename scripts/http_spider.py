#!/usr/bin/env python3
"""
HTTP/S Spider for MCP-BD Explorer
Specialized crawler for fetching and processing web content
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Tuple
import ssl
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
import certifi

logger = logging.getLogger(__name__)


class HTTPSpider:
    """
    Production-grade HTTP/S spider with:
    - Async concurrent crawling
    - User-agent rotation
    - Redirect following
    - Timeout handling
    - Resource limits
    - SSL certificate verification
    """
    
    COMMON_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
    ]
    
    def __init__(
        self,
        timeout: int = 30,
        max_redirects: int = 5,
        max_size: int = 10 * 1024 * 1024,  # 10MB
        verify_ssl: bool = True
    ):
        """
        Initialize HTTP spider
        
        Args:
            timeout: Request timeout in seconds
            max_redirects: Maximum redirects to follow
            max_size: Maximum response size in bytes
            verify_ssl: Verify SSL certificates
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.max_size = max_size
        self.verify_ssl = verify_ssl
        self.session: Optional[ClientSession] = None
        self.user_agent_index = 0
        
    async def initialize(self):
        """Initialize HTTP session"""
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        if not self.verify_ssl:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
        connector = TCPConnector(
            ssl=ssl_context,
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300
        )
        
        self.session = ClientSession(
            connector=connector,
            timeout=ClientTimeout(total=self.timeout)
        )
        logger.info("HTTP spider session initialized")
        
    async def shutdown(self):
        """Cleanup session"""
        if self.session:
            await self.session.close()
        logger.info("HTTP spider shutdown complete")
        
    def _get_user_agent(self) -> str:
        """Get rotating user agent"""
        agent = self.COMMON_USER_AGENTS[self.user_agent_index]
        self.user_agent_index = (self.user_agent_index + 1) % len(self.COMMON_USER_AGENTS)
        return agent
        
    async def head_request(self, url: str) -> Optional[Dict]:
        """
        Send HEAD request to validate domain
        
        Args:
            url: URL to request
            
        Returns:
            Dict with status, headers, or None if failed
        """
        try:
            headers = {'User-Agent': self._get_user_agent()}
            
            async with self.session.head(
                url,
                headers=headers,
                allow_redirects=True,
                ssl=self.verify_ssl
            ) as response:
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'url': str(response.url),
                    'success': True
                }
                
        except asyncio.TimeoutError:
            logger.warning(f"HEAD request timeout: {url}")
            return {'status': 0, 'success': False, 'error': 'timeout'}
        except Exception as e:
            logger.debug(f"HEAD request error for {url}: {str(e)}")
            return {'status': 0, 'success': False, 'error': str(e)}
            
    async def fetch(self, url: str, follow_redirects: bool = True) -> Optional[Dict]:
        """
        Fetch full page content
        
        Args:
            url: URL to fetch
            follow_redirects: Follow redirect chains
            
        Returns:
            Dict with status, headers, content, or None if failed
        """
        try:
            headers = {'User-Agent': self._get_user_agent()}
            
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
                
            start_time = time.time()
            
            async with self.session.get(
                url,
                headers=headers,
                allow_redirects=follow_redirects,
                ssl=self.verify_ssl
            ) as response:
                # Check content size
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > self.max_size:
                    logger.warning(f"Content too large for {url}: {content_length} bytes")
                    return None
                    
                content = await response.content.read(self.max_size)
                
                if len(content) >= self.max_size:
                    logger.warning(f"Content truncated for {url}")
                    
                elapsed = time.time() - start_time
                
                # Try to decode content
                try:
                    text = content.decode('utf-8')
                except UnicodeDecodeError:
                    # Try other encodings
                    for encoding in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
                        try:
                            text = content.decode(encoding)
                            break
                        except:
                            continue
                    else:
                        logger.warning(f"Could not decode content for {url}")
                        return None
                        
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'content': text,
                    'url': str(response.url),
                    'size': len(content),
                    'elapsed_ms': elapsed * 1000,
                    'success': response.status == 200
                }
                
        except asyncio.TimeoutError:
            logger.warning(f"Fetch timeout: {url}")
            return None
        except Exception as e:
            logger.debug(f"Fetch error for {url}: {str(e)}")
            return None
            
    async def fetch_with_retry(
        self,
        url: str,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ) -> Optional[Dict]:
        """
        Fetch with exponential backoff retry
        
        Args:
            url: URL to fetch
            max_retries: Maximum retry attempts
            backoff_factor: Exponential backoff factor
            
        Returns:
            Fetch result or None
        """
        for attempt in range(max_retries):
            try:
                result = await self.fetch(url)
                if result and result.get('success'):
                    return result
                    
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt * backoff_factor
                    logger.info(f"Retry {attempt + 1}/{max_retries} for {url} (wait {wait_time}s)")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
        
    async def batch_fetch(
        self,
        urls: list,
        max_concurrent: int = 10,
        with_retry: bool = True
    ) -> Dict[str, Optional[Dict]]:
        """
        Fetch multiple URLs concurrently
        
        Args:
            urls: List of URLs to fetch
            max_concurrent: Maximum concurrent requests
            with_retry: Use retry logic
            
        Returns:
            Dict mapping URL to fetch result
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_fetch(url: str):
            async with semaphore:
                if with_retry:
                    return await self.fetch_with_retry(url)
                else:
                    return await self.fetch(url)
                    
        tasks = [bounded_fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        return dict(zip(urls, results))
        
    async def validate_domain(self, domain: str) -> bool:
        """
        Quick validation of domain accessibility
        
        Args:
            domain: Domain to validate
            
        Returns:
            True if domain is accessible
        """
        if not domain.startswith(('http://', 'https://')):
            domain = f'https://{domain}'
            
        result = await self.head_request(domain)
        return result is not None and result.get('success', False)


class RobotsTxtParser:
    """Parse and respect robots.txt"""
    
    def __init__(self):
        self.cache = {}
        
    async def get_robots_txt(self, domain: str, spider: HTTPSpider) -> Optional[str]:
        """Fetch robots.txt for domain"""
        if domain in self.cache:
            return self.cache[domain]
            
        robots_url = f"https://{domain}/robots.txt"
        result = await spider.fetch(robots_url)
        
        if result:
            content = result.get('content', '')
            self.cache[domain] = content
            return content
            
        return None
        
    def is_crawlable(self, robots_content: str, path: str = '/', user_agent: str = '*') -> bool:
        """Check if path is crawlable"""
        if not robots_content:
            return True
            
        lines = robots_content.split('\n')
        disallow_rules = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(f'User-agent: {user_agent}'):
                # Parse following Disallow rules
                continue
            if line.startswith('Disallow:'):
                rule = line.split(':', 1)[1].strip()
                disallow_rules.append(rule)
                
        # Check if path matches any disallow rule
        for rule in disallow_rules:
            if path.startswith(rule):
                return False
                
        return True


async def main():
    """Test HTTP spider"""
    spider = HTTPSpider(timeout=10)
    await spider.initialize()
    
    try:
        # Test single URL
        result = await spider.fetch_with_retry('https://example.com')
        if result:
            print(f"Status: {result['status']}")
            print(f"Size: {result['size']} bytes")
            print(f"Elapsed: {result['elapsed_ms']:.0f}ms")
            
        # Test batch
        urls = ['https://example.com', 'https://google.com']
        results = await spider.batch_fetch(urls)
        print(f"\nBatch fetch completed: {len(results)} URLs")
        
    finally:
        await spider.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
