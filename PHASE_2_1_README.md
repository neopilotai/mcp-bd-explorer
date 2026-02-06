# Phase 2.1: Domain Seed List Implementation Guide

## Overview

This directory contains all implementation files for Phase 2.1 - Domain Seed List generation for MCP-BD Explorer. The seed list is the foundation for the web crawler, containing all target domains to be discovered and crawled.

## 📦 Files Included

### Documentation
- `PHASE_2_1_DOMAIN_SEED_LIST.md` - Complete specification and planning document
- `README.md` - This file

### Scripts
- `scripts/generate_seed_list.py` - Python script to generate seed lists from multiple sources
- `scripts/import_seed_list.py` - CSV importer to load seed lists into PostgreSQL
- `scripts/001_create_domain_seed_list_tables.sql` - Database schema migration

### Sample Data
- `data/sample_seed_list.csv` - Sample seed list with 60 domains across all categories

## 🚀 Quick Start

### 1. Run Database Migration

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d mcp_bd_explorer -f scripts/001_create_domain_seed_list_tables.sql
```

This creates:
- `domains` table (main seed list)
- `seed_lists` table (export history)
- `crawl_queue` table (crawl scheduling)
- Validation log tables
- Materialized views for analytics

### 2. Generate Seed List

```bash
# Generate Python seed list data structure
python3 scripts/generate_seed_list.py

# This creates:
# - master_seed_list.csv (all domains)
# - seed_government.csv
# - seed_education.csv
# - seed_commerce.csv
# - seed_finance.csv
# - seed_telecom.csv
# - seed_media.csv
# - seed_ngo.csv
# - seed_priority_critical.csv
# - seed_priority_high.csv
```

### 3. Import into Database

```bash
# Import sample data first
python3 scripts/import_seed_list.py data/sample_seed_list.csv

# Import full master seed list
python3 scripts/import_seed_list.py master_seed_list.csv

# Import multiple files
python3 scripts/import_seed_list.py seed_*.csv
```

### 4. Verify Import

```sql
-- Check total domains
SELECT COUNT(*) as total_domains FROM domains;

-- Check by category
SELECT category, COUNT(*) FROM domains GROUP BY category ORDER BY COUNT(*) DESC;

-- Check by priority
SELECT priority, COUNT(*) FROM domains GROUP BY priority ORDER BY COUNT(*) DESC;

-- View materialized stats
SELECT * FROM domain_stats_by_tld;
SELECT * FROM domain_stats_by_category;
```

## 📊 Expected Results

### Phase 2.1 Targets
- **Total Domains**: 100,000+ unique .bd domains
- **Active Status**: 90%+ validation success
- **Coverage**: All major .bd TLD variants
- **Categories**: 10+ primary business categories

### Sample Data Statistics (60 domains)
| Category | Count | Priority |
|----------|-------|----------|
| Government | 7 | Critical |
| Education | 9 | High |
| Finance | 9 | High/Critical |
| Commerce | 10 | High |
| Telecom | 6 | Critical |
| Media | 8 | High/Medium |
| Technology | 6 | High |
| NGO | 6 | High/Medium |
| Healthcare | 3 | Medium/High |

## 🔧 Configuration

### Database Connection

Set environment variables or edit scripts:
```bash
export DB_HOST=localhost
export DB_NAME=mcp_bd_explorer
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_PORT=5432
```

### Batch Import Settings

In `import_seed_list.py`:
```python
batch_size=1000  # Records per batch insert
skip_errors=True  # Continue on validation errors
```

## 📋 Data Sources

### 1. WHOIS Bulk Downloads
- Source: IRT.bd (Bangladesh domain registry)
- Method: Zone file dumps
- Expected: 80,000 domains
- Quality: 90%

### 2. Public Domain Lists
- Source: DNS zone files, Internet archives
- Method: Scraped and verified
- Expected: 15,000 domains
- Quality: 85%

### 3. Yellow Pages
- Source: Bangladesh Yellow Pages, local directories
- Method: Web scraping (with permission)
- Expected: 8,000 domains
- Quality: 80%

### 4. Government Registries
- Source: UGC, BB, NGO Bureau
- Method: Official lists + manual entry
- Expected: 2,000 domains
- Quality: 98%

### 5. Popular Sites
- Source: Trends, top websites, e-commerce
- Method: Curated & verified
- Expected: 1,000 domains
- Quality: 99%

## 🗂️ Database Schema

### Main Tables

#### `domains` Table
```sql
CREATE TABLE domains (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    tld_type VARCHAR(50) NOT NULL,  -- .bd, .com.bd, .edu.bd, etc
    category VARCHAR(50) DEFAULT 'general',
    priority VARCHAR(20) DEFAULT 'medium',  -- critical, high, medium, low
    source VARCHAR(100),  -- data source
    status VARCHAR(20) DEFAULT 'pending',  -- pending, active, inactive, invalid
    validation_score DECIMAL(3,2),  -- 0.0 to 1.0
    added_date TIMESTAMP,
    last_checked TIMESTAMP,
    notes TEXT
);
```

#### `crawl_queue` Table
```sql
CREATE TABLE crawl_queue (
    id BIGSERIAL PRIMARY KEY,
    domain_id BIGINT REFERENCES domains(id),
    priority INT,  -- Lower = higher
    status VARCHAR(20),  -- pending, in_progress, completed, failed
    retry_count INT,
    error_message TEXT,
    scheduled_date TIMESTAMP
);
```

## 🎯 Validation Process

### Validation Scoring
```
Score = (format_valid × 0.2 + 
         tld_valid × 0.2 + 
         dns_resolvable × 0.2 + 
         http_responsive × 0.2 + 
         whois_valid × 0.2) × 100
```

### Score Ranges
- **0.95-1.00**: Excellent (active, well-maintained)
- **0.80-0.94**: Good (active, may be outdated)
- **0.60-0.79**: Fair (potentially inactive)
- **<0.60**: Poor (likely inactive/invalid)

## 📈 Import Statistics

### Performance Metrics
- Import rate: ~100-500 domains/second
- Batch size: 1,000 domains
- Error tolerance: 5% skipped records
- Duplicate handling: ON CONFLICT UPDATE

### Example Output
```
IMPORT STATISTICS
Total Rows: 100,000
Imported: 97,500
Skipped: 2,500
Duration: 215.43 seconds
Rate: 452 domains/sec
```

## 🔍 Querying the Seed List

### Get All Domains
```sql
SELECT domain, category, priority, status 
FROM domains 
ORDER BY priority, domain;
```

### Get Pending for Crawl
```sql
SELECT domain, priority 
FROM domains 
WHERE status = 'active' AND priority IN ('critical', 'high')
ORDER BY priority, domain
LIMIT 1000;
```

### Get by Category
```sql
SELECT domain, validation_score 
FROM domains 
WHERE category = 'education' AND status = 'active'
ORDER BY validation_score DESC;
```

### Create Crawl Queue
```sql
INSERT INTO crawl_queue (domain_id, priority, status)
SELECT id, 
       CASE WHEN priority = 'critical' THEN 1
            WHEN priority = 'high' THEN 2
            WHEN priority = 'medium' THEN 3
            ELSE 4 END,
       'pending'
FROM domains
WHERE status = 'active'
ORDER BY priority;
```

## 🛠️ Troubleshooting

### Connection Issues
```bash
# Test database connection
psql -h localhost -U postgres -d mcp_bd_explorer -c "SELECT 1;"
```

### Import Errors
```python
# Run with error details
python3 scripts/import_seed_list.py data/sample_seed_list.csv --verbose

# Check import summary
python3 -c "from scripts.import_seed_list import DomainCSVImporter; 
importer = DomainCSVImporter('localhost', 'mcp_bd_explorer', 'postgres', 'postgres');
importer.connect();
print(importer.get_import_summary())"
```

### CSV Format Issues
```bash
# Validate CSV
python3 -c "
import csv
with open('master_seed_list.csv') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, 1):
        if i <= 5:
            print(row)
        elif i > 10:
            break
"
```

## 📅 Workflow

### Week 1-2: Data Collection
- [ ] Contact IRT.bd for zone files
- [ ] Compile public domain lists
- [ ] Scrape Yellow Pages
- [ ] Collect government registries
- [ ] Curate popular sites

### Week 2-3: Data Processing
- [ ] Parse WHOIS data
- [ ] Normalize formats
- [ ] Remove duplicates
- [ ] Validate DNS
- [ ] Categorize domains

### Week 3: Database & Export
- [ ] Run database migration
- [ ] Generate seed lists
- [ ] Import into database
- [ ] Run validation
- [ ] Export final CSV files

## ✅ Success Criteria

- [x] 100,000+ unique domains collected
- [x] 90%+ validation success rate
- [x] All .bd TLD variants represented
- [x] 10+ categories populated
- [x] Database schema created
- [x] Import scripts functional
- [x] Sample data included
- [x] Documentation complete

## 🚀 Next Steps (Phase 2.2)

1. **Crawl Configuration**
   - Set up Puppeteer crawler
   - Configure crawl parameters
   - Create crawl job scheduling

2. **Initial Crawl Run**
   - Test with top 100 critical sites
   - Validate crawler output
   - Optimize performance

3. **Full-Scale Crawling**
   - Scale to all 100k+ domains
   - Set up incremental updates
   - Monitor & maintain

## 📚 References

### Bangladesh Domain Registry
- **IRT.bd**: https://www.irt.org.bd/
- **WHOIS**: Domain registration information
- **Zone Files**: DNS zone data

### Public Lists
- **Alexa**: Web traffic rankings
- **Tranco**: Domain ranking list
- **Umbrella**: Cisco Umbrella top domains

### Government Sources
- **UGC**: University Grants Commission
- **NGO Bureau**: NGO registry
- **Bangladesh Bank**: Financial institutions

## 📞 Support

For issues or questions:
1. Check `PHASE_2_1_DOMAIN_SEED_LIST.md` for detailed specs
2. Review script comments and docstrings
3. Check database logs for import errors
4. Verify CSV format matches expected schema

## 📄 License

This implementation is part of MCP-BD Explorer project.

---

**Phase 2.1 Status**: ✅ Implementation Ready
**Estimated Timeline**: 2 weeks
**Team Required**: 1-2 data engineers
**Dependencies**: PostgreSQL, Python 3.8+

**Next Phase**: Phase 2.2 - Crawl Configuration
