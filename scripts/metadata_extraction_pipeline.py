#!/usr/bin/env python3
"""
Metadata Extraction Pipeline for MCP-BD Explorer
Orchestrates the extraction of rich metadata from discovered domains
"""

import asyncio
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Set
import hashlib

import aiohttp
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MetadataRecord:
    """Represents extracted metadata for a single domain"""
    domain: str
    url: str
    status_code: int
    title: str
    meta_description: str
    h1_heading: str
    h2_headings: List[str]
    server_software: str
    content_type: str
    page_size: int
    load_time_ms: float
    technologies: List[str]
    cms: Optional[str]
    frameworks: List[str]
    programming_language: Optional[str]
    analytics_tools: List[str]
    country_code: str
    city: str
    isp: str
    hosting_provider: str
    seo_score: float
    canonical_url: str
    robots_txt_present: bool
    sitemap_url: Optional[str]
    backlink_count: int
    traffic_estimate: Optional[int]
    domain_authority: Optional[float]
    ssl_valid: bool
    ssl_issuer: str
    extracted_at: datetime
    extraction_success: bool
    confidence_score: float


class MetadataExtractionPipeline:
    """
    Main orchestrator for metadata extraction pipeline
    Coordinates HTTP spider, technology detection, and data storage
    """
    
    def __init__(self, db_connection, max_workers: int = 100):
        """
        Initialize the extraction pipeline
        
        Args:
            db_connection: PostgreSQL connection
            max_workers: Maximum concurrent workers
        """
        self.db = db_connection
        self.max_workers = max_workers
        self.session: Optional[aiohttp.ClientSession] = None
        self.extracted_domains: Set[str] = set()
        self.failed_domains: Dict[str, str] = {}
        
    async def initialize(self):
        """Initialize async session and resources"""
        self.session = aiohttp.ClientSession()
        logger.info("Metadata extraction pipeline initialized")
        
    async def shutdown(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        logger.info("Metadata extraction pipeline shutdown complete")
        
    async def extract_domain_metadata(self, domain: str) -> Optional[MetadataRecord]:
        """
        Extract metadata for a single domain
        
        Args:
            domain: Domain name to extract metadata from
            
        Returns:
            MetadataRecord with extracted data or None if failed
        """
        try:
            start_time = time.time()
            url = f"https://{domain}"
            
            # Step 1: HTTP request
            logger.debug(f"Fetching metadata for {domain}")
            response_data = await self._fetch_page(url)
            if not response_data:
                return None
                
            # Step 2: Parse HTML
            soup = BeautifulSoup(response_data['content'], 'html.parser')
            
            # Step 3: Extract basic metadata
            title = self._extract_title(soup)
            meta_description = self._extract_meta_description(soup)
            h1 = self._extract_h1(soup)
            h2_list = self._extract_h2_list(soup)
            
            # Step 4: Detect technologies
            technologies, cms, frameworks, language = self._detect_technologies(
                soup, response_data['headers']
            )
            
            # Step 5: Extract SEO data
            seo_data = self._analyze_seo(soup, response_data['headers'])
            
            # Step 6: Get hosting info
            hosting_info = self._get_hosting_info(domain, response_data['headers'])
            
            # Step 7: Estimate traffic
            traffic_data = self._estimate_traffic(domain)
            
            load_time = (time.time() - start_time) * 1000
            
            # Create metadata record
            record = MetadataRecord(
                domain=domain,
                url=url,
                status_code=response_data['status'],
                title=title,
                meta_description=meta_description,
                h1_heading=h1,
                h2_headings=h2_list,
                server_software=response_data['headers'].get('Server', 'Unknown'),
                content_type=response_data['headers'].get('Content-Type', 'Unknown'),
                page_size=len(response_data['content']),
                load_time_ms=load_time,
                technologies=technologies,
                cms=cms,
                frameworks=frameworks,
                programming_language=language,
                analytics_tools=self._detect_analytics(soup),
                country_code=hosting_info.get('country', 'Unknown'),
                city=hosting_info.get('city', 'Unknown'),
                isp=hosting_info.get('isp', 'Unknown'),
                hosting_provider=hosting_info.get('provider', 'Unknown'),
                seo_score=seo_data['score'],
                canonical_url=seo_data['canonical'],
                robots_txt_present=seo_data['has_robots'],
                sitemap_url=seo_data['sitemap'],
                backlink_count=traffic_data.get('backlinks', 0),
                traffic_estimate=traffic_data.get('traffic', None),
                domain_authority=traffic_data.get('authority', None),
                ssl_valid=response_data.get('ssl_valid', False),
                ssl_issuer=response_data.get('ssl_issuer', 'Unknown'),
                extracted_at=datetime.utcnow(),
                extraction_success=True,
                confidence_score=self._calculate_confidence_score(
                    response_data, seo_data, record
                )
            )
            
            logger.info(f"Successfully extracted metadata for {domain} in {load_time:.0f}ms")
            return record
            
        except Exception as e:
            logger.error(f"Error extracting metadata for {domain}: {str(e)}")
            self.failed_domains[domain] = str(e)
            return None
            
    async def _fetch_page(self, url: str, timeout: int = 30) -> Optional[Dict]:
        """Fetch page with error handling"""
        try:
            async with self.session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                ssl=True
            ) as response:
                content = await response.read()
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'content': content.decode('utf-8', errors='ignore'),
                    'ssl_valid': True,
                    'ssl_issuer': 'OK'
                }
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
            
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.text.strip() if title_tag else ''
        
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta = soup.find('meta', {'name': 'description'})
        return meta.get('content', '') if meta else ''
        
    def _extract_h1(self, soup: BeautifulSoup) -> str:
        """Extract first H1 heading"""
        h1 = soup.find('h1')
        return h1.text.strip() if h1 else ''
        
    def _extract_h2_list(self, soup: BeautifulSoup) -> List[str]:
        """Extract all H2 headings"""
        h2_tags = soup.find_all('h2', limit=5)
        return [h2.text.strip() for h2 in h2_tags]
        
    def _detect_technologies(self, soup: BeautifulSoup, headers: Dict) -> tuple:
        """Detect technologies, CMS, frameworks"""
        technologies = []
        cms = None
        frameworks = []
        language = None
        
        # Check headers
        server = headers.get('Server', '').lower()
        if 'nginx' in server:
            technologies.append('Nginx')
        if 'apache' in server:
            technologies.append('Apache')
        if 'php' in server:
            language = 'PHP'
            
        # Check meta tags
        generator = soup.find('meta', {'name': 'generator'})
        if generator:
            content = generator.get('content', '').lower()
            if 'wordpress' in content:
                cms = 'WordPress'
            if 'drupal' in content:
                cms = 'Drupal'
            if 'joomla' in content:
                cms = 'Joomla'
                
        # Check scripts for frameworks
        scripts = [s.get('src', '') for s in soup.find_all('script')]
        script_content = ' '.join(scripts).lower()
        
        if 'react' in script_content:
            frameworks.append('React')
        if 'vue' in script_content:
            frameworks.append('Vue.js')
        if 'angular' in script_content:
            frameworks.append('Angular')
        if 'jquery' in script_content:
            frameworks.append('jQuery')
            
        return technologies, cms, frameworks, language
        
    def _analyze_seo(self, soup: BeautifulSoup, headers: Dict) -> Dict:
        """Analyze SEO elements"""
        canonical = ''
        has_robots = False
        sitemap = None
        
        # Find canonical URL
        canonical_tag = soup.find('link', {'rel': 'canonical'})
        if canonical_tag:
            canonical = canonical_tag.get('href', '')
            
        # Check for robots.txt
        has_robots = 'X-Robots-Tag' in headers
        
        # Find sitemap
        sitemap_tag = soup.find('link', {'rel': 'sitemap'})
        if sitemap_tag:
            sitemap = sitemap_tag.get('href', '')
            
        # Calculate SEO score (0-100)
        score = 0
        if soup.find('title'):
            score += 15
        if soup.find('meta', {'name': 'description'}):
            score += 15
        if soup.find('h1'):
            score += 10
        if canonical:
            score += 10
        if has_robots:
            score += 5
        if sitemap:
            score += 10
        if soup.find('meta', {'name': 'viewport'}):
            score += 15
        if soup.find_all('meta', {'property': 'og:'}):
            score += 5
            
        return {
            'score': min(score, 100),
            'canonical': canonical,
            'has_robots': has_robots,
            'sitemap': sitemap
        }
        
    def _get_hosting_info(self, domain: str, headers: Dict) -> Dict:
        """Get hosting and IP information"""
        # This would integrate with GeoIP2 API in production
        return {
            'country': 'BD',
            'city': 'Dhaka',
            'isp': 'Unknown',
            'provider': 'Unknown'
        }
        
    def _estimate_traffic(self, domain: str) -> Dict:
        """Estimate traffic metrics"""
        # This would integrate with traffic APIs in production
        return {
            'traffic': None,
            'backlinks': 0,
            'authority': None
        }
        
    def _detect_analytics(self, soup: BeautifulSoup) -> List[str]:
        """Detect analytics tools"""
        analytics = []
        scripts_str = ' '.join([s.get('src', '') for s in soup.find_all('script')])
        
        if 'google-analytics' in scripts_str or 'ga(' in scripts_str:
            analytics.append('Google Analytics')
        if 'facebook' in scripts_str:
            analytics.append('Facebook Pixel')
        if 'mixpanel' in scripts_str:
            analytics.append('Mixpanel')
            
        return analytics
        
    def _calculate_confidence_score(self, response_data: Dict, seo_data: Dict, record: 'MetadataRecord') -> float:
        """Calculate overall confidence score (0.0-1.0)"""
        score = 0.0
        
        # Status code (25%)
        if response_data['status'] == 200:
            score += 0.25
            
        # SEO quality (25%)
        score += (seo_data['score'] / 100) * 0.25
        
        # Content presence (25%)
        has_title = bool(record.title)
        has_description = bool(record.meta_description)
        has_h1 = bool(record.h1_heading)
        content_score = (has_title + has_description + has_h1) / 3
        score += content_score * 0.25
        
        # Server info (25%)
        server_score = 0.25 if record.server_software != 'Unknown' else 0
        score += server_score
        
        return min(score, 1.0)
        
    async def process_batch(self, domains: List[str]) -> Dict[str, MetadataRecord]:
        """Process batch of domains concurrently"""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def bounded_extract(domain: str):
            async with semaphore:
                return await self.extract_domain_metadata(domain)
                
        tasks = [bounded_extract(domain) for domain in domains]
        results = await asyncio.gather(*tasks)
        
        metadata_dict = {}
        for domain, record in zip(domains, results):
            if record:
                metadata_dict[domain] = record
                self.extracted_domains.add(domain)
                
        return metadata_dict
        
    async def save_metadata(self, records: Dict[str, MetadataRecord]) -> int:
        """Save metadata records to database"""
        count = 0
        for domain, record in records.items():
            try:
                # Insert into database
                self.db.insert_metadata(asdict(record))
                count += 1
            except Exception as e:
                logger.error(f"Error saving metadata for {domain}: {str(e)}")
                
        logger.info(f"Saved {count} metadata records to database")
        return count


async def main():
    """Main execution"""
    logger.info("Starting metadata extraction pipeline")
    
    # Sample domains to process
    sample_domains = [
        'bd-online.com',
        'dhakahotel.com.bd',
        'bangladeshtravel.org',
    ]
    
    # Initialize pipeline (would use real DB connection)
    pipeline = MetadataExtractionPipeline(db_connection=None, max_workers=10)
    await pipeline.initialize()
    
    try:
        # Process batch
        metadata = await pipeline.process_batch(sample_domains)
        logger.info(f"Successfully extracted {len(metadata)} domains")
        
        for domain, record in metadata.items():
            logger.info(f"  {domain}: {record.title} ({record.seo_score:.0f}/100 SEO)")
            
    finally:
        await pipeline.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
