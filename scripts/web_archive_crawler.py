#!/usr/bin/env python3
"""
Web Archive Crawler
Phase 2.2: Automated Crawling & Discovery

Discovers historical .bd domains from Archive.org
(Wayback Machine) snapshots.

Author: MCP-BD Team
Date: 2026-02-06
Version: 1.0
"""

import logging
import requests
import json
import re
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

logger = logging.getLogger(__name__)


@dataclass
class ArchiveSnapshot:
    """Represents a Wayback Machine snapshot"""
    url: str
    timestamp: str
    status_code: Optional[int] = None
    size: Optional[int] = None


class WebArchiveCrawler:
    """
    Crawls Archive.org for .bd domain snapshots
    
    Retrieves historical website data to discover
    domains that may no longer be active but were
    historically important.
    """

    def __init__(self, max_workers: int = 5):
        self.archive_api_base = "https://archive.org/advancedsearch.php"
        self.archive_cdx_api = "https://cdx.archive.org/search/cdx"
        self.wayback_base = "https://web.archive.org/web"
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MCP-BD-Explorer/2.2 (+http://neopilot.ai)'
        })
        self.discovered_domains: Set[str] = set()
        self.snapshots: List[ArchiveSnapshot] = []

    def crawl_archive_org(self, max_results: int = 10000) -> Dict:
        """Crawl Archive.org for .bd domains"""
        logger.info("Starting Web Archive crawl for .bd domains")

        stats = {
            'queries_executed': 0,
            'total_snapshots_found': 0,
            'unique_domains_discovered': 0,
            'domains': []
        }

        # Query Archive.org
        domains = self._query_archive_org(max_results)
        stats['unique_domains_discovered'] = len(domains)
        stats['domains'] = sorted(list(domains))

        self.discovered_domains.update(domains)

        logger.info(
            f"Found {len(domains)} unique .bd domains in Archive.org"
        )

        return stats

    def _query_archive_org(self, max_results: int = 10000) -> Set[str]:
        """Query Archive.org API for .bd domains"""
        domains = set()

        try:
            params = {
                'q': 'domain:*.bd',
                'output': 'json',
                'fl': 'identifier,timestamp',
                'rows': min(max_results, 100000),
                'page': 1
            }

            logger.info("Querying Archive.org for .bd snapshots")

            response = self.session.get(
                self.archive_api_base,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            docs = data.get('response', {}).get('docs', [])

            logger.info(f"Found {len(docs)} snapshots in Archive.org")

            for doc in docs:
                identifier = doc.get('identifier', '').lower()

                # Extract domain from identifier
                if identifier.endswith('.bd'):
                    # Remove URL parts
                    domain = self._extract_domain(identifier)
                    if domain and domain.endswith('.bd'):
                        domains.add(domain)

        except requests.exceptions.Timeout:
            logger.error("Archive.org API timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Archive.org API error: {e}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from Archive.org")
        except Exception as e:
            logger.error(f"Unexpected error querying Archive.org: {e}")

        return domains

    def get_snapshots_for_domain(
        self,
        domain: str,
        max_snapshots: int = 100
    ) -> List[ArchiveSnapshot]:
        """Get all snapshots for a domain from CDX API"""
        snapshots = []

        try:
            params = {
                'url': f"*.{domain}/*",
                'output': 'json',
                'matchType': 'domain',
                'collapse': 'urlkey',
                'filter': ['statuscode:200', 'mimetype:text/html'],
                'rows': max_snapshots,
                'showDuplicates': 'false'
            }

            response = self.session.get(
                self.archive_cdx_api,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if len(data) > 1:
                # First row is headers
                headers = data[0]
                for row in data[1:]:
                    try:
                        url = row[headers.index('original')]
                        timestamp = row[headers.index('timestamp')]
                        status = int(row[headers.index('statuscode')])

                        snapshot = ArchiveSnapshot(
                            url=url,
                            timestamp=timestamp,
                            status_code=status
                        )
                        snapshots.append(snapshot)

                    except (ValueError, IndexError):
                        continue

        except Exception as e:
            logger.debug(f"Error getting snapshots for {domain}: {e}")

        return snapshots

    def crawl_domain_history(
        self,
        domain: str,
        fetch_content: bool = False
    ) -> Dict:
        """Crawl complete history of domain from Archive.org"""
        logger.info(f"Crawling history for {domain}")

        snapshots = self.get_snapshots_for_domain(domain)

        stats = {
            'domain': domain,
            'total_snapshots': len(snapshots),
            'date_range': {
                'earliest': None,
                'latest': None
            },
            'snapshots': []
        }

        if snapshots:
            # Sort by timestamp
            snapshots.sort(key=lambda x: x.timestamp)

            stats['date_range']['earliest'] = snapshots[0].timestamp
            stats['date_range']['latest'] = snapshots[-1].timestamp

            # Sample snapshots if too many
            if len(snapshots) > 50:
                sampled = [
                    snapshots[int(i * len(snapshots) / 50)]
                    for i in range(50)
                ]
            else:
                sampled = snapshots

            for snapshot in sampled:
                snapshot_info = {
                    'url': snapshot.url,
                    'timestamp': snapshot.timestamp,
                    'status_code': snapshot.status_code
                }

                if fetch_content:
                    content = self._fetch_snapshot_content(
                        domain,
                        snapshot.timestamp
                    )
                    snapshot_info['content_size'] = len(content)
                    snapshot_info['content_preview'] = content[:500]

                stats['snapshots'].append(snapshot_info)

        return stats

    def _fetch_snapshot_content(
        self,
        domain: str,
        timestamp: str
    ) -> str:
        """Fetch content from Wayback Machine snapshot"""
        try:
            url = f"{self.wayback_base}/{timestamp}/{domain}"
            response = self.session.get(url, timeout=10)
            return response.text
        except Exception as e:
            logger.debug(f"Error fetching snapshot: {e}")
            return ""

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            # Remove protocol
            url = re.sub(r'^https?://', '', url)
            # Remove www
            url = re.sub(r'^www\.', '', url)
            # Get domain part
            domain = url.split('/')[0].split('?')[0]
            return domain.lower()
        except Exception:
            return ""

    def analyze_domain_trends(self) -> Dict:
        """Analyze trends in discovered domains"""
        if not self.snapshots:
            return {}

        # Group by time period
        decades = {}

        for snapshot in self.snapshots:
            try:
                year = snapshot.timestamp[:4]
                decade = f"{year[0:3]}0s"

                if decade not in decades:
                    decades[decade] = 0

                decades[decade] += 1

            except Exception:
                continue

        return {
            'total_snapshots': len(self.snapshots),
            'timeline': decades,
            'earliest_snapshot': min(
                self.snapshots,
                key=lambda x: x.timestamp
            ).timestamp if self.snapshots else None,
            'latest_snapshot': max(
                self.snapshots,
                key=lambda x: x.timestamp
            ).timestamp if self.snapshots else None
        }


async def main():
    """Main entry point"""
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    crawler = WebArchiveCrawler()

    # Crawl for .bd domains
    stats = crawler.crawl_archive_org(max_results=5000)

    print("\n" + "=" * 60)
    print("ARCHIVE.ORG CRAWL STATISTICS")
    print("=" * 60)
    print(f"Unique domains discovered: {stats['unique_domains_discovered']}")

    if stats['domains']:
        print("\nSample discovered domains:")
        for domain in stats['domains'][:20]:
            print(f"  - {domain}")

        if len(stats['domains']) > 20:
            print(f"  ... and {len(stats['domains']) - 20} more")

    print("=" * 60)

    # Detailed history for sample domain
    if stats['domains']:
        sample_domain = stats['domains'][0]
        print(f"\nDetailed history for {sample_domain}:")

        history = crawler.crawl_domain_history(sample_domain)
        print(f"  Total snapshots: {history['total_snapshots']}")
        if history.get('date_range', {}).get('earliest'):
            print(f"  Earliest: {history['date_range']['earliest']}")
            print(f"  Latest: {history['date_range']['latest']}")
        print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
