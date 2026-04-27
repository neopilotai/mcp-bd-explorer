# PHASE 4.1 - Extraction Layer

## Overview

The Extraction Layer provides multiple data collection methods for the MCP-BD Explorer system. This phase focuses on building configurable scraping jobs and incremental update scripts that work together to maintain a comprehensive and current database of Bangladeshi domains.

## Architecture

### Data Sources

1. **Web Crawling (Puppeteer)**
   - JavaScript-heavy sites
   - Real-time content extraction
   - Progressive crawling
   - Rate limiting: 10 sites/minute

2. **API Integrations**
   - Search engine APIs (Bing, DuckDuckGo)
   - WHOIS APIs
   - DNS query APIs
   - SSL certificate APIs

3. **Incremental Updates**
   - Domain status checks (HTTP HEAD requests)
   - Metadata refresh (monthly cycle)
   - Technology detection updates
   - SEO metrics refresh

### Job Types

| Job Type | Frequency | Scope | Priority |
|----------|-----------|-------|----------|
| Full Crawl | Monthly | All domains | Low |
| Incremental | Daily | Last 30 days | Medium |
| Status Check | Weekly | Active domains | High |
| Metadata Refresh | Monthly | Quality tier 1-2 | Medium |
| Technology Detect | Bi-weekly | New/updated | Medium |

## Configurable Scraping Jobs

### Job Configuration Format

```yaml
jobs:
  - id: "full_crawl_monthly"
    name: "Full Monthly Crawl"
    type: "full_crawl"
    schedule: "0 0 1 * *"  # Monthly on 1st
    config:
      domains: "all"
      timeout: 30000
      concurrent: 5
      retry: 3
      storage: "s3"
    
  - id: "incremental_daily"
    name: "Daily Incremental Update"
    type: "incremental"
    schedule: "0 2 * * *"  # Daily at 2 AM
    config:
      days_back: 30
      timeout: 20000
      concurrent: 10
      retry: 2
      
  - id: "status_check_weekly"
    name: "Weekly Status Check"
    type: "status_check"
    schedule: "0 3 * * 0"  # Weekly Sunday 3 AM
    config:
      scope: "active_domains"
      timeout: 5000
      concurrent: 20
      http_method: "HEAD"
      
  - id: "tech_detect_biweekly"
    name: "Technology Detection"
    type: "tech_detect"
    schedule: "0 4 * * 1,3,5"  # Mon/Wed/Fri
    config:
      scope: "recent_30_days"
      timeout: 15000
      concurrent: 8
      tools:
        - "builtwith"
        - "wappalyzer"
        - "custom_detector"
```

### Job Execution Pipeline

```
Config Load
    ↓
Domain Query (PostgreSQL)
    ↓
Queue Job (Redis/Celery)
    ↓
Worker Pool
    ├─ Puppeteer Extraction
    ├─ API Calls
    ├─ HTTP Requests
    └─ Metadata Processing
    ↓
Result Processing
    ├─ Parse Response
    ├─ Extract Data
    ├─ Quality Check
    └─ Error Handling
    ↓
Storage
    ├─ PostgreSQL (Metadata)
    ├─ Elasticsearch (Index)
    ├─ S3 (Raw HTML)
    └─ Redis (Cache)
    ↓
Status Update
    ├─ Job Completion
    ├─ Error Logging
    ├─ Metrics Recording
    └─ Notifications
```

## Incremental Update Scripts

### Update Strategy

**Day 1-5**: Incremental crawl (recent 30 days)
- New domains only
- Status updates
- Quick metadata refresh

**Day 6-10**: Maintenance cycle
- Dead link removal
- Technology detection
- SEO metrics update

**Day 11-20**: Content analysis
- Content categorization
- Quality scoring
- Analytics update

**Day 21-30**: Full metrics
- Comprehensive analysis
- Backlink checking
- Authority scoring

### Database Update Operations

```sql
-- Mark domains for update
UPDATE domains 
SET last_crawled = NOW() - INTERVAL '30 days'
WHERE status = 'active' 
AND created_at < NOW() - INTERVAL '30 days'
LIMIT 10000;

-- Update crawl status
UPDATE crawl_jobs
SET status = 'completed',
    finished_at = NOW(),
    records_processed = $1
WHERE id = $2;

-- Increment update counter
UPDATE domain_metrics
SET update_count = update_count + 1,
    last_update = NOW()
WHERE domain_id = $1;
```

## Monitoring & Error Handling

### Job Monitoring

- Real-time job status tracking
- Success/failure metrics
- Performance monitoring (qps, latency)
- Error logging with retry logic
- Dead letter queue for failed items

### Error Recovery

| Error Type | Retry Count | Backoff Strategy |
|-----------|------------|------------------|
| Network timeout | 3 | Exponential (2^n * 1s) |
| 429 (Rate limit) | 5 | Linear + jitter (10-60s) |
| 5xx Server error | 2 | Exponential (2^n * 5s) |
| Invalid data | 0 | DLQ + alert |
| DNS failure | 2 | Exponential (5-30s) |

### Metrics

- Jobs per hour: 50-200
- Success rate target: 95%+
- Average job duration: 5-60 minutes
- Error rate target: <5%
- Retry success rate: 70%+

## Next Steps

- Implementation of job scheduler (Airflow/APScheduler)
- API connector development
- Incremental update script creation
- Monitoring & alerting setup
- Testing & validation

---

**Phase 4.1 Status**: Documentation Complete
**Next Phase**: 4.2 Transformation Workflows
