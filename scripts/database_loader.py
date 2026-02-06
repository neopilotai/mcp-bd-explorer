"""
Phase 4.3 - Database Loader Implementation
Handles batch loading with versioning and error recovery
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2.pool import SimpleConnectionPool
import uuid

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Production-grade database loader with versioning and error handling"""
    
    def __init__(self, 
                 db_host: str,
                 db_port: int = 5432,
                 db_name: str = "mcp_explorer",
                 db_user: str = "postgres",
                 db_password: str = "",
                 pool_size: int = 10,
                 batch_size: int = 1000):
        """Initialize database loader with connection pooling"""
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
        self.pool_size = pool_size
        self.batch_size = batch_size
        self.connection_pool = None
        self.stats = {
            'inserted': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
    
    def connect(self) -> None:
        """Initialize connection pool"""
        try:
            self.connection_pool = SimpleConnectionPool(
                1, self.pool_size,
                **self.db_config
            )
            logger.info(f"Connection pool created with {self.pool_size} connections")
        except psycopg2.Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Connection pool closed")
    
    def _get_connection(self):
        """Get connection from pool"""
        return self.connection_pool.getconn()
    
    def _release_connection(self, conn):
        """Release connection back to pool"""
        self.connection_pool.putconn(conn)
    
    def load_domains_batch(self, domains: List[Dict[str, Any]]) -> Tuple[int, int, int]:
        """
        Load batch of domains with upsert logic
        
        Args:
            domains: List of domain records
            
        Returns:
            Tuple of (inserted, updated, failed)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        inserted = 0
        updated = 0
        failed = 0
        
        try:
            # Prepare upsert statements
            for domain in domains:
                try:
                    upsert_sql = """
                    INSERT INTO domains (domain_name, tld, category, quality_score, 
                                        crawl_status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (domain_name) DO UPDATE
                    SET category = EXCLUDED.category,
                        quality_score = EXCLUDED.quality_score,
                        crawl_status = EXCLUDED.crawl_status,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING domain_id, (xmax = 0) as is_insert;
                    """
                    
                    cursor.execute(upsert_sql, (
                        domain['domain_name'],
                        domain['tld'],
                        domain.get('category', 'unknown'),
                        domain.get('quality_score', 0.5),
                        domain.get('status', 'pending'),
                        domain.get('created_at', datetime.utcnow()),
                        datetime.utcnow()
                    ))
                    
                    result = cursor.fetchone()
                    if result and result[1]:
                        inserted += 1
                    else:
                        updated += 1
                        
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to load domain {domain.get('domain_name')}: {e}")
                    self.stats['errors'].append(str(e))
            
            conn.commit()
            self.stats['inserted'] += inserted
            self.stats['updated'] += updated
            self.stats['failed'] += failed
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Batch load failed: {e}")
            failed = len(domains)
            self.stats['failed'] += failed
        
        finally:
            cursor.close()
            self._release_connection(conn)
        
        return inserted, updated, failed
    
    def load_technologies_batch(self, tech_mappings: List[Dict[str, Any]]) -> Tuple[int, int, int]:
        """Load technology stack mappings"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        inserted = 0
        updated = 0
        failed = 0
        
        try:
            for mapping in tech_mappings:
                try:
                    upsert_sql = """
                    INSERT INTO domain_technologies (domain_id, tech_id, confidence_score, version)
                    VALUES (%s, %s, %s, 1)
                    ON CONFLICT (domain_id, tech_id) DO UPDATE
                    SET confidence_score = EXCLUDED.confidence_score,
                        version = version + 1,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING (xmax = 0) as is_insert;
                    """
                    
                    cursor.execute(upsert_sql, (
                        mapping['domain_id'],
                        mapping['tech_id'],
                        mapping.get('confidence_score', 0.8)
                    ))
                    
                    result = cursor.fetchone()
                    if result and result[0]:
                        inserted += 1
                    else:
                        updated += 1
                        
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to load technology mapping: {e}")
            
            conn.commit()
            self.stats['inserted'] += inserted
            self.stats['updated'] += updated
            self.stats['failed'] += failed
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Technology batch load failed: {e}")
            failed = len(tech_mappings)
        
        finally:
            cursor.close()
            self._release_connection(conn)
        
        return inserted, updated, failed
    
    def load_metrics_batch(self, metrics: List[Dict[str, Any]]) -> Tuple[int, int, int]:
        """Load daily metrics for domains"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        inserted = 0
        updated = 0
        failed = 0
        
        try:
            for metric in metrics:
                try:
                    upsert_sql = """
                    INSERT INTO metrics_daily (domain_id, metric_date, estimated_visits, 
                                               bounce_rate, organic_traffic, backlink_count)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (domain_id, metric_date) DO UPDATE
                    SET estimated_visits = EXCLUDED.estimated_visits,
                        bounce_rate = EXCLUDED.bounce_rate,
                        organic_traffic = EXCLUDED.organic_traffic,
                        backlink_count = EXCLUDED.backlink_count
                    RETURNING (xmax = 0) as is_insert;
                    """
                    
                    cursor.execute(upsert_sql, (
                        metric['domain_id'],
                        metric['metric_date'],
                        metric.get('estimated_visits', 0),
                        metric.get('bounce_rate', 0),
                        metric.get('organic_traffic', 0),
                        metric.get('backlink_count', 0)
                    ))
                    
                    result = cursor.fetchone()
                    if result and result[0]:
                        inserted += 1
                    else:
                        updated += 1
                        
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to load metric: {e}")
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Metrics batch load failed: {e}")
            failed = len(metrics)
        
        finally:
            cursor.close()
            self._release_connection(conn)
        
        return inserted, updated, failed
    
    def record_audit_log(self, table_name: str, record_id: str, 
                        operation: str, old_values: Dict, new_values: Dict) -> bool:
        """Record change in audit trail"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            insert_sql = """
            INSERT INTO audit_log (audit_id, table_name, record_id, operation, 
                                   old_values, new_values, changed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            
            cursor.execute(insert_sql, (
                str(uuid.uuid4()),
                table_name,
                record_id,
                operation,
                json.dumps(old_values),
                json.dumps(new_values),
                datetime.utcnow()
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")
            conn.rollback()
            return False
        
        finally:
            cursor.close()
            self._release_connection(conn)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return load statistics"""
        return {
            'inserted': self.stats['inserted'],
            'updated': self.stats['updated'],
            'failed': self.stats['failed'],
            'total_processed': self.stats['inserted'] + self.stats['updated'] + self.stats['failed'],
            'error_count': len(self.stats['errors']),
            'errors': self.stats['errors'][-10:]  # Last 10 errors
        }
    
    def reset_statistics(self) -> None:
        """Reset load statistics"""
        self.stats = {
            'inserted': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }


# Usage example
if __name__ == "__main__":
    loader = DatabaseLoader(
        db_host="localhost",
        db_port=5432,
        db_name="mcp_explorer",
        db_user="postgres",
        db_password="password",
        pool_size=10,
        batch_size=1000
    )
    
    loader.connect()
    
    # Load sample domains
    sample_domains = [
        {
            'domain_name': 'example.com.bd',
            'tld': '.com.bd',
            'category': 'business',
            'quality_score': 0.85,
            'status': 'success'
        }
    ]
    
    inserted, updated, failed = loader.load_domains_batch(sample_domains)
    print(f"Inserted: {inserted}, Updated: {updated}, Failed: {failed}")
    print(f"Statistics: {loader.get_statistics()}")
    
    loader.disconnect()
