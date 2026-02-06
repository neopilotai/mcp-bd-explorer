#!/usr/bin/env python3
"""
Domain Seed List CSV Importer for MCP-BD Explorer
Imports domain CSV files into PostgreSQL database
"""

import csv
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
import psycopg2
from psycopg2.extras import execute_batch
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DomainCSVImporter:
    """Imports domain CSV files into database"""
    
    VALID_CATEGORIES = {
        'government', 'education', 'healthcare', 'finance', 'commerce',
        'media', 'telecom', 'ngo', 'technology', 'general'
    }
    
    VALID_PRIORITIES = {'critical', 'high', 'medium', 'low'}
    VALID_STATUSES = {'pending', 'active', 'inactive', 'invalid'}
    VALID_SOURCES = {'whois_bulk', 'public_list', 'yellow_pages', 'gov_registry', 'popular_sites', 'manual_entry'}
    VALID_TLDS = {'bd', 'com.bd', 'org.bd', 'edu.bd', 'gov.bd', 'net.bd', 'ac.bd', 'biz.bd', 'mobi.bd', 'info.bd'}
    
    def __init__(self, db_host: str, db_name: str, db_user: str, db_password: str, db_port: int = 5432):
        """Initialize database connection"""
        self.db_config = {
            'host': db_host,
            'database': db_name,
            'user': db_user,
            'password': db_password,
            'port': db_port
        }
        self.conn = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database {self.db_config['database']}")
            return True
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
    
    def validate_row(self, row: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate CSV row data
        Returns (is_valid, error_message)
        """
        # Check required fields
        if not row.get('domain'):
            return False, "Missing domain"
        
        if not row.get('tld_type'):
            return False, "Missing tld_type"
        
        # Validate domain format
        domain = row['domain'].lower().strip()
        if not domain or len(domain) > 255:
            return False, f"Invalid domain: {domain}"
        
        # Validate TLD
        tld_type = row['tld_type'].lower().strip()
        if tld_type not in self.VALID_TLDS:
            return False, f"Invalid tld_type: {tld_type}"
        
        # Validate category
        category = row.get('category', 'general').lower().strip()
        if category not in self.VALID_CATEGORIES:
            return False, f"Invalid category: {category}"
        
        # Validate priority
        priority = row.get('priority', 'medium').lower().strip()
        if priority not in self.VALID_PRIORITIES:
            return False, f"Invalid priority: {priority}"
        
        # Validate status
        status = row.get('status', 'pending').lower().strip()
        if status not in self.VALID_STATUSES:
            return False, f"Invalid status: {status}"
        
        # Validate source
        source = row.get('source', 'manual_entry').lower().strip()
        if source not in self.VALID_SOURCES:
            return False, f"Invalid source: {source}"
        
        # Validate score if present
        if row.get('validation_score'):
            try:
                score = float(row['validation_score'])
                if not (0 <= score <= 1):
                    return False, f"Score out of range: {score}"
            except ValueError:
                return False, f"Invalid validation_score: {row['validation_score']}"
        
        return True, None
    
    def sanitize_row(self, row: Dict) -> Dict:
        """Sanitize and normalize CSV row"""
        return {
            'domain': row['domain'].lower().strip(),
            'tld_type': row['tld_type'].lower().strip(),
            'category': row.get('category', 'general').lower().strip(),
            'priority': row.get('priority', 'medium').lower().strip(),
            'status': row.get('status', 'pending').lower().strip(),
            'source': row.get('source', 'manual_entry').lower().strip(),
            'validation_score': float(row['validation_score']) if row.get('validation_score') else 0.0,
            'notes': row.get('notes', '').strip()[:500],  # Limit to 500 chars
        }
    
    def import_csv(self, csv_file: str, batch_size: int = 1000, skip_errors: bool = True) -> Dict:
        """
        Import domains from CSV file
        Returns import statistics
        """
        stats = {
            'total_rows': 0,
            'imported': 0,
            'skipped': 0,
            'errors': [],
            'start_time': datetime.now(),
            'end_time': None,
            'duration': None
        }
        
        if not self.conn:
            logger.error("Not connected to database")
            return stats
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if not reader.fieldnames:
                    logger.error("CSV file has no headers")
                    return stats
                
                batch = []
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (skip header)
                    stats['total_rows'] += 1
                    
                    # Validate row
                    is_valid, error_msg = self.validate_row(row)
                    if not is_valid:
                        error = f"Row {row_num}: {error_msg}"
                        stats['errors'].append(error)
                        stats['skipped'] += 1
                        if not skip_errors:
                            logger.error(error)
                        continue
                    
                    # Sanitize row
                    clean_row = self.sanitize_row(row)
                    
                    # Add to batch
                    batch.append((
                        clean_row['domain'],
                        clean_row['tld_type'],
                        clean_row['category'],
                        clean_row['priority'],
                        clean_row['source'],
                        clean_row['status'],
                        clean_row['validation_score'],
                        clean_row['notes'],
                        datetime.now()
                    ))
                    
                    # Insert batch when full
                    if len(batch) >= batch_size:
                        imported = self._insert_batch(batch)
                        stats['imported'] += imported
                        batch = []
                        logger.info(f"Progress: {stats['total_rows']} rows processed, {stats['imported']} imported")
                
                # Insert remaining batch
                if batch:
                    imported = self._insert_batch(batch)
                    stats['imported'] += imported
        
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            stats['errors'].append(str(e))
            if self.conn:
                self.conn.rollback()
        
        stats['end_time'] = datetime.now()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        
        return stats
    
    def _insert_batch(self, batch: List[tuple]) -> int:
        """Insert batch of domains"""
        if not batch or not self.cursor:
            return 0
        
        insert_sql = """
            INSERT INTO domains 
            (domain, tld_type, category, priority, source, status, validation_score, notes, added_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (domain) DO UPDATE SET
                last_updated = NOW(),
                priority = CASE WHEN domains.priority = 'medium' THEN EXCLUDED.priority ELSE domains.priority END
            RETURNING id;
        """
        
        try:
            execute_batch(self.cursor, insert_sql, batch, page_size=1000)
            self.conn.commit()
            return len(batch)
        except psycopg2.Error as e:
            logger.error(f"Batch insert failed: {e}")
            self.conn.rollback()
            return 0
    
    def import_multiple_files(self, csv_files: List[str]) -> Dict:
        """Import from multiple CSV files"""
        total_stats = {
            'total_files': len(csv_files),
            'files_processed': 0,
            'total_rows': 0,
            'total_imported': 0,
            'total_skipped': 0,
            'file_stats': {}
        }
        
        for csv_file in csv_files:
            logger.info(f"Importing {csv_file}...")
            stats = self.import_csv(csv_file)
            
            total_stats['files_processed'] += 1
            total_stats['total_rows'] += stats['total_rows']
            total_stats['total_imported'] += stats['imported']
            total_stats['total_skipped'] += stats['skipped']
            total_stats['file_stats'][csv_file] = stats
            
            logger.info(f"  Imported: {stats['imported']}, Skipped: {stats['skipped']}, Duration: {stats['duration']:.2f}s")
        
        return total_stats
    
    def get_import_summary(self) -> Dict:
        """Get summary of imported domains"""
        if not self.cursor:
            return {}
        
        try:
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'active') as active,
                    COUNT(*) FILTER (WHERE validation_score >= 0.9) as high_quality,
                    COUNT(DISTINCT category) as categories,
                    COUNT(DISTINCT tld_type) as tld_types
                FROM domains;
            """)
            
            result = self.cursor.fetchone()
            return {
                'total_domains': result[0] or 0,
                'active_domains': result[1] or 0,
                'high_quality_domains': result[2] or 0,
                'unique_categories': result[3] or 0,
                'unique_tld_types': result[4] or 0
            }
        except psycopg2.Error as e:
            logger.error(f"Error getting summary: {e}")
            return {}


def print_import_stats(stats: Dict) -> None:
    """Print import statistics"""
    print("\n" + "="*60)
    print("IMPORT STATISTICS")
    print("="*60)
    print(f"Total Rows: {stats['total_rows']:,}")
    print(f"Imported: {stats['imported']:,}")
    print(f"Skipped: {stats['skipped']:,}")
    print(f"Duration: {stats['duration']:.2f} seconds")
    print(f"Rate: {stats['imported'] / stats['duration']:.0f} domains/sec")
    
    if stats['errors']:
        print(f"\nFirst 10 Errors:")
        for error in stats['errors'][:10]:
            print(f"  - {error}")
    
    print("="*60 + "\n")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python import_seed_list.py <csv_file> [csv_file2 ...]")
        sys.exit(1)
    
    # Database configuration (from environment or defaults)
    importer = DomainCSVImporter(
        db_host='localhost',
        db_name='mcp_bd_explorer',
        db_user='postgres',
        db_password='postgres'
    )
    
    if not importer.connect():
        sys.exit(1)
    
    try:
        # Import CSV files
        csv_files = sys.argv[1:]
        total_stats = importer.import_multiple_files(csv_files)
        
        # Print overall statistics
        print("\n" + "="*60)
        print("OVERALL IMPORT RESULTS")
        print("="*60)
        print(f"Files Processed: {total_stats['files_processed']}/{total_stats['total_files']}")
        print(f"Total Rows: {total_stats['total_rows']:,}")
        print(f"Total Imported: {total_stats['total_imported']:,}")
        print(f"Total Skipped: {total_stats['total_skipped']:,}")
        
        # Get final summary
        summary = importer.get_import_summary()
        if summary:
            print(f"\nDatabase Summary:")
            print(f"  Total Domains: {summary['total_domains']:,}")
            print(f"  Active Domains: {summary['active_domains']:,}")
            print(f"  High Quality: {summary['high_quality_domains']:,}")
            print(f"  Unique Categories: {summary['unique_categories']}")
            print(f"  Unique TLD Types: {summary['unique_tld_types']}")
        
        print("="*60 + "\n")
        
    finally:
        importer.disconnect()


if __name__ == "__main__":
    main()
