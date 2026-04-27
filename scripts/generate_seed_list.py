#!/usr/bin/env python3
"""
Domain Seed List Generator for MCP-BD Explorer
Generates master seed list of .bd domains from multiple sources
"""

import csv
import asyncio
import httpx
import json
from datetime import datetime
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TldType(str, Enum):
    """Bangladesh TLD variants"""
    COM_BD = "com.bd"
    ORG_BD = "org.bd"
    EDU_BD = "edu.bd"
    GOV_BD = "gov.bd"
    NET_BD = "net.bd"
    AC_BD = "ac.bd"
    BD = "bd"
    BIZ_BD = "biz.bd"
    MOBI_BD = "mobi.bd"
    INFO_BD = "info.bd"


class Category(str, Enum):
    """Domain categories"""
    GOVERNMENT = "government"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    COMMERCE = "commerce"
    MEDIA = "media"
    TELECOM = "telecom"
    NGO = "ngo"
    TECHNOLOGY = "technology"
    GENERAL = "general"


class Priority(str, Enum):
    """Priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    """Domain status"""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    INVALID = "invalid"


class Source(str, Enum):
    """Data sources"""
    WHOIS_BULK = "whois_bulk"
    PUBLIC_LIST = "public_list"
    YELLOW_PAGES = "yellow_pages"
    GOV_REGISTRY = "gov_registry"
    POPULAR_SITES = "popular_sites"
    MANUAL_ENTRY = "manual_entry"


@dataclass
class Domain:
    """Domain data model"""
    domain: str
    tld_type: str
    category: str = Category.GENERAL.value
    priority: str = Priority.MEDIUM.value
    source: str = Source.MANUAL_ENTRY.value
    status: str = Status.PENDING.value
    validation_score: float = 0.0
    added_date: str = None
    notes: str = ""
    
    def __post_init__(self):
        if self.added_date is None:
            self.added_date = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for CSV"""
        return asdict(self)


class DomainValidator:
    """Validates domains"""
    
    BD_TLDS = {
        ".com.bd", ".org.bd", ".edu.bd", ".gov.bd",
        ".net.bd", ".ac.bd", ".bd", ".biz.bd",
        ".mobi.bd", ".info.bd"
    }
    
    @staticmethod
    def is_valid_format(domain: str) -> bool:
        """Check domain format validity"""
        # Must have at least one dot
        if '.' not in domain:
            return False
        
        # Check for valid characters
        pattern = r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$'
        return bool(re.match(pattern, domain.lower()))
    
    @staticmethod
    def has_bd_tld(domain: str) -> bool:
        """Check if domain has .bd TLD"""
        domain_lower = domain.lower()
        return any(domain_lower.endswith(tld) for tld in DomainValidator.BD_TLDS)
    
    @staticmethod
    def get_tld_type(domain: str) -> Optional[str]:
        """Extract TLD type from domain"""
        domain_lower = domain.lower()
        for tld in DomainValidator.BD_TLDS:
            if domain_lower.endswith(tld):
                return tld.lstrip('.')
        return None
    
    @staticmethod
    async def validate_dns(domain: str, score: float = 1.0) -> float:
        """
        Validate DNS resolution
        In production, would use dns.resolver or similar
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try HEAD request
                response = await client.head(f"https://{domain}", follow_redirects=True)
                if response.status_code < 500:
                    return score
        except Exception as e:
            logger.debug(f"DNS validation failed for {domain}: {e}")
            return score * 0.8
        
        return score * 0.5
    
    @staticmethod
    async def validate_http(domain: str, score: float = 1.0) -> float:
        """
        Validate HTTP responsiveness
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"https://{domain}", follow_redirects=True)
                if 200 <= response.status_code < 400:
                    return score
                elif response.status_code < 500:
                    return score * 0.7
        except Exception as e:
            logger.debug(f"HTTP validation failed for {domain}: {e}")
            return score * 0.5
        
        return score * 0.3
    
    @staticmethod
    async def calculate_validation_score(domain: str) -> float:
        """
        Calculate overall validation score
        """
        score = 1.0
        
        # Format validation (20%)
        if DomainValidator.is_valid_format(domain):
            format_score = 1.0
        else:
            format_score = 0.0
        
        # TLD validation (20%)
        if DomainValidator.has_bd_tld(domain):
            tld_score = 1.0
        else:
            tld_score = 0.0
        
        # DNS validation (20%)
        dns_score = await DomainValidator.validate_dns(domain)
        
        # HTTP validation (20%)
        http_score = await DomainValidator.validate_http(domain)
        
        # Whois validation (20%) - placeholder
        whois_score = 0.8
        
        # Calculate weighted score
        final_score = (
            format_score * 0.2 +
            tld_score * 0.2 +
            dns_score * 0.2 +
            http_score * 0.2 +
            whois_score * 0.2
        )
        
        return final_score


class DomainSeedListGenerator:
    """Generates domain seed lists from multiple sources"""
    
    def __init__(self):
        self.domains: Dict[str, Domain] = {}
        self.validator = DomainValidator()
    
    def add_domain(self, domain: Domain) -> bool:
        """Add domain to seed list (no duplicates)"""
        domain_lower = domain.domain.lower()
        if domain_lower in self.domains:
            return False
        self.domains[domain_lower] = domain
        return True
    
    def add_domains_bulk(self, domains: List[Domain]) -> int:
        """Add multiple domains, return count added"""
        count = 0
        for domain in domains:
            if self.add_domain(domain):
                count += 1
        return count
    
    def remove_invalid_domains(self) -> int:
        """Remove domains with invalid format"""
        invalid = []
        for domain_str, domain in self.domains.items():
            if not self.validator.is_valid_format(domain_str):
                invalid.append(domain_str)
            elif not self.validator.has_bd_tld(domain_str):
                invalid.append(domain_str)
        
        for domain_str in invalid:
            del self.domains[domain_str]
        
        return len(invalid)
    
    def categorize_by_tld(self) -> Dict[str, int]:
        """Get domain count by TLD type"""
        by_tld = {}
        for domain in self.domains.values():
            tld = domain.tld_type
            by_tld[tld] = by_tld.get(tld, 0) + 1
        return by_tld
    
    def categorize_by_category(self) -> Dict[str, int]:
        """Get domain count by category"""
        by_category = {}
        for domain in self.domains.values():
            cat = domain.category
            by_category[cat] = by_category.get(cat, 0) + 1
        return by_category
    
    def get_by_category(self, category: str) -> List[Domain]:
        """Get all domains in a category"""
        return [d for d in self.domains.values() if d.category == category]
    
    def get_by_priority(self, priority: str) -> List[Domain]:
        """Get all domains with specific priority"""
        return [d for d in self.domains.values() if d.priority == priority]
    
    def get_above_validation_score(self, min_score: float) -> List[Domain]:
        """Get domains above validation score threshold"""
        return [d for d in self.domains.values() if d.validation_score >= min_score]
    
    def export_csv(self, filename: str, domains: Optional[List[Domain]] = None) -> None:
        """Export domains to CSV file"""
        export_domains = domains or list(self.domains.values())
        
        if not export_domains:
            logger.warning(f"No domains to export to {filename}")
            return
        
        fieldnames = ['domain', 'tld_type', 'category', 'priority', 'source', 'status', 'validation_score', 'added_date', 'notes']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for domain in sorted(export_domains, key=lambda d: d.domain):
                writer.writerow(domain.to_dict())
        
        logger.info(f"Exported {len(export_domains)} domains to {filename}")
    
    def get_stats(self) -> Dict:
        """Get statistics about seed list"""
        return {
            'total_domains': len(self.domains),
            'by_tld': self.categorize_by_tld(),
            'by_category': self.categorize_by_category(),
            'by_priority': {p.value: len(self.get_by_priority(p.value)) for p in Priority},
            'avg_validation_score': sum(d.validation_score for d in self.domains.values()) / len(self.domains) if self.domains else 0.0,
            'high_quality_domains': len(self.get_above_validation_score(0.9)),
        }
    
    def print_stats(self) -> None:
        """Print statistics"""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("DOMAIN SEED LIST STATISTICS")
        print("="*60)
        print(f"Total Domains: {stats['total_domains']:,}")
        print(f"\nBy TLD Type:")
        for tld, count in sorted(stats['by_tld'].items()):
            print(f"  {tld}: {count:,}")
        print(f"\nBy Category:")
        for cat, count in sorted(stats['by_category'].items()):
            print(f"  {cat}: {count}")
        print(f"\nBy Priority:")
        for priority, count in sorted(stats['by_priority'].items()):
            print(f"  {priority}: {count}")
        print(f"\nQuality Metrics:")
        print(f"  Average Validation Score: {stats['avg_validation_score']:.2f}")
        print(f"  High Quality (>0.9): {stats['high_quality_domains']:,}")
        print("="*60 + "\n")


# Example usage and sample data

def create_sample_seed_list() -> DomainSeedListGenerator:
    """Create a sample seed list with test data"""
    generator = DomainSeedListGenerator()
    
    # Sample critical government domains
    critical_gov = [
        Domain("www.gov.bd", "bd", Category.GOVERNMENT.value, Priority.CRITICAL.value, Source.GOV_REGISTRY.value, notes="Main government portal"),
        Domain("bangladesh.gov.bd", "bd", Category.GOVERNMENT.value, Priority.CRITICAL.value, Source.GOV_REGISTRY.value, notes="Official Bangladesh portal"),
        Domain("mofa.gov.bd", "bd", Category.GOVERNMENT.value, Priority.CRITICAL.value, Source.GOV_REGISTRY.value, notes="Ministry of Foreign Affairs"),
        Domain("mof.gov.bd", "bd", Category.GOVERNMENT.value, Priority.CRITICAL.value, Source.GOV_REGISTRY.value, notes="Ministry of Finance"),
    ]
    
    # Sample educational domains
    educational = [
        Domain("diu.edu.bd", "edu.bd", Category.EDUCATION.value, Priority.HIGH.value, Source.GOV_REGISTRY.value, notes="Daffodil International University"),
        Domain("buet.ac.bd", "ac.bd", Category.EDUCATION.value, Priority.HIGH.value, Source.GOV_REGISTRY.value, notes="Bangladesh University of Engineering and Technology"),
        Domain("du.ac.bd", "ac.bd", Category.EDUCATION.value, Priority.HIGH.value, Source.GOV_REGISTRY.value, notes="University of Dhaka"),
        Domain("bracu.ac.bd", "ac.bd", Category.EDUCATION.value, Priority.HIGH.value, Source.GOV_REGISTRY.value, notes="Brac University"),
    ]
    
    # Sample commerce domains
    commerce = [
        Domain("daraz.com.bd", "com.bd", Category.COMMERCE.value, Priority.CRITICAL.value, Source.POPULAR_SITES.value, notes="Major e-commerce platform"),
        Domain("robi.com.bd", "com.bd", Category.COMMERCE.value, Priority.HIGH.value, Source.POPULAR_SITES.value, notes="Mobile telecom operator"),
        Domain("grameenphone.com.bd", "com.bd", Category.COMMERCE.value, Priority.HIGH.value, Source.POPULAR_SITES.value, notes="Major telecom provider"),
    ]
    
    # Sample media domains
    media = [
        Domain("bdnews24.com", "com", Category.MEDIA.value, Priority.HIGH.value, Source.POPULAR_SITES.value, notes="Online news portal"),
        Domain("prothomalo.com", "com", Category.MEDIA.value, Priority.HIGH.value, Source.POPULAR_SITES.value, notes="Daily newspaper"),
    ]
    
    # Sample finance domains
    finance = [
        Domain("bb.org.bd", "org.bd", Category.FINANCE.value, Priority.CRITICAL.value, Source.GOV_REGISTRY.value, notes="Bangladesh Bank (Central Bank)"),
    ]
    
    # Combine and add
    all_domains = critical_gov + educational + commerce + media + finance
    generator.add_domains_bulk(all_domains)
    
    logger.info(f"Created sample seed list with {len(all_domains)} domains")
    return generator


if __name__ == "__main__":
    # Create sample seed list
    generator = create_sample_seed_list()
    
    # Print statistics
    generator.print_stats()
    
    # Export full list
    generator.export_csv("master_seed_list.csv")
    
    # Export by category
    for category in Category:
        domains = generator.get_by_category(category.value)
        if domains:
            filename = f"seed_{category.value}.csv"
            generator.export_csv(filename, domains)
    
    # Export by priority
    for priority in Priority:
        domains = generator.get_by_priority(priority.value)
        if domains:
            filename = f"seed_priority_{priority.value}.csv"
            generator.export_csv(filename, domains)
    
    logger.info("Seed list generation complete!")
