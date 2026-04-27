# Phase 2.1: Domain Seed List Generation

## Overview
This document describes the implementation of domain seed list generation for MCP-BD Explorer, including sources, methods, and data structures.

## Sources & Methods

### 1. TLD Variants (.bd domains)
Primary domains using Bangladesh country code TLD:
- `.com.bd` - Commercial
- `.org.bd` - Non-profit organizations
- `.edu.bd` - Educational institutions
- `.gov.bd` - Government entities
- `.net.bd` - Network providers
- `.ac.bd` - Academic institutions
- `.bd` - Generic Bangladesh domain
- `.biz.bd` - Business
- `.mobi.bd` - Mobile services
- `.info.bd` - Information services

### 2. Data Sources

#### A. WHOIS Bulk Downloads
- **Source**: IRT.bd (Bangladesh domain registry)
- **Format**: Zone file dump (if available)
- **Frequency**: Monthly
- **Method**: Automated WHOIS bulk query
- **Expected Domains**: 50,000-150,000

#### B. Public Domain Lists
- **Source 1**: Zone files from DNS providers
- **Source 2**: Common crawls and Internet archives
- **Source 3**: Alexa top sites (Bangladesh segment)
- **Format**: CSV/TXT lists
- **Processing**: Deduplication & validation

#### C. Bangladesh Yellow Pages
- **Source**: Local business directories
- **Data**: Company names → domain inference
- **Method**: Web scraping (with permission)
- **Expected Coverage**: 5,000-10,000 businesses

#### D. Government Registries
- **Banks**: BB (Bangladesh Bank) list
- **Universities**: UGC (University Grants Commission) list
- **NGOs**: NGO Bureau registry
- **Government**: Ministry websites
- **Expected Domains**: 1,000-2,000

#### E. Popular Local Domains (Trends)
- **Google Trends**: Search trends in Bangladesh
- **Top websites**: NewsGuard, local news sites
- **Social media**: Facebook pages, YouTube channels with .bd domains
- **E-commerce**: Daraz, Robi, Grameenphone, etc.
- **Expected Domains**: 500-1,000

#### F. Manual Entry & Crowdsourcing
- **Admin entry**: Manual addition of known domains
- **Community**: User-submitted domains
- **Import**: Bulk CSV upload
- **Expected Domains**: Growing as needed

### 3. Seed List Structure

```csv
domain,tld_type,source,category,priority,added_date,notes
example.com.bd,commercial,whois_bulk,general,high,2026-02-06,Zone file dump
diu.edu.bd,academic,government_registry,education,high,2026-02-06,DIU official
bbtc.org.bd,nonprofit,government_registry,ngo,high,2026-02-06,NGO Bureau
daraz.com.bd,ecommerce,popular_sites,commerce,high,2026-02-06,Top e-commerce
```

### 4. Category Classifications

**Primary Categories:**
- `government` - Government agencies
- `education` - Universities & schools
- `healthcare` - Hospitals & clinics
- `finance` - Banks & financial institutions
- `commerce` - E-commerce & retail
- `media` - News, media, entertainment
- `telecom` - Telecommunications
- `ngo` - Non-profit organizations
- `technology` - IT & software companies
- `general` - Uncategorized/general

**Priority Levels:**
- `critical` - Strategic importance (government, major universities)
- `high` - Significant coverage (popular sites, major businesses)
- `medium` - Standard coverage (typical businesses)
- `low` - Optional coverage (small sites)

## Master Seed List Targets

### Phase 2.1 Initial Targets
- **Total Domains**: 100,000+ unique domains
- **Quality Threshold**: 95% active/valid
- **Coverage**: Minimum 50% of .bd domain space

### Breakdown by Source:
| Source | Target Count | Quality | Effort |
|--------|--------------|---------|--------|
| WHOIS Bulk | 80,000 | 90% | Automated |
| Public Lists | 15,000 | 85% | Scraped |
| Yellow Pages | 8,000 | 80% | Scraped |
| Gov Registry | 2,000 | 98% | Manual/API |
| Popular Sites | 1,000 | 99% | Curated |
| Manual Entry | 5,000 | 100% | Manual |
| **TOTAL** | **111,000** | **92%** | Mixed |

## Implementation Plan

### Step 1: Data Collection (Week 1-2)
- [ ] Contact IRT.bd for zone file access
- [ ] Compile public domain lists
- [ ] Scrape Bangladesh Yellow Pages
- [ ] Collect government registries
- [ ] Identify popular .bd domains

### Step 2: Data Processing (Week 2-3)
- [ ] Parse WHOIS data
- [ ] Normalize domain formats
- [ ] Remove duplicates
- [ ] Validate DNS records
- [ ] Categorize domains

### Step 3: Database Import (Week 3)
- [ ] Create `domains` table schema
- [ ] Bulk import validated domains
- [ ] Index for performance
- [ ] Quality validation

### Step 4: Seed List Export (Week 3)
- [ ] Generate master CSV
- [ ] Create priority-filtered lists
- [ ] Export by category
- [ ] Version control seed list

## Database Schema

### `domains` Table
```sql
CREATE TABLE domains (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    tld_type VARCHAR(50),
    category VARCHAR(50),
    priority VARCHAR(20),
    source VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, active, inactive, invalid
    added_date TIMESTAMP DEFAULT NOW(),
    last_checked TIMESTAMP,
    validation_score DECIMAL(3,2),
    notes TEXT,
    INDEX idx_domain (domain),
    INDEX idx_category (category),
    INDEX idx_priority (priority),
    INDEX idx_status (status)
);
```

### `seed_lists` Table
```sql
CREATE TABLE seed_lists (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    total_domains INT,
    active_domains INT,
    quality_score DECIMAL(3,2),
    created_date TIMESTAMP DEFAULT NOW(),
    exported_date TIMESTAMP,
    file_path VARCHAR(255)
);
```

## CSV File Format

### Master Seed List (master_seed_list.csv)
```csv
domain,tld_type,category,priority,source,status,validation_score,notes
example.com.bd,commercial,general,high,whois_bulk,active,0.95,"Zone file dump, 2026-02-06"
diu.edu.bd,academic,education,critical,gov_registry,active,0.98,"Verified university domain"
```

### Category-Filtered Lists
- `seed_government.csv` - Government only
- `seed_education.csv` - Education only
- `seed_commerce.csv` - E-commerce only
- `seed_priority_critical.csv` - Critical sites only
- `seed_priority_high.csv` - Priority high+

## Validation Process

### Domain Validation Checks
1. **Format Validation**: Proper domain syntax
2. **TLD Validation**: Correct .bd variant
3. **DNS Resolution**: A/MX records exist
4. **HTTP Check**: Website responsive
5. **Whois Lookup**: Registered & valid

### Validation Scoring
```
score = (
    format_valid * 0.2 +      # 20%
    tld_valid * 0.2 +         # 20%
    dns_resolvable * 0.2 +    # 20%
    http_responsive * 0.2 +   # 20%
    whois_valid * 0.2         # 20%
) * 100
```

Score Range:
- 0.95-1.00: Excellent (active, well-maintained)
- 0.80-0.94: Good (active, may be outdated)
- 0.60-0.79: Fair (potentially inactive)
- <0.60: Poor (likely inactive/invalid)

## Seed List Management

### Version Control
- `master_seed_list_v1.0.csv` - Initial list (100k+)
- `master_seed_list_v1.1.csv` - Updates from validation
- `master_seed_list_v1.2.csv` - Quarterly refresh
- Tag format: `seed_list_YYYYMMDDvX.Y`

### Update Frequency
- **Daily**: Add newly discovered domains
- **Weekly**: Remove inactive domains
- **Monthly**: Full validation sweep
- **Quarterly**: WHOIS bulk re-download
- **Yearly**: Comprehensive refresh

## Output Deliverables

### Phase 2.1 Completion Checklist
- [ ] Master seed list (100k+ domains)
- [ ] Master seed list CSV file
- [ ] Category-filtered seed lists (10 files)
- [ ] Priority-filtered seed lists (4 files)
- [ ] Database with `domains` table populated
- [ ] Validation report (quality metrics)
- [ ] Source documentation
- [ ] Import scripts & procedures
- [ ] Update procedures documented

### Files Generated
1. `master_seed_list.csv` - Complete list
2. `seed_government.csv` - Government domains only
3. `seed_education.csv` - Educational institutions
4. `seed_commerce.csv` - E-commerce sites
5. `seed_finance.csv` - Banks & financial
6. `seed_telecom.csv` - Telecom companies
7. `seed_media.csv` - News & media
8. `seed_ngo.csv` - NGO domains
9. `seed_priority_critical.csv` - Critical sites
10. `seed_priority_high.csv` - High priority sites

## Success Criteria

### Quality Metrics
- ✅ At least 100,000 unique domains collected
- ✅ Minimum 90% validation score
- ✅ Coverage of all major .bd TLDs
- ✅ All categories represented
- ✅ Priority levels assigned
- ✅ CSV files generated and verified

### Coverage Targets
- ✅ 80% of estimated .bd domain space (500k total)
- ✅ 95%+ coverage of government domains
- ✅ 90%+ coverage of educational institutions
- ✅ 85%+ coverage of major businesses
- ✅ 70%+ coverage of SMEs

### Performance Targets
- ✅ Data collection < 1 week
- ✅ Processing & validation < 1 week
- ✅ Database import < 1 hour
- ✅ List generation < 30 minutes
- ✅ Query performance < 100ms

## Risk Mitigation

### Technical Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|------------|-----------|
| WHOIS data incomplete | Coverage gap | Medium | Use multiple sources |
| DNS validation slow | Timeline impact | High | Batch processing, async |
| Duplicate domains | Data quality | Medium | Deduplication algorithm |
| Invalid categories | Manual work | Low | Review & approve |

### Operational Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|------------|-----------|
| Website blocking crawlers | Data gap | Medium | Respect robots.txt |
| Rate limiting | Slow progress | High | Implement throttling |
| Data licensing | Legal issue | Low | Verify permissions |
| Service unavailable | Blocked | Low | Retry mechanism |

## Next Steps (Phase 2.2)

After completing domain seed list:
1. **Phase 2.2**: Crawl Configuration
   - Set up Puppeteer crawler
   - Configure crawl parameters
   - Create crawl jobs from seed list
   
2. **Phase 2.3**: Initial Crawl Run
   - Execute crawl on top 1,000 domains
   - Validate results
   - Optimize crawler performance

3. **Phase 2.4**: Full-Scale Crawling
   - Scale to all 100k+ domains
   - Set up incremental updates
   - Monitor & maintain

## References

- **IRT.bd**: https://www.irt.org.bd/ (Bangladesh domain registry)
- **WHOIS Lookup**: Domain registration database
- **Bangladesh Yellow Pages**: Local business directory
- **UGC**: University Grants Commission of Bangladesh
- **NGO Bureau**: NGO registration authority

---

**Phase 2.1 Status**: Ready for implementation
**Expected Completion**: End of Week 2
**Team Required**: 1-2 data engineers
**Resources**: Automated scripts + manual review
