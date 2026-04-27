# PHASE 4.2 - Transformation Layer

## Overview

The Transformation Layer processes, cleans, normalizes, and categorizes raw extracted data into structured, high-quality records. This phase implements Apache Airflow workflows and Python/Pandas transformations to maintain data integrity and quality.

## Data Transformation Pipeline

### ETL Flow

```
Raw Data (Extraction Layer)
    ↓
Validation
├─ Schema validation
├─ Type checking
└─ Null handling
    ↓
Cleaning
├─ Whitespace normalization
├─ URL standardization
├─ Case normalization
└─ Special character handling
    ↓
Deduplication
├─ Exact match (domain)
├─ Fuzzy match (similar domains)
├─ Merge logic (keep newest)
└─ Historical tracking
    ↓
Normalization
├─ Domain format (lowercase, remove www)
├─ IP standardization
├─ Metadata standardization
└─ Relationship linking
    ↓
Categorization
├─ Website type classification
├─ Industry categorization
├─ Content classification
└─ Quality scoring
    ↓
Enrichment
├─ Technology detection
├─ Hosting provider lookup
├─ Regional classification
└─ Authority scoring
    ↓
Storage
├─ PostgreSQL (normalized)
├─ Elasticsearch (indexed)
└─ Cache (hot data)
```

### Transformation Operations

#### 1. Data Cleaning

```python
def clean_domain_data(record):
    """Clean extracted domain data"""
    
    # Remove whitespace
    domain = record['domain'].strip().lower()
    
    # Remove www prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Validate URL format
    if not is_valid_domain(domain):
        return None
    
    # Normalize metadata
    record['title'] = record.get('title', '').strip()[:255]
    record['description'] = record.get('description', '').strip()[:500]
    
    # Standardize URLs
    record['url'] = normalize_url(domain)
    
    return {**record, 'domain': domain}
```

#### 2. Deduplication

```python
def deduplicate_domains(domains_df):
    """Remove duplicates with smart merge logic"""
    
    # Exact match deduplication
    exact_dupes = domains_df.duplicated(subset=['domain'], keep='first')
    deduped = domains_df[~exact_dupes]
    
    # Fuzzy matching for similar domains
    similar_pairs = find_similar_domains(deduped, threshold=0.95)
    
    # Merge similar domains (keep with higher quality score)
    for domain1, domain2 in similar_pairs:
        if quality_score(domain1) >= quality_score(domain2):
            deduped = deduped[deduped['domain'] != domain2]
        else:
            deduped = deduped[deduped['domain'] != domain1]
    
    return deduped
```

#### 3. Website Categorization

```python
def categorize_website(record):
    """Classify website into categories"""
    
    categories = {
        'government': check_government_indicators,
        'news': check_news_indicators,
        'e-commerce': check_ecommerce_indicators,
        'education': check_education_indicators,
        'health': check_health_indicators,
        'finance': check_finance_indicators,
    }
    
    scores = {}
    for category, checker in categories.items():
        scores[category] = checker(record)
    
    # Assign primary category (highest score)
    primary = max(scores, key=scores.get)
    confidence = scores[primary]
    
    # Assign secondary categories if score > threshold
    secondary = [cat for cat, score in scores.items() 
                 if score > 0.5 and cat != primary]
    
    return {
        'primary_category': primary,
        'category_confidence': confidence,
        'secondary_categories': secondary,
        'category_scores': scores
    }
```

#### 4. Quality Scoring

```python
def calculate_quality_score(record):
    """Compute domain quality (0.0-1.0)"""
    
    score = 0.0
    weights = {
        'domain_age': 0.15,
        'ssl_valid': 0.20,
        'response_time': 0.15,
        'content_quality': 0.20,
        'tech_stack': 0.15,
        'authority': 0.15
    }
    
    # Domain age (0-15 years bonus)
    years = (now() - record['created_date']).days / 365
    age_score = min(years / 15, 1.0) * weights['domain_age']
    score += age_score
    
    # SSL validity
    score += (1.0 if record['ssl_valid'] else 0.0) * weights['ssl_valid']
    
    # Response time (<1s optimal)
    response_ms = record.get('response_time', 5000)
    speed_score = max(1 - (response_ms / 5000), 0) * weights['response_time']
    score += speed_score
    
    # Content quality (word count, grammar, etc)
    content_score = min(record.get('word_count', 0) / 1000, 1.0)
    score += content_score * weights['content_quality']
    
    # Technology stack diversity
    tech_count = len(record.get('technologies', []))
    tech_score = min(tech_count / 10, 1.0) * weights['tech_stack']
    score += tech_score
    
    # Authority (backlinks, domain authority)
    authority = record.get('domain_authority', 0)
    auth_score = min(authority / 60, 1.0) * weights['authority']
    score += auth_score
    
    return score
```

## Airflow Workflows

### DAG Structure

```
mcp_bd_etl_pipeline
├── extract_task
│   ├── extract_from_api
│   ├── extract_from_crawl
│   └── extract_from_incremental
├── validate_task
│   └── validate_schema
├── clean_task
│   ├── clean_domains
│   ├── normalize_urls
│   └── standardize_data
├── deduplicate_task
│   ├── exact_dedup
│   ├── fuzzy_dedup
│   └── merge_logic
├── categorize_task
│   ├── classify_website_type
│   ├── classify_industry
│   └── calculate_quality_score
├── enrich_task
│   ├── detect_technologies
│   ├── lookup_hosting
│   └── compute_authority
└── load_task
    ├── upsert_postgres
    ├── index_elasticsearch
    ├── populate_cache
    └── update_metrics
```

### Airflow DAG Definition

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'mcp-bd-explorer',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email': ['alerts@example.com']
}

dag = DAG(
    'mcp_bd_etl_pipeline',
    default_args=default_args,
    description='MCP-BD Explorer ETL Pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['mcp-bd', 'etl', 'production']
)

def extract_domains(**context):
    """Extract domains from various sources"""
    pass

def validate_data(**context):
    """Validate extracted data"""
    pass

def clean_data(**context):
    """Clean and normalize data"""
    pass

def deduplicate_data(**context):
    """Remove duplicates"""
    pass

def categorize_domains(**context):
    """Categorize websites"""
    pass

def enrich_domains(**context):
    """Enrich with additional data"""
    pass

def load_to_db(**context):
    """Load to PostgreSQL"""
    pass

def index_to_es(**context):
    """Index to Elasticsearch"""
    pass

# Task definitions
extract = PythonOperator(
    task_id='extract_domains',
    python_callable=extract_domains,
    dag=dag
)

validate = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag
)

clean = PythonOperator(
    task_id='clean_data',
    python_callable=clean_data,
    dag=dag
)

deduplicate = PythonOperator(
    task_id='deduplicate_data',
    python_callable=deduplicate_data,
    dag=dag
)

categorize = PythonOperator(
    task_id='categorize_domains',
    python_callable=categorize_domains,
    dag=dag
)

enrich = PythonOperator(
    task_id='enrich_domains',
    python_callable=enrich_domains,
    dag=dag
)

load = PythonOperator(
    task_id='load_to_db',
    python_callable=load_to_db,
    dag=dag
)

index = PythonOperator(
    task_id='index_to_es',
    python_callable=index_to_es,
    dag=dag
)

# Task dependencies
extract >> validate >> clean >> deduplicate >> [categorize, enrich] >> load >> index
```

## Transformation Workflows

### Daily Incremental Workflow

```
1. Extract (2 hours)
   - Fetch recent crawls (last 30 days)
   - Fetch new domains from APIs
   - Get status updates
   - Total: ~50k records

2. Validate (30 minutes)
   - Schema validation
   - Type checking
   - Null handling
   - Pass rate: 98%+

3. Clean (1 hour)
   - Normalize URLs
   - Remove duplicates from extraction
   - Standardize fields
   - Output: ~45k clean records

4. Deduplicate (45 minutes)
   - Check against existing domains
   - Fuzzy matching on similar domains
   - Merge duplicates
   - Net new domains: ~8-12k

5. Categorize (1 hour)
   - Website type classification
   - Industry categorization
   - Content analysis
   - Assign confidence scores

6. Load (30 minutes)
   - Upsert to PostgreSQL
   - Update Elasticsearch index
   - Refresh cache
   - Completion: 2 AM + 5.5 hours = 7:30 AM

Total Duration: ~5-6 hours
Success Rate Target: 95%+
```

### Monthly Full Crawl Workflow

```
1. Extract Full Dataset (16 hours)
   - All 100k domains
   - Full page crawl
   - Complete metadata extraction
   - All technologies detected

2. Validate (1 hour)
   - Comprehensive schema validation
   - Data type verification
   - Integrity checks

3. Clean (2 hours)
   - Full normalization
   - URL standardization
   - Format fixes

4. Deduplicate (2 hours)
   - Complete deduplication
   - Fuzzy matching on all pairs
   - Merge logic applied

5. Categorize (2 hours)
   - Full website classification
   - Industry mapping
   - Authority scoring

6. Enrich (2 hours)
   - Technology detection
   - Hosting lookup
   - Relationship building

7. Load (2 hours)
   - Full database replace
   - Elasticsearch reindex
   - Cache warmup

Total Duration: ~27 hours
Success Rate Target: 99%+
Monthly Schedule: 1st of each month
```

## Quality Assurance

### Data Quality Checks

- **Schema Validation**: 100% schema compliance
- **Type Checking**: Correct data types for all fields
- **Null Handling**: <5% null rate on required fields
- **Domain Validity**: 99%+ valid domains
- **URL Format**: 100% proper URL format
- **Categorization**: 95%+ confident categorization

### Monitoring

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Success Rate | 95%+ | <90% |
| Processing Time | <6 hours | >8 hours |
| Error Rate | <5% | >10% |
| Null Rate | <5% | >8% |
| Duplicate Rate | 0% | >0.1% |
| Quality Score Avg | 0.75+ | <0.65 |

## Delivery

- Configurable job specifications
- Airflow DAG definitions
- Transformation functions (Python)
- Monitoring & alerting setup
- Error handling & recovery
- Complete documentation

---

**Phase 4.2 Status**: Documentation Complete
**Confidence Level**: 9.5/10
**Ready for Implementation**: Yes
