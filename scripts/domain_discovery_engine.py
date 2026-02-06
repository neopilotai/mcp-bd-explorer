#!/usr/bin/env python3
"""
Domain Discovery Engine for MCP-BD Explorer
Phase 2.2: Automated Crawling & Discovery

Aggregates domains from multiple sources:
- SSL Certificate Transparency logs
- DNS queries and reverse lookups
- Web Archive snapshots
- Subdomain enumeration
- Search engine results
- WHOIS bulk data

Author: MCP-BD Team
Date: 2026-02-06
Version: 2.2.0
"""

import asyncio
import json
import logging
import hashlib
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import psycopg2
from psycopg2.extras import execute_values
import requests
from concurrent.futures import ThreadPoolExecutor
import socket
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscoverySource(Enum):
    """Enumeration of discovery sources"""
    CT_LOGS = "ct_logs"
    DNS_DISCOVERY = "dns_discovery"
    WEB_ARCHIVE = "web_archive"
    SUBDOMAIN_ENUM = "subdomain_enum"
    SEARCH_ENGINE = "search_engine"
    WHOIS_BULK = "whois_bulk"


class ValidationStatus(Enum):
    """Domain validation status"""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    DUPLICATE = "duplicate"
    LOW_QUALITY = "low_quality"


class ConfidenceLevel(Enum):
    """Confidence levels for discovered domains"""
    VERY_HIGH = (0.95, 1.00)
    HIGH = (0.85, 0.95)
    MEDIUM = (0.70, 0.85)
    LOW = (0.50, 0.70)


@dataclass
class DiscoveredDomain:
    """Represents a discovered domain with metadata"""
    name: str
    source: DiscoverySource
    discovered_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0
    format_valid: bool = False
    dns_resolvable: bool = False
    http_reachable: bool = False
    tld_valid: bool = False
    category: Optional[str] = None
    status: ValidationStatus = ValidationStatus.PENDING
    metadata: Dict = field(default_factory=dict)
    validation_checks: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'source': self.source.value,
            'discovered_at': self.discovered_at.isoformat(),
            'confidence_score': self.confidence_score,
            'format_valid': self.format_valid,
            'dns_resolvable': self.dns_resolvable,
            'http_reachable': self.http_reachable,
            'tld_valid': self.tld_valid,
            'category': self.category,
            'status': self.status.value,
            'metadata': self.metadata,
            'validation_checks': self.validation_checks
        }

    def get_composite_score(self) -> float:
        """Calculate composite quality score"""
        weights = {
            'format_valid': 0.15,
            'dns_resolvable': 0.25,
            'http_reachable': 0.20,
            'tld_valid': 0.15,
            'metadata_complete': 0.15,
            'source_reliability': 0.10
        }

        score = 0.0
        score += weights['format_valid'] * (1.0 if self.format_valid else 0.0)
        score += weights['dns_resolvable'] * (1.0 if self.dns_resolvable else 0.0)
        score += weights['http_reachable'] * (1.0 if self.http_reachable else 0.0)
        score += weights['tld_valid'] * (1.0 if self.tld_valid else 0.0)
        score += weights['metadata_complete'] * (1.0 if self.metadata else 0.0)
        score += weights['source_reliability'] * self._get_source_reliability()

        return score

    def _get_source_reliability(self) -> float:
        """Get reliability score for source"""
        reliability_scores = {
            DiscoverySource.WHOIS_BULK: 0.99,
            DiscoverySource.CT_LOGS: 0.95,
            DiscoverySource.DNS_DISCOVERY: 0.92,
            DiscoverySource.SEARCH_ENGINE: 0.88,
            DiscoverySource.WEB_ARCHIVE: 0.75,
            DiscoverySource.SUBDOMAIN_ENUM: 0.70
        }
        return reliability_scores.get(self.source, 0.5)


@dataclass
class DiscoveryStats:
    """Statistics for discovery process"""
    total_discovered: int = 0
    total_valid: int = 0
    total_duplicates: int = 0
    total_invalid: int = 0
    avg_confidence_score: float = 0.0
    sources_stats: Dict[str, int] = field(default_factory=dict)
    processing_time_seconds: float = 0.0


class BaseCrawler(ABC):
    """Base class for all crawlers"""

    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize crawler
        
        Args:
            rate_limit: Delay between requests in seconds
        """
        self.rate_limit = rate_limit
        self.discovered_domains: List[DiscoveredDomain] = []
        self.session = requests.Session()

    @abstractmethod
    async def crawl(self) -> List[DiscoveredDomain]:
        """Execute crawl and return discovered domains"""
        pass

    def _validate_domain_format(self, domain: str) -> bool:
        """Validate domain format"""
        pattern = r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.bd$'
        return bool(re.match(pattern, domain.lower()))

    def _resolve_dns(self, domain: str) -> bool:
        """Check if domain resolves via DNS"""
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False
        except Exception as e:
            logger.debug(f"DNS resolution error for {domain}: {e}")
            return False

    def _check_http_reachable(self, domain: str, timeout: int = 5) -> bool:
        """Check if domain has HTTP/HTTPS endpoint"""
        try:
            for protocol in ['https', 'http']:
                try:
                    response = requests.head(
                        f"{protocol}://{domain}",
                        timeout=timeout,
                        allow_redirects=False
                    )
                    if response.status_code < 500:
                        return True
                except requests.exceptions.Timeout:
                    continue
                except requests.exceptions.ConnectionError:
                    continue
                except Exception:
                    continue
            return False
        except Exception as e:
            logger.debug(f"HTTP check error for {domain}: {e}")
            return False

    def _cleanup_domain_name(self, domain: str) -> str:
        """Clean and normalize domain name"""
        domain = domain.lower().strip()
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0]
        return domain

    async def _apply_rate_limit(self):
        """Apply rate limiting delay"""
        await asyncio.sleep(self.rate_limit)


class SSLCertificateCrawler(BaseCrawler):
    """
    Crawls SSL Certificate Transparency logs
    
    Sources:
    - Google CT Log API
    - DigiCert CT Log
    - Comodo CT Log
    - Sectigo CT Log
    """

    def __init__(self, rate_limit: float = 0.5):
        super().__init__(rate_limit)
        self.ct_log_apis = [
            "https://ct.googleapis.com/log/ct/v2/get-entries",
            "https://log.digicert.com/log/get-entries",
        ]

    async def crawl(self) -> List[DiscoveredDomain]:
        """Crawl SSL Certificate Transparency logs"""
        logger.info("Starting SSL Certificate Transparency crawl")
        domains = []

        for api_url in self.ct_log_apis:
            try:
                domains.extend(await self._query_ct_api(api_url))
                await self._apply_rate_limit()
            except Exception as e:
                logger.error(f"Error querying {api_url}: {e}")

        self.discovered_domains = domains
        return domains

    async def _query_ct_api(self, api_url: str) -> List[DiscoveredDomain]:
        """Query CT Log API for .bd domains"""
        domains = []
        batch_size = 500
        start = 0

        try:
            while True:
                params = {'start': start, 'end': start + batch_size}
                response = self.session.get(api_url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()
                entries = data.get('entries', [])

                if not entries:
                    break

                for entry in entries:
                    domains.extend(
                        await self._parse_certificate(entry)
                    )

                start += batch_size
                await self._apply_rate_limit()

        except Exception as e:
            logger.error(f"Error parsing CT API response: {e}")

        return domains

    async def _parse_certificate(self, entry: Dict) -> List[DiscoveredDomain]:
        """Extract domains from certificate entry"""
        domains = []

        try:
            # Parse certificate data (simplified)
            leaf_cert = entry.get('leaf_cert', {})
            subject = leaf_cert.get('subject', {})
            san = leaf_cert.get('subject_alt_name', [])

            # Extract domain names
            domain_names = set()

            if 'CN' in subject:
                domain_names.add(subject['CN'])

            domain_names.update(san)

            # Filter .bd domains
            for domain_name in domain_names:
                if domain_name.endswith('.bd'):
                    domain_obj = DiscoveredDomain(
                        name=self._cleanup_domain_name(domain_name),
                        source=DiscoverySource.CT_LOGS,
                        confidence_score=0.95,
                        metadata={'certificate_found': True}
                    )
                    domain_obj.format_valid = self._validate_domain_format(
                        domain_obj.name
                    )
                    domain_obj.tld_valid = True
                    domains.append(domain_obj)

        except Exception as e:
            logger.debug(f"Error parsing certificate: {e}")

        return domains


class DNSDiscoveryCrawler(BaseCrawler):
    """
    Crawls DNS records and performs reverse DNS lookups
    
    Methods:
    - Zone transfers (AXFR)
    - Reverse DNS lookups
    - NS record enumeration
    """

    def __init__(self, nameservers: List[str] = None, rate_limit: float = 1.0):
        super().__init__(rate_limit)
        self.nameservers = nameservers or ['8.8.8.8', '1.1.1.1', '1.0.0.1']

    async def crawl(self) -> List[DiscoveredDomain]:
        """Crawl DNS records"""
        logger.info("Starting DNS Discovery crawl")
        domains = []

        # DNS reverse lookup on common IP ranges
        domains.extend(await self._reverse_dns_lookup())

        self.discovered_domains = domains
        return domains

    async def _reverse_dns_lookup(self) -> List[DiscoveredDomain]:
        """Perform reverse DNS lookups on Bangladesh IP ranges"""
        domains = []
        # Bangladesh IP ranges (sample)
        ranges = [
            ('220.225.0.0', '220.240.0.0'),
        ]

        with ThreadPoolExecutor(max_workers=10) as executor:
            for range_start, range_end in ranges:
                # Convert IP to integer for iteration
                start_int = self._ip_to_int(range_start)
                end_int = self._ip_to_int(range_end)

                # Sample IPs from range (full scan would be too slow)
                ips_to_check = [
                    self._int_to_ip(
                        start_int + i * ((end_int - start_int) // 1000)
                    )
                    for i in range(1000)
                ]

                loop = asyncio.get_event_loop()
                for ip in ips_to_check:
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                        if hostname.endswith('.bd'):
                            domain_obj = DiscoveredDomain(
                                name=hostname,
                                source=DiscoverySource.DNS_DISCOVERY,
                                confidence_score=0.92,
                                dns_resolvable=True
                            )
                            domain_obj.format_valid = (
                                self._validate_domain_format(hostname)
                            )
                            domains.append(domain_obj)
                    except (socket.herror, socket.error):
                        pass
                    except Exception as e:
                        logger.debug(f"Reverse DNS error for {ip}: {e}")

                    await self._apply_rate_limit()

        return domains

    @staticmethod
    def _ip_to_int(ip: str) -> int:
        """Convert IP address to integer"""
        parts = ip.split('.')
        return sum(int(part) << (8 * (3 - i)) for i, part in enumerate(parts))

    @staticmethod
    def _int_to_ip(num: int) -> str:
        """Convert integer to IP address"""
        return '.'.join([str((num >> (8 * (3 - i))) & 0xff) for i in range(4)])


class WebArchiveCrawler(BaseCrawler):
    """
    Crawls web archive snapshots from Archive.org
    
    Retrieves historical snapshots of .bd websites
    """

    def __init__(self, rate_limit: float = 1.0):
        super().__init__(rate_limit)
        self.archive_api = "https://archive.org/advancedsearch.php"

    async def crawl(self) -> List[DiscoveredDomain]:
        """Crawl web archive for .bd domains"""
        logger.info("Starting Web Archive crawl")
        domains = []

        try:
            domains = await self._query_archive_org()
        except Exception as e:
            logger.error(f"Error querying archive.org: {e}")

        self.discovered_domains = domains
        return domains

    async def _query_archive_org(self) -> List[DiscoveredDomain]:
        """Query Archive.org API for .bd domain snapshots"""
        domains = []
        params = {
            'q': 'domain:*.bd',
            'output': 'json',
            'fl': 'identifier,timestamp',
            'rows': 10000,
            'page': 1
        }

        try:
            response = self.session.get(
                self.archive_api,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            docs = data.get('response', {}).get('docs', [])

            for doc in docs:
                identifier = doc.get('identifier', '')
                if identifier.endswith('.bd'):
                    domain_obj = DiscoveredDomain(
                        name=self._cleanup_domain_name(identifier),
                        source=DiscoverySource.WEB_ARCHIVE,
                        confidence_score=0.75,
                        metadata={
                            'archive_snapshots': doc.get('timestamp', [])
                        }
                    )
                    domain_obj.format_valid = (
                        self._validate_domain_format(domain_obj.name)
                    )
                    domains.append(domain_obj)

        except Exception as e:
            logger.error(f"Error querying archive.org: {e}")

        return domains


class SearchEngineCrawler(BaseCrawler):
    """
    Crawls search engine results for .bd domains
    
    Uses Google/Bing search APIs
    """

    def __init__(self, api_key: str = None, rate_limit: float = 1.0):
        super().__init__(rate_limit)
        self.api_key = api_key

    async def crawl(self) -> List[DiscoveredDomain]:
        """Crawl search engines for .bd domains"""
        logger.info("Starting Search Engine crawl")
        domains = []

        if not self.api_key:
            logger.warning("No API key provided for search engine crawling")
            return domains

        queries = [
            "site:.bd government",
            "site:.bd education",
            "site:.bd business",
            "site:.bd commerce",
            "site:.bd technology"
        ]

        for query in queries:
            try:
                domains.extend(await self._search_query(query))
                await self._apply_rate_limit()
            except Exception as e:
                logger.error(f"Error searching for '{query}': {e}")

        self.discovered_domains = domains
        return domains

    async def _search_query(self, query: str) -> List[DiscoveredDomain]:
        """Execute search query and extract domains"""
        domains = []
        # This would use actual search API
        # Simplified for demonstration
        logger.info(f"Executing search query: {query}")
        return domains


class DomainDiscoveryEngine:
    """
    Main domain discovery engine
    
    Coordinates multiple crawlers:
    - SSL Certificate crawling
    - DNS discovery
    - Web Archive crawling
    - Subdomain enumeration
    - Search engine crawling
    - WHOIS bulk import
    """

    def __init__(
        self,
        db_connection_string: str,
        min_quality_score: float = 0.70
    ):
        """
        Initialize discovery engine
        
        Args:
            db_connection_string: PostgreSQL connection string
            min_quality_score: Minimum quality score for inclusion
        """
        self.db_connection_string = db_connection_string
        self.min_quality_score = min_quality_score
        self.discovered_domains: Set[str] = set()
        self.domain_objects: Dict[str, DiscoveredDomain] = {}
        self.stats = DiscoveryStats()

    async def run_discovery(self) -> DiscoveryStats:
        """Run complete discovery pipeline"""
        start_time = datetime.now()

        logger.info("=" * 60)
        logger.info("Starting MCP-BD Domain Discovery Engine")
        logger.info("=" * 60)

        # Run all crawlers in parallel
        crawlers = [
            SSLCertificateCrawler(),
            DNSDiscoveryCrawler(),
            WebArchiveCrawler(),
        ]

        tasks = [crawler.crawl() for crawler in crawlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for crawler, result in zip(crawlers, results):
            if isinstance(result, Exception):
                logger.error(f"Crawler {crawler.__class__.__name__} failed: {result}")
                continue

            for domain in result:
                self._process_discovered_domain(domain)

        # Deduplication
        self._deduplicate_domains()

        # Quality scoring
        self._score_domains()

        # Database storage
        await self._store_domains()

        # Calculate statistics
        end_time = datetime.now()
        self.stats.processing_time_seconds = (
            end_time - start_time
        ).total_seconds()

        logger.info("=" * 60)
        logger.info("Discovery Pipeline Complete")
        logger.info(f"Total discovered: {self.stats.total_discovered}")
        logger.info(f"Total valid: {self.stats.total_valid}")
        logger.info(f"Total duplicates: {self.stats.total_duplicates}")
        logger.info(
            f"Processing time: {self.stats.processing_time_seconds:.1f}s"
        )
        logger.info("=" * 60)

        return self.stats

    def _process_discovered_domain(self, domain: DiscoveredDomain):
        """Process and validate discovered domain"""
        domain_key = domain.name.lower()

        # Check for duplicates
        if domain_key in self.domain_objects:
            self.stats.total_duplicates += 1
            existing = self.domain_objects[domain_key]
            existing.metadata['sources'] = existing.metadata.get(
                'sources', []
            )
            existing.metadata['sources'].append(domain.source.value)
            return

        # Perform validation checks
        domain.format_valid = self._validate_domain_format(domain.name)
        domain.dns_resolvable = self._resolve_dns(domain.name)
        domain.http_reachable = self._check_http_reachable(domain.name)
        domain.tld_valid = domain.name.endswith('.bd')

        # Determine status
        if not domain.format_valid or not domain.tld_valid:
            domain.status = ValidationStatus.INVALID
        else:
            domain.status = ValidationStatus.VALID

        self.discovered_domains.add(domain_key)
        self.domain_objects[domain_key] = domain
        self.stats.total_discovered += 1

    def _deduplicate_domains(self):
        """Remove duplicate domains"""
        logger.info(f"Deduplicating {len(self.domain_objects)} domains")
        
        seen_hashes = set()
        unique_domains = {}

        for domain_key, domain_obj in self.domain_objects.items():
            # Create hash for fuzzy matching
            domain_hash = self._create_domain_hash(domain_key)

            if domain_hash not in seen_hashes:
                seen_hashes.add(domain_hash)
                unique_domains[domain_key] = domain_obj
            else:
                self.stats.total_duplicates += 1

        self.domain_objects = unique_domains
        logger.info(
            f"After deduplication: {len(self.domain_objects)} unique domains"
        )

    def _score_domains(self):
        """Calculate quality scores for all domains"""
        logger.info("Calculating quality scores")

        total_score = 0.0
        valid_count = 0

        for domain in self.domain_objects.values():
            composite_score = domain.get_composite_score()
            domain.confidence_score = composite_score

            if composite_score >= self.min_quality_score:
                domain.status = ValidationStatus.VALID
                valid_count += 1
                total_score += composite_score
            else:
                domain.status = ValidationStatus.LOW_QUALITY

        if valid_count > 0:
            self.stats.avg_confidence_score = total_score / valid_count
            self.stats.total_valid = valid_count
        else:
            self.stats.total_valid = 0

    async def _store_domains(self):
        """Store discovered domains in database"""
        logger.info("Storing domains in database")

        try:
            conn = psycopg2.connect(self.db_connection_string)
            cur = conn.cursor()

            # Prepare batch insert
            values = []
            for domain in self.domain_objects.values():
                if domain.status == ValidationStatus.VALID:
                    values.append((
                        domain.name,
                        domain.source.value,
                        domain.confidence_score,
                        domain.status.value,
                        json.dumps(domain.metadata),
                        json.dumps(domain.validation_checks)
                    ))

            if values:
                # Insert domains
                execute_values(
                    cur,
                    """
                    INSERT INTO domain_discovery_log 
                    (domain_name, source_id, confidence_score, validation_status, 
                     metadata, validation_checks)
                    VALUES %s
                    ON CONFLICT (domain_name) DO UPDATE
                    SET confidence_score = EXCLUDED.confidence_score
                    """,
                    values
                )

                conn.commit()
                logger.info(f"Stored {len(values)} domains")

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Database error: {e}")

    @staticmethod
    def _validate_domain_format(domain: str) -> bool:
        """Validate domain format"""
        pattern = r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.bd$'
        return bool(re.match(pattern, domain.lower()))

    @staticmethod
    def _resolve_dns(domain: str) -> bool:
        """Check DNS resolution"""
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False

    @staticmethod
    def _check_http_reachable(domain: str) -> bool:
        """Check HTTP reachability"""
        try:
            for protocol in ['https', 'http']:
                try:
                    response = requests.head(
                        f"{protocol}://{domain}",
                        timeout=5,
                        allow_redirects=False
                    )
                    if response.status_code < 500:
                        return True
                except Exception:
                    pass
            return False
        except Exception:
            return False

    @staticmethod
    def _create_domain_hash(domain: str) -> str:
        """Create hash for deduplication"""
        return hashlib.md5(domain.lower().encode()).hexdigest()


async def main():
    """Main entry point"""
    import os

    db_connection = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost/mcp_bd_explorer'
    )

    engine = DomainDiscoveryEngine(
        db_connection_string=db_connection,
        min_quality_score=0.70
    )

    stats = await engine.run_discovery()

    # Print final statistics
    print("\n" + "=" * 60)
    print("DISCOVERY STATISTICS")
    print("=" * 60)
    print(f"Total Discovered: {stats.total_discovered}")
    print(f"Total Valid: {stats.total_valid}")
    print(f"Total Duplicates: {stats.total_duplicates}")
    print(f"Total Invalid: {stats.total_invalid}")
    print(f"Average Confidence: {stats.avg_confidence_score:.2%}")
    print(f"Processing Time: {stats.processing_time_seconds:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
