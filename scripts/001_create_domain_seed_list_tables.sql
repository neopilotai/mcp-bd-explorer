-- Migration: Create Domain Seed List Tables
-- Version: 001
-- Description: Create tables for managing .bd domain seed lists

-- Create domains table
CREATE TABLE domains (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    tld_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    priority VARCHAR(20) DEFAULT 'medium',
    source VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    added_date TIMESTAMP DEFAULT NOW(),
    last_checked TIMESTAMP,
    last_updated TIMESTAMP DEFAULT NOW(),
    validation_score DECIMAL(3,2) DEFAULT 0.00,
    http_status INT,
    dns_resolves BOOLEAN,
    notes TEXT,
    
    -- Constraints
    CONSTRAINT valid_tld CHECK (tld_type IN (
        'bd', 'com.bd', 'org.bd', 'edu.bd', 'gov.bd', 
        'net.bd', 'ac.bd', 'biz.bd', 'mobi.bd', 'info.bd'
    )),
    CONSTRAINT valid_category CHECK (category IN (
        'government', 'education', 'healthcare', 'finance', 'commerce',
        'media', 'telecom', 'ngo', 'technology', 'general'
    )),
    CONSTRAINT valid_priority CHECK (priority IN (
        'critical', 'high', 'medium', 'low'
    )),
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'active', 'inactive', 'invalid'
    )),
    CONSTRAINT valid_source CHECK (source IN (
        'whois_bulk', 'public_list', 'yellow_pages', 'gov_registry', 'popular_sites', 'manual_entry'
    )),
    CONSTRAINT valid_score CHECK (validation_score >= 0 AND validation_score <= 1)
);

-- Create indexes for performance
CREATE INDEX idx_domains_domain ON domains(domain);
CREATE INDEX idx_domains_category ON domains(category);
CREATE INDEX idx_domains_priority ON domains(priority);
CREATE INDEX idx_domains_status ON domains(status);
CREATE INDEX idx_domains_tld_type ON domains(tld_type);
CREATE INDEX idx_domains_source ON domains(source);
CREATE INDEX idx_domains_validation_score ON domains(validation_score DESC);
CREATE INDEX idx_domains_added_date ON domains(added_date DESC);

-- Create seed_lists table to track exported lists
CREATE TABLE seed_lists (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    total_domains INT,
    active_domains INT,
    quality_score DECIMAL(3,2),
    filters_applied TEXT, -- JSON of applied filters
    created_date TIMESTAMP DEFAULT NOW(),
    exported_date TIMESTAMP,
    file_path VARCHAR(255),
    file_size_kb INT,
    checksum VARCHAR(64) -- SHA256 checksum for verification
);

-- Create index for seed list lookups
CREATE INDEX idx_seed_lists_created ON seed_lists(created_date DESC);
CREATE INDEX idx_seed_lists_name ON seed_lists(name);

-- Create crawl_queue table to track domains to crawl
CREATE TABLE crawl_queue (
    id BIGSERIAL PRIMARY KEY,
    domain_id BIGINT NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    priority INT DEFAULT 100, -- Lower = higher priority
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, failed
    scheduled_date TIMESTAMP,
    started_date TIMESTAMP,
    completed_date TIMESTAMP,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    error_message TEXT,
    result_metadata JSONB, -- Store crawl results metadata
    created_date TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_crawl_status CHECK (status IN (
        'pending', 'in_progress', 'completed', 'failed', 'skipped'
    )),
    CONSTRAINT valid_priority CHECK (priority >= 0 AND priority <= 1000)
);

-- Create indexes for crawl queue
CREATE INDEX idx_crawl_queue_status ON crawl_queue(status);
CREATE INDEX idx_crawl_queue_priority ON crawl_queue(priority ASC, created_date ASC);
CREATE INDEX idx_crawl_queue_domain_id ON crawl_queue(domain_id);
CREATE INDEX idx_crawl_queue_scheduled ON crawl_queue(scheduled_date) WHERE status = 'pending';

-- Create domain_validation_log table for tracking validation history
CREATE TABLE domain_validation_log (
    id BIGSERIAL PRIMARY KEY,
    domain_id BIGINT NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    validation_date TIMESTAMP DEFAULT NOW(),
    format_valid BOOLEAN,
    tld_valid BOOLEAN,
    dns_resolvable BOOLEAN,
    http_responsive BOOLEAN,
    http_status_code INT,
    whois_valid BOOLEAN,
    validation_score DECIMAL(3,2),
    notes TEXT
);

-- Create index for validation logs
CREATE INDEX idx_validation_log_domain_id ON domain_validation_log(domain_id);
CREATE INDEX idx_validation_log_date ON domain_validation_log(validation_date DESC);

-- Create seed_list_export_history table to track exports
CREATE TABLE seed_list_export_history (
    id BIGSERIAL PRIMARY KEY,
    seed_list_id BIGINT REFERENCES seed_lists(id) ON DELETE SET NULL,
    exported_by VARCHAR(255),
    export_date TIMESTAMP DEFAULT NOW(),
    category_filter VARCHAR(50),
    priority_filter VARCHAR(20),
    status_filter VARCHAR(20),
    total_records INT,
    export_path VARCHAR(255),
    export_format VARCHAR(20) -- csv, json, sql
);

-- Create index for export history
CREATE INDEX idx_export_history_date ON seed_list_export_history(export_date DESC);

-- Create domain_sources table to track domain sources more granularly
CREATE TABLE domain_sources (
    id BIGSERIAL PRIMARY KEY,
    domain_id BIGINT NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    source_name VARCHAR(100) NOT NULL,
    source_date TIMESTAMP,
    source_confidence DECIMAL(3,2),
    additional_data JSONB
);

-- Create index for source tracking
CREATE INDEX idx_domain_sources_domain_id ON domain_sources(domain_id);
CREATE INDEX idx_domain_sources_source ON domain_sources(source_name);

-- Create materialized views for quick aggregations
CREATE MATERIALIZED VIEW domain_stats_by_tld AS
SELECT 
    tld_type,
    COUNT(*) as total_domains,
    COUNT(*) FILTER (WHERE status = 'active') as active_domains,
    COUNT(*) FILTER (WHERE validation_score >= 0.9) as high_quality,
    AVG(validation_score) as avg_validation_score,
    MAX(last_checked) as last_check_date
FROM domains
GROUP BY tld_type;

CREATE INDEX idx_domain_stats_tld ON domain_stats_by_tld(tld_type);

-- Create materialized view for category statistics
CREATE MATERIALIZED VIEW domain_stats_by_category AS
SELECT 
    category,
    COUNT(*) as total_domains,
    COUNT(*) FILTER (WHERE status = 'active') as active_domains,
    COUNT(*) FILTER (WHERE priority = 'critical') as critical_count,
    COUNT(*) FILTER (WHERE priority = 'high') as high_count,
    AVG(validation_score) as avg_validation_score,
    MAX(last_checked) as last_check_date
FROM domains
GROUP BY category;

CREATE INDEX idx_domain_stats_category ON domain_stats_by_category(category);

-- Create function to update last_updated timestamp
CREATE OR REPLACE FUNCTION update_last_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for domains table
CREATE TRIGGER update_domains_last_updated
BEFORE UPDATE ON domains
FOR EACH ROW
EXECUTE FUNCTION update_last_updated_column();

-- Grant permissions (adjust as needed for your database user)
-- GRANT SELECT, INSERT, UPDATE ON domains TO crawler_user;
-- GRANT SELECT, INSERT, UPDATE ON crawl_queue TO crawler_user;
-- GRANT SELECT ON domain_stats_by_tld TO app_user;
-- GRANT SELECT ON domain_stats_by_category TO app_user;

-- Seed initial critical domains (optional)
INSERT INTO domains (domain, tld_type, category, priority, source, status, validation_score, notes) VALUES
    ('www.gov.bd', 'bd', 'government', 'critical', 'gov_registry', 'active', 0.98, 'Main government portal'),
    ('bb.org.bd', 'org.bd', 'finance', 'critical', 'gov_registry', 'active', 0.98, 'Bangladesh Bank (Central Bank)'),
    ('daraz.com.bd', 'com.bd', 'commerce', 'critical', 'popular_sites', 'active', 0.98, 'Major e-commerce platform'),
    ('du.ac.bd', 'ac.bd', 'education', 'high', 'gov_registry', 'active', 0.97, 'University of Dhaka'),
    ('buet.ac.bd', 'ac.bd', 'education', 'high', 'gov_registry', 'active', 0.97, 'BUET')
ON CONFLICT (domain) DO NOTHING;

-- Add initial record to seed_lists tracking
INSERT INTO seed_lists (name, description, total_domains, active_domains, created_date) VALUES
    ('Initial Seed List', 'Phase 2.1 initial domain collection', 0, 0, NOW())
ON CONFLICT DO NOTHING;

-- Display table summaries
\echo 'Migration completed successfully!'
\echo 'Created tables:'
\echo '  - domains'
\echo '  - seed_lists'
\echo '  - crawl_queue'
\echo '  - domain_validation_log'
\echo '  - seed_list_export_history'
\echo '  - domain_sources'
\echo 'Created materialized views:'
\echo '  - domain_stats_by_tld'
\echo '  - domain_stats_by_category'
