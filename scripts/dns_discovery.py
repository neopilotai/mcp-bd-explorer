#!/usr/bin/env python3
"""
DNS Discovery Module
Phase 2.2: Automated Crawling & Discovery

Discovers .bd domains through:
- Reverse DNS lookups
- Zone transfers (AXFR)
- NS record enumeration
- SOA record analysis

Author: MCP-BD Team
Date: 2026-02-06
Version: 1.0
"""

import logging
import dns.resolver
import dns.zone
import dns.rdatatype
import dns.query
import socket
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress

logger = logging.getLogger(__name__)


@dataclass
class DNSRecord:
    """Represents a DNS record"""
    domain: str
    record_type: str
    value: str
    ttl: Optional[int] = None
    authority: Optional[str] = None


class DNSDiscoveryModule:
    """
    Discovers .bd domains through DNS queries
    
    Methods:
    - Reverse DNS lookup on Bangladesh IP ranges
    - Zone transfers (if permitted)
    - NS record enumeration
    - SOA record analysis
    """

    def __init__(
        self,
        nameservers: List[str] = None,
        max_workers: int = 10
    ):
        self.nameservers = nameservers or [
            '8.8.8.8',      # Google
            '1.1.1.1',      # Cloudflare
            '1.0.0.1',      # Cloudflare secondary
        ]
        self.max_workers = max_workers
        self.discovered_domains: Set[str] = set()
        self.dns_records: List[DNSRecord] = []

    def discover_all(self) -> Dict:
        """Run all discovery methods"""
        logger.info("Starting DNS discovery")

        stats = {
            'reverse_dns_domains': 0,
            'zone_transfer_domains': 0,
            'ns_enumeration_domains': 0,
            'total_unique_domains': 0,
            'domains': []
        }

        # Reverse DNS lookup
        logger.info("Starting reverse DNS lookup")
        reverse_domains = self._reverse_dns_discovery()
        stats['reverse_dns_domains'] = len(reverse_domains)
        self.discovered_domains.update(reverse_domains)

        # Zone transfers
        logger.info("Attempting zone transfers")
        zone_domains = self._zone_transfer_discovery()
        stats['zone_transfer_domains'] = len(zone_domains)
        self.discovered_domains.update(zone_domains)

        # NS enumeration
        logger.info("Enumerating NS records")
        ns_domains = self._ns_enumeration_discovery()
        stats['ns_enumeration_domains'] = len(ns_domains)
        self.discovered_domains.update(ns_domains)

        stats['total_unique_domains'] = len(self.discovered_domains)
        stats['domains'] = sorted(list(self.discovered_domains))

        return stats

    def _reverse_dns_discovery(self) -> Set[str]:
        """Discover domains via reverse DNS lookup"""
        domains = set()

        # Bangladesh IP ranges (sample)
        bangladesh_ranges = [
            ('220.225.0.0', '220.240.0.0'),      # Grameen Phone
            ('103.16.0.0', '103.31.255.255'),    # Various ISPs
            ('59.152.0.0', '59.183.255.255'),    # Robi Axiata
        ]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            for range_start, range_end in bangladesh_ranges:
                # Sample IPs from the range
                ips = self._sample_ip_range(range_start, range_end, 100)

                for ip in ips:
                    future = executor.submit(
                        self._reverse_lookup_single,
                        ip
                    )
                    futures[future] = ip

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        domains.update(result)
                except Exception as e:
                    logger.debug(f"Reverse DNS error: {e}")

        return domains

    def _reverse_lookup_single(self, ip: str) -> Set[str]:
        """Reverse lookup single IP"""
        domains = set()

        try:
            # Reverse DNS query
            hostname = socket.gethostbyaddr(ip)[0]

            if hostname.endswith('.bd'):
                domains.add(hostname.lower())

        except socket.herror:
            pass
        except socket.error:
            pass
        except Exception as e:
            logger.debug(f"Error reverse looking up {ip}: {e}")

        return domains

    def _zone_transfer_discovery(self) -> Set[str]:
        """Discover domains via zone transfer"""
        domains = set()

        # Try zone transfer for .bd
        try:
            # Attempt zone transfer
            zone = dns.zone.from_xfr(
                dns.query.xfr('ns1.bd', 'bd', lifetime=10)
            )

            # Extract all domain names
            for name, node in zone.items():
                domain_name = f"{name}.bd".lower()
                if domain_name.endswith('.bd'):
                    domains.add(domain_name)

        except Exception as e:
            logger.debug(f"Zone transfer failed: {e}")

        return domains

    def _ns_enumeration_discovery(self) -> Set[str]:
        """Discover domains by enumerating nameservers"""
        domains = set()

        # Query for NS records
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = self.nameservers

            # Query for NS records of .bd
            ns_records = resolver.query('bd', dns.rdatatype.NS)

            for rdata in ns_records:
                ns_name = str(rdata.target).rstrip('.')
                domains.add(ns_name.lower())

        except Exception as e:
            logger.debug(f"NS enumeration error: {e}")

        return domains

    @staticmethod
    def _sample_ip_range(
        start: str,
        end: str,
        sample_size: int = 100
    ) -> List[str]:
        """Sample IP range"""
        try:
            start_int = int(ipaddress.IPv4Address(start))
            end_int = int(ipaddress.IPv4Address(end))
            range_size = end_int - start_int

            if range_size <= sample_size:
                # Include all IPs
                ips = [
                    str(ipaddress.IPv4Address(ip))
                    for ip in range(start_int, end_int + 1)
                ]
            else:
                # Sample uniformly
                step = range_size // sample_size
                ips = [
                    str(ipaddress.IPv4Address(
                        start_int + i * step
                    ))
                    for i in range(sample_size)
                ]

            return ips

        except Exception as e:
            logger.error(f"Error sampling IP range: {e}")
            return []


async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    discovery = DNSDiscoveryModule()
    stats = discovery.discover_all()

    print("\n" + "=" * 60)
    print("DNS DISCOVERY STATISTICS")
    print("=" * 60)
    print(f"Reverse DNS domains: {stats['reverse_dns_domains']}")
    print(f"Zone transfer domains: {stats['zone_transfer_domains']}")
    print(f"NS enumeration domains: {stats['ns_enumeration_domains']}")
    print(f"Total unique domains: {stats['total_unique_domains']}")

    if stats['domains']:
        print("\nSample discovered domains:")
        for domain in stats['domains'][:10]:
            print(f"  - {domain}")
        if len(stats['domains']) > 10:
            print(f"  ... and {len(stats['domains']) - 10} more")

    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
