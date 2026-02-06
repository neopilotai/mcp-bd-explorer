#!/usr/bin/env python3
"""
SSL Certificate Transparency Crawler
Phase 2.2: Automated Crawling & Discovery

Extracts domain names from SSL/TLS certificates
issued for .bd domains by querying Certificate
Transparency logs.

Author: MCP-BD Team
Date: 2026-02-06
Version: 1.0
"""

import logging
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import requests
from datetime import datetime, timedelta
import base64
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class Certificate:
    """Represents an SSL certificate"""
    common_name: Optional[str] = None
    subject_alt_names: List[str] = None
    issuer: Optional[str] = None
    serial_number: Optional[str] = None
    not_before: Optional[datetime] = None
    not_after: Optional[datetime] = None
    raw_data: Optional[bytes] = None


class CTLogProvider:
    """Base class for CT Log providers"""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MCP-BD-Explorer/2.2'
        })

    def get_log_info(self) -> Dict:
        """Get CT log metadata"""
        try:
            response = self.session.get(
                f"{self.base_url}/ct/v1/get-sth",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting log info for {self.name}: {e}")
            return {}

    def get_entries(
        self,
        start: int = 0,
        end: int = 100
    ) -> List[Dict]:
        """Get certificate entries from CT log"""
        try:
            response = self.session.get(
                f"{self.base_url}/ct/v1/get-entries",
                params={'start': start, 'end': end},
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('entries', [])
        except Exception as e:
            logger.error(
                f"Error getting entries from {self.name}: {e}"
            )
            return []

    def parse_certificate(
        self,
        leaf_input: str
    ) -> Optional[Certificate]:
        """Parse certificate from leaf input"""
        try:
            # Decode leaf input
            cert_data = base64.b64decode(leaf_input)

            # Parse certificate using cryptography
            cert = x509.load_der_x509_certificate(
                cert_data,
                default_backend()
            )

            # Extract common name
            cn = None
            try:
                cn_attr = cert.subject.get_attributes_for_oid(
                    x509.oid.NameOID.COMMON_NAME
                )
                if cn_attr:
                    cn = cn_attr[0].value
            except Exception:
                pass

            # Extract SANs
            sans = []
            try:
                san_ext = cert.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                )
                for name in san_ext.value:
                    if isinstance(name, x509.DNSName):
                        sans.append(name.value)
            except Exception:
                pass

            # Extract issuer
            issuer = None
            try:
                issuer = str(cert.issuer)
            except Exception:
                pass

            return Certificate(
                common_name=cn,
                subject_alt_names=sans,
                issuer=issuer,
                serial_number=str(cert.serial_number),
                not_before=cert.not_valid_before,
                not_after=cert.not_valid_after,
                raw_data=cert_data
            )

        except Exception as e:
            logger.debug(f"Error parsing certificate: {e}")
            return None


class SSLCertificateTransparencyCrawler:
    """
    Crawls SSL Certificate Transparency logs
    
    Supported providers:
    - Google CT Log
    - DigiCert CT Log
    - Sectigo (formerly Comodo) CT Log
    """

    def __init__(self, max_workers: int = 5):
        self.ct_providers = [
            CTLogProvider(
                'Google',
                'https://ct.googleapis.com/log'
            ),
            CTLogProvider(
                'DigiCert',
                'https://log.digicert.com/log'
            ),
            CTLogProvider(
                'Sectigo',
                'https://sabre.sectigo.com'
            ),
        ]
        self.max_workers = max_workers
        self.discovered_domains = set()
        self.certificates = []

    def crawl_all_providers(self, max_entries: int = 10000) -> Dict:
        """Crawl all CT log providers"""
        logger.info("Starting CT log crawl for all providers")

        stats = {
            'total_entries_processed': 0,
            'total_domains_discovered': 0,
            'bd_domains': [],
            'providers': {}
        }

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.crawl_provider,
                    provider,
                    max_entries
                ): provider.name
                for provider in self.ct_providers
            }

            for future in as_completed(futures):
                provider_name = futures[future]
                try:
                    result = future.result()
                    stats['providers'][provider_name] = result
                    stats['total_entries_processed'] += result.get(
                        'entries_processed',
                        0
                    )
                    stats['total_domains_discovered'] += result.get(
                        'domains_discovered',
                        0
                    )
                except Exception as e:
                    logger.error(
                        f"Error crawling {provider_name}: {e}"
                    )
                    stats['providers'][provider_name] = {
                        'error': str(e)
                    }

        stats['bd_domains'] = list(self.discovered_domains)
        return stats

    def crawl_provider(
        self,
        provider: CTLogProvider,
        max_entries: int = 10000
    ) -> Dict:
        """Crawl specific CT log provider"""
        logger.info(f"Crawling {provider.name} CT log")

        entries_processed = 0
        domains_discovered = 0
        batch_size = 100

        try:
            for start in range(0, max_entries, batch_size):
                entries = provider.get_entries(
                    start=start,
                    end=start + batch_size
                )

                if not entries:
                    break

                for entry in entries:
                    domains_found = self._process_entry(
                        entry,
                        provider
                    )
                    domains_discovered += domains_found
                    entries_processed += 1

                logger.info(
                    f"{provider.name}: Processed {entries_processed} "
                    f"entries, found {domains_discovered} .bd domains"
                )

        except Exception as e:
            logger.error(f"Error crawling {provider.name}: {e}")

        return {
            'entries_processed': entries_processed,
            'domains_discovered': domains_discovered,
            'bd_domains': list(self.discovered_domains)
        }

    def _process_entry(
        self,
        entry: Dict,
        provider: CTLogProvider
    ) -> int:
        """Process single CT log entry"""
        domains_count = 0

        try:
            # Extract leaf certificate
            leaf_input = entry.get('leaf_input')
            if not leaf_input:
                return 0

            # Parse certificate
            cert = provider.parse_certificate(leaf_input)
            if not cert:
                return 0

            self.certificates.append(cert)

            # Extract domains
            domains = set()

            if cert.common_name:
                domains.add(cert.common_name.lower())

            if cert.subject_alt_names:
                domains.update(
                    [d.lower() for d in cert.subject_alt_names]
                )

            # Filter .bd domains
            for domain in domains:
                if domain.endswith('.bd'):
                    self.discovered_domains.add(domain)
                    domains_count += 1

        except Exception as e:
            logger.debug(f"Error processing entry: {e}")

        return domains_count

    def get_statistics(self) -> Dict:
        """Get crawling statistics"""
        return {
            'total_certificates': len(self.certificates),
            'total_domains_discovered': len(self.discovered_domains),
            'bd_domains': sorted(list(self.discovered_domains))
        }

    def save_results(self, output_file: str):
        """Save discovered domains to file"""
        with open(output_file, 'w') as f:
            for domain in sorted(self.discovered_domains):
                f.write(f"{domain}\n")

        logger.info(
            f"Saved {len(self.discovered_domains)} domains to {output_file}"
        )


async def main():
    """Main entry point"""
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    crawler = SSLCertificateTransparencyCrawler()
    stats = crawler.crawl_all_providers(max_entries=5000)

    print("\n" + "=" * 60)
    print("CT LOG CRAWL STATISTICS")
    print("=" * 60)
    print(f"Total entries processed: {stats['total_entries_processed']}")
    print(f"Total domains discovered: {stats['total_domains_discovered']}")
    print(f".bd domains found: {len(stats['bd_domains'])}")
    print("\nProvider Results:")
    for provider, result in stats['providers'].items():
        if 'error' in result:
            print(f"  {provider}: ERROR - {result['error']}")
        else:
            print(
                f"  {provider}: "
                f"{result.get('domains_discovered', 0)} domains"
            )
    print("=" * 60)

    # Save results
    crawler.save_results('ct_log_domains.txt')


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
