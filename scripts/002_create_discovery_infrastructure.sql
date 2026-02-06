-- Phase 2.2 Database Schema: Discovery Infrastructure
-- Automated Crawling & Discovery Tables and Indexes
-- Date: 2026-02-06

-- ============================================================
-- TABLE: discovery_sources
-- Purpose: Track all discovery sources and their configuration
-- ============================================================

CREATE TABLE IF NOT EXISTS discovery_sources (
  id BIGSERIAL PRIMARY KEY,
  source_name VARCHAR(50) NOT NULL UNIQUE,
  source_type VARCHAR(50) NOT NULL, -- ct_logs, dns, archive, search, etc
  api_endpoint TEXT,
  credentials_key VARCHAR(100),
  is_active BOOLEAN DEFAULT true,
  query_frequency VARCHAR(20), -- hourly, daily, weekly
  rate_limit_per_hour INT DEFAULT 1000,
  last_query_time TIMESTAMP,
  last_query_status VARCHAR(20), -- success, partial, failed
  domains_discovered INT DEFAULT 0,
  quality_score DECIMAL(3,2) DEFAULT 0.80,
  reliability_score DECIMAL(3,2) DEFAULT 0.90,
  config_json JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: domain_discovery_log
-- Purpose: Log of all discovered domains with metadata
-- ============================================================

CREATE TABLE IF NOT EXISTS domain_discovery_log (
  id BIGSERIAL PRIMARY KEY,
  domain_name VARCHAR(255) NOT NULL,
  source_id BIGINT REFERENCES discovery_sources(id),
  discovery_date TIMESTAMP DEFAULT NOW(),
  confidence_score DECIMAL(3,2),
  validation_status VARCHAR(20), -- pending, valid, invalid, duplicate, low_quality
  format_valid BOOLEAN,
  dns_resolvable BOOLEAN,
  http_reachable BOOLEAN,
  tld_valid BOOLEAN,
  category VARCHAR(50),
  first_seen TIMESTAMP,
  last_verified TIMESTAMP,
  quality_metrics JSONB DEFAULT '{}',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(domain_name, source_id)
);

-- ============================================================
-- TABLE: domain_quality_scores
-- Purpose: Detailed quality scoring for domains
-- ============================================================

CREATE TABLE IF NOT EXISTS domain_quality_scores (
  id BIGSERIAL PRIMARY KEY,
  domain_name VARCHAR(255) NOT NULL REFERENCES domain_discovery_log(domain_name),
  format_score DECIMAL(3,2),
  dns_score DECIMAL(3,2),
  http_score DECIMAL(3,2),
  whois_score DECIMAL(3,2),
  ssl_score DECIMAL(3,2),
  composite_score DECIMAL(3,2),
  confidence_level VARCHAR(20), -- very_high, high, medium, low
  last_check TIMESTAMP,
  check_count INT DEFAULT 0,
  scoring_method VARCHAR(50), -- composite, weighted, manual, etc
  scoring_config JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: crawl_jobs
-- Purpose: Track discovery crawl jobs and their results
-- ============================================================

CREATE TABLE IF NOT EXISTS crawl_jobs (
  id BIGSERIAL PRIMARY KEY,
  job_name VARCHAR(100) NOT NULL,
  job_type VARCHAR(50), -- discovery, validation, scoring, dedup
  source_id BIGINT REFERENCES discovery_sources(id),
  status VARCHAR(20), -- pending, running, completed, failed, paused
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  duration_seconds INT,
  domains_found INT DEFAULT 0,
  domains_validated INT DEFAULT 0,
  domains_imported INT DEFAULT 0,
  duplicates_removed INT DEFAULT 0,
  errors_count INT DEFAULT 0,
  warnings_count INT DEFAULT 0,
  job_config JSONB,
  results_summary JSONB,
  error_log TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: deduplication_matches
-- Purpose: Track duplicate domain matches
-- ============================================================

CREATE TABLE IF NOT EXISTS deduplication_matches (
  id BIGSERIAL PRIMARY KEY,
  primary_domain VARCHAR(255) NOT NULL,
  duplicate_domain VARCHAR(255) NOT NULL,
  match_type VARCHAR(20), -- exact, fuzzy, normalization, etc
  similarity_score DECIMAL(3,2),
  primary_source VARCHAR(50),
  duplicate_source VARCHAR(50),
  resolved_to VARCHAR(255), -- final domain after resolution
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: discovery_statistics
-- Purpose: Aggregate statistics for discovery pipeline
-- ============================================================

CREATE TABLE IF NOT EXISTS discovery_statistics (
  id BIGSERIAL PRIMARY KEY,
  stat_date DATE NOT NULL UNIQUE,
  total_discovered INT,
  total_valid INT,
  total_invalid INT,
  total_duplicates INT,
  avg_confidence_score DECIMAL(3,2),
  sources_active INT,
  domains_in_db INT,
  processing_time_seconds INT,
  cpu_usage_percent DECIMAL(5,2),
  memory_usage_mb INT,
  database_size_mb INT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES for Performance
-- ============================================================

-- Discovery sources
CREATE INDEX idx_discovery_source_name ON discovery_sources(source_name);
CREATE INDEX idx_discovery_source_active ON discovery_sources(is_active);
CREATE INDEX idx_discovery_source_type ON discovery_sources(source_type);

-- Domain discovery log
CREATE INDEX idx_domain_discovery_date ON domain_discovery_log(discovery_date);
CREATE INDEX idx_domain_discovery_domain ON domain_discovery_log(domain_name);
CREATE INDEX idx_domain_discovery_source ON domain_discovery_log(source_id);
CREATE INDEX idx_domain_discovery_status ON domain_discovery_log(validation_status);
CREATE INDEX idx_domain_discovery_confidence ON domain_discovery_log(confidence_score);
CREATE INDEX idx_domain_discovery_verified ON domain_discovery_log(last_verified);

-- Domain quality scores
CREATE INDEX idx_quality_domain ON domain_quality_scores(domain_name);
CREATE INDEX idx_quality_composite ON domain_quality_scores(composite_score);
CREATE INDEX idx_quality_level ON domain_quality_scores(confidence_level);
CREATE INDEX idx_quality_check ON domain_quality_scores(last_check);

-- Crawl jobs
CREATE INDEX idx_crawl_job_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_job_type ON crawl_jobs(job_type);
CREATE INDEX idx_crawl_job_source ON crawl_jobs(source_id);
CREATE INDEX idx_crawl_job_date ON crawl_jobs(start_time);

-- Deduplication
CREATE INDEX idx_dedup_primary ON deduplication_matches(primary_domain);
CREATE INDEX idx_dedup_duplicate ON deduplication_matches(duplicate_domain);

-- Statistics
CREATE INDEX idx_stats_date ON discovery_statistics(stat_date);

-- ============================================================
-- MATERIALIZED VIEWS for Analytics
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS discovery_summary_by_source AS
SELECT 
  ds.source_name,
  ds.source_type,
  COUNT(DISTINCT ddl.domain_name) as domains_discovered,
  COUNT(CASE WHEN ddl.validation_status = 'valid' THEN 1 END) as domains_valid,
  COUNT(CASE WHEN ddl.validation_status = 'invalid' THEN 1 END) as domains_invalid,
  AVG(ddl.confidence_score) as avg_confidence,
  MAX(ddl.discovery_date) as last_discovery,
  ds.quality_score,
  ds.reliability_score
FROM discovery_sources ds
LEFT JOIN domain_discovery_log ddl ON ds.id = ddl.source_id
WHERE ds.is_active = true
GROUP BY ds.id, ds.source_name, ds.source_type, ds.quality_score, ds.reliability_score;

CREATE INDEX idx_view_summary_source ON discovery_summary_by_source(source_name);

CREATE MATERIALIZED VIEW IF NOT EXISTS quality_distribution AS
SELECT 
  CASE 
    WHEN dqs.composite_score >= 0.95 THEN 'Very High (95-100%)'
    WHEN dqs.composite_score >= 0.85 THEN 'High (85-95%)'
    WHEN dqs.composite_score >= 0.70 THEN 'Medium (70-85%)'
    ELSE 'Low (<70%)'
  END as quality_level,
  COUNT(*) as domain_count,
  AVG(dqs.composite_score) as avg_score,
  MIN(dqs.composite_score) as min_score,
  MAX(dqs.composite_score) as max_score
FROM domain_quality_scores dqs
GROUP BY quality_level;

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Update timestamp on discovery_sources
CREATE OR REPLACE FUNCTION update_discovery_sources_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER discovery_sources_update_timestamp
  BEFORE UPDATE ON discovery_sources
  FOR EACH ROW
  EXECUTE FUNCTION update_discovery_sources_timestamp();

-- Update timestamp on domain_discovery_log
CREATE OR REPLACE FUNCTION update_discovery_log_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER discovery_log_update_timestamp
  BEFORE UPDATE ON domain_discovery_log
  FOR EACH ROW
  EXECUTE FUNCTION update_discovery_log_timestamp();

-- ============================================================
-- SAMPLE DATA - Discovery Sources
-- ============================================================

INSERT INTO discovery_sources 
  (source_name, source_type, api_endpoint, query_frequency, rate_limit_per_hour, quality_score, reliability_score, config_json)
VALUES 
  ('Google CT Log', 'ct_logs', 'https://ct.googleapis.com/log', 'hourly', 1000, 0.95, 0.99, '{"providers": ["google"], "batch_size": 500}'),
  ('DigiCert CT Log', 'ct_logs', 'https://log.digicert.com/log', 'hourly', 1000, 0.94, 0.98, '{"providers": ["digicert"], "batch_size": 500}'),
  ('DNS Discovery', 'dns_discovery', NULL, 'daily', 500, 0.92, 0.95, '{"methods": ["reverse_dns", "zone_transfer", "ns_enum"]}'),
  ('Archive.org', 'web_archive', 'https://archive.org/advancedsearch.php', 'daily', 100, 0.75, 0.98, '{"batch_size": 100, "crawl_delay": 1}'),
  ('Security Tools', 'subdomain_enum', NULL, 'daily', 200, 0.70, 0.85, '{"tools": ["ct_mining", "dns_brute", "dorking"]}')
ON CONFLICT (source_name) DO NOTHING;

-- ============================================================
-- SAMPLE DATA - Crawl Jobs
-- ============================================================

INSERT INTO crawl_jobs 
  (job_name, job_type, source_id, status, start_time, end_time, duration_seconds, domains_found, domains_validated, domains_imported, duplicates_removed, errors_count)
VALUES 
  (
    'Initial CT Log Discovery',
    'discovery',
    (SELECT id FROM discovery_sources WHERE source_name = 'Google CT Log' LIMIT 1),
    'completed',
    NOW() - INTERVAL '2 hours',
    NOW() - INTERVAL '1.5 hours',
    1800,
    15000,
    14800,
    14500,
    300,
    5
  )
ON CONFLICT DO NOTHING;

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

-- Get discovery summary
CREATE OR REPLACE FUNCTION get_discovery_summary()
RETURNS TABLE (
  total_domains BIGINT,
  valid_domains BIGINT,
  invalid_domains BIGINT,
  avg_confidence DECIMAL,
  active_sources BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    COUNT(DISTINCT ddl.domain_name),
    COUNT(CASE WHEN ddl.validation_status = 'valid' THEN 1 END),
    COUNT(CASE WHEN ddl.validation_status = 'invalid' THEN 1 END),
    AVG(ddl.confidence_score),
    COUNT(DISTINCT ds.id)
  FROM domain_discovery_log ddl
  LEFT JOIN discovery_sources ds ON ddl.source_id = ds.id
  WHERE ds.is_active = true;
END;
$$ LANGUAGE plpgsql;

-- Get domains by quality level
CREATE OR REPLACE FUNCTION get_domains_by_quality(quality_threshold DECIMAL DEFAULT 0.70)
RETURNS TABLE (
  domain_name VARCHAR,
  quality_score DECIMAL,
  quality_level VARCHAR,
  source VARCHAR,
  last_verified TIMESTAMP
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ddl.domain_name,
    dqs.composite_score,
    dqs.confidence_level,
    ds.source_name,
    ddl.last_verified
  FROM domain_discovery_log ddl
  LEFT JOIN domain_quality_scores dqs ON ddl.domain_name = dqs.domain_name
  LEFT JOIN discovery_sources ds ON ddl.source_id = ds.id
  WHERE dqs.composite_score >= quality_threshold
  ORDER BY dqs.composite_score DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- GRANTS
-- ============================================================

-- Grant permissions to crawler user
GRANT SELECT, INSERT, UPDATE ON discovery_sources TO crawler_user;
GRANT SELECT, INSERT, UPDATE ON domain_discovery_log TO crawler_user;
GRANT SELECT, INSERT, UPDATE ON domain_quality_scores TO crawler_user;
GRANT SELECT, INSERT, UPDATE ON crawl_jobs TO crawler_user;
GRANT SELECT, INSERT, UPDATE ON deduplication_matches TO crawler_user;
GRANT SELECT, INSERT, UPDATE ON discovery_statistics TO crawler_user;

-- ============================================================
-- COMPLETION
-- ============================================================

-- Record schema creation
INSERT INTO discovery_statistics (stat_date, sources_active)
VALUES (CURRENT_DATE, (SELECT COUNT(*) FROM discovery_sources WHERE is_active = true))
ON CONFLICT (stat_date) DO UPDATE SET sources_active = EXCLUDED.sources_active;

-- Verify tables created
SELECT 
  'discovery_sources' as table_name,
  COUNT(*) as row_count
FROM discovery_sources
UNION ALL
SELECT 
  'domain_discovery_log',
  COUNT(*)
FROM domain_discovery_log
UNION ALL
SELECT 
  'discovery_statistics',
  COUNT(*)
FROM discovery_statistics;

-- ============================================================
-- End of Phase 2.2 Database Schema
-- ============================================================
