# scripts/extraction_job_scheduler.py

"""
Configurable job scheduler for extraction layer.
Manages scheduling, queuing, and execution of scraping and API jobs.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from dataclasses import dataclass, asdict
import yaml
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from croniter import croniter
from enum import Enum

logger = logging.getLogger(__name__)

class JobType(Enum):
    """Job type enumeration"""
    FULL_CRAWL = "full_crawl"
    INCREMENTAL = "incremental"
    STATUS_CHECK = "status_check"
    TECH_DETECT = "tech_detect"
    API_FETCH = "api_fetch"
    METADATA_REFRESH = "metadata_refresh"

class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class JobConfig:
    """Configuration for extraction jobs"""
    id: str
    name: str
    job_type: JobType
    schedule: str
    enabled: bool = True
    priority: int = 5
    timeout: int = 3600
    concurrent: int = 5
    retry_count: int = 3
    retry_backoff: str = "exponential"
    config: Dict[str, Any] = None

@dataclass
class JobExecution:
    """Track individual job execution"""
    job_id: str
    execution_id: str
    status: JobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None

class ExtractionJobScheduler:
    """Main scheduler for extraction jobs"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.jobs: Dict[str, JobConfig] = {}
        self.executions: Dict[str, JobExecution] = {}
        
        # Initialize connections
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        self.db_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'mcp_bd'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        self._load_config()
    
    def _load_config(self) -> None:
        """Load job configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            for job_data in config_data.get('jobs', []):
                job = JobConfig(
                    id=job_data['id'],
                    name=job_data['name'],
                    job_type=JobType(job_data['type']),
                    schedule=job_data['schedule'],
                    enabled=job_data.get('enabled', True),
                    priority=job_data.get('priority', 5),
                    timeout=job_data['config'].get('timeout', 3600),
                    concurrent=job_data['config'].get('concurrent', 5),
                    retry_count=job_data['config'].get('retry', 3),
                    config=job_data.get('config', {})
                )
                self.jobs[job.id] = job
                logger.info(f"Loaded job configuration: {job.name}")
        
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
        except yaml.YAMLError as e:
            logger.error(f"YAML parse error: {e}")
    
    def get_next_execution_time(self, job_id: str) -> Optional[datetime]:
        """Calculate next execution time for a job"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        cron = croniter(job.schedule, datetime.now())
        return cron.get_next(datetime)
    
    def schedule_job(self, job_id: str) -> Optional[str]:
        """Queue a job for execution"""
        if job_id not in self.jobs:
            logger.error(f"Job not found: {job_id}")
            return None
        
        job = self.jobs[job_id]
        
        # Create execution record
        execution_id = f"{job_id}_{datetime.now().timestamp()}"
        execution = JobExecution(
            job_id=job_id,
            execution_id=execution_id,
            status=JobStatus.QUEUED
        )
        
        # Store in Redis queue
        queue_key = f"job_queue:{job.priority}"
        job_data = {
            'execution_id': execution_id,
            'job_id': job_id,
            'job_type': job.job_type.value,
            'config': json.dumps(job.config),
            'enqueued_at': datetime.now().isoformat()
        }
        
        self.redis_client.rpush(queue_key, json.dumps(job_data))
        
        # Store execution in database
        self._store_execution(execution)
        
        logger.info(f"Job queued: {job.name} (execution_id: {execution_id})")
        return execution_id
    
    def _store_execution(self, execution: JobExecution) -> None:
        """Store execution record in PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO job_executions 
                (job_id, execution_id, status, enqueued_at)
                VALUES (%s, %s, %s, %s)
            """, (execution.job_id, execution.execution_id, 
                  execution.status.value, datetime.now()))
            
            conn.commit()
            cursor.close()
            conn.close()
        
        except psycopg2.Error as e:
            logger.error(f"Database error storing execution: {e}")
    
    def update_execution_status(self, execution_id: str, 
                               status: JobStatus, 
                               error_msg: str = None) -> None:
        """Update job execution status"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            if status == JobStatus.COMPLETED:
                cursor.execute("""
                    UPDATE job_executions 
                    SET status = %s, completed_at = %s
                    WHERE execution_id = %s
                """, (status.value, datetime.now(), execution_id))
            
            elif status == JobStatus.FAILED:
                cursor.execute("""
                    UPDATE job_executions 
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE execution_id = %s
                """, (status.value, error_msg, datetime.now(), execution_id))
            
            else:
                cursor.execute("""
                    UPDATE job_executions 
                    SET status = %s
                    WHERE execution_id = %s
                """, (status.value, execution_id))
            
            conn.commit()
            cursor.close()
            conn.close()
        
        except psycopg2.Error as e:
            logger.error(f"Database error updating execution: {e}")
    
    def get_job_status(self, execution_id: str) -> Optional[Dict]:
        """Get current status of a job execution"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM job_executions 
                WHERE execution_id = %s
            """, (execution_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return dict(result) if result else None
        
        except psycopg2.Error as e:
            logger.error(f"Database error getting job status: {e}")
            return None
    
    def get_domains_for_extraction(self, job_type: JobType, 
                                   limit: int = 1000) -> List[Dict]:
        """Get domains to extract based on job type"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if job_type == JobType.FULL_CRAWL:
                query = "SELECT * FROM domains WHERE status = 'active' LIMIT %s"
            
            elif job_type == JobType.INCREMENTAL:
                query = """
                    SELECT * FROM domains 
                    WHERE status = 'active' 
                    AND (last_crawled < NOW() - INTERVAL '30 days'
                         OR last_crawled IS NULL)
                    LIMIT %s
                """
            
            elif job_type == JobType.STATUS_CHECK:
                query = """
                    SELECT * FROM domains 
                    WHERE status = 'active'
                    LIMIT %s
                """
            
            elif job_type == JobType.TECH_DETECT:
                query = """
                    SELECT * FROM domains 
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    LIMIT %s
                """
            
            else:
                return []
            
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
        
        except psycopg2.Error as e:
            logger.error(f"Database error fetching domains: {e}")
            return []


class IncrementalUpdateManager:
    """Manages incremental updates for domains"""
    
    def __init__(self, db_params: Dict):
        self.db_params = db_params
    
    def mark_for_update(self, domain_ids: List[int], 
                        days_since_update: int = 30) -> int:
        """Mark domains for incremental update"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            update_date = datetime.now() - timedelta(days=days_since_update)
            
            cursor.execute("""
                UPDATE domains 
                SET update_required = true,
                    marked_for_update_at = %s
                WHERE id = ANY(%s)
                AND (last_crawled < %s OR last_crawled IS NULL)
            """, (datetime.now(), domain_ids, update_date))
            
            updated = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Marked {updated} domains for update")
            return updated
        
        except psycopg2.Error as e:
            logger.error(f"Database error marking domains: {e}")
            return 0
    
    def get_update_batch(self, batch_size: int = 500) -> List[Dict]:
        """Get next batch of domains for incremental update"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM domains 
                WHERE update_required = true
                ORDER BY marked_for_update_at ASC
                LIMIT %s
            """, (batch_size,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
        
        except psycopg2.Error as e:
            logger.error(f"Database error getting update batch: {e}")
            return []
    
    def complete_update(self, domain_id: int, 
                       update_data: Dict) -> bool:
        """Mark domain update as complete"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE domains 
                SET update_required = false,
                    last_crawled = %s,
                    last_updated = %s,
                    status_code = %s,
                    response_time_ms = %s,
                    content_length = %s
                WHERE id = %s
            """, (datetime.now(), datetime.now(), 
                  update_data.get('status_code'),
                  update_data.get('response_time_ms'),
                  update_data.get('content_length'),
                  domain_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        
        except psycopg2.Error as e:
            logger.error(f"Database error completing update: {e}")
            return False


if __name__ == '__main__':
    # Initialize scheduler
    scheduler = ExtractionJobScheduler('jobs_config.yaml')
    
    # Example: Queue a job
    execution_id = scheduler.schedule_job('incremental_daily')
    print(f"Job queued with execution_id: {execution_id}")
    
    # Get next execution time
    for job_id in scheduler.jobs:
        next_time = scheduler.get_next_execution_time(job_id)
        print(f"Job {job_id} next execution: {next_time}")
