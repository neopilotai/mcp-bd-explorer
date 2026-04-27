-- Database migration for Phase 2.3: Deep Site Metadata Extraction
-- PostgreSQL 14+
-- Creates tables, indexes, and views for metadata storage and analysis

BEGIN;

-- ============================================================================
-- TABLE: site_metadata
-- Core metadata storage for all discovered sites
-- ============================================================================

CREATE TABLE IF NOT EXISTS site_metadata (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    url VARCHAR(2048) NOT NULL,
    status_code SMALLINT,
    title VARCHAR(255),
    meta_description TEXT,
    h1_heading VARCHAR(255),
    h2_headings TEXT[],
    server_software VARCHAR(100),
    content_type VARCHAR(100),
    page_size BIGINT,
    load_time_ms FLOAT,
    ssl_valid BOOLEAN DEFAULT false,
    ssl_issuer VARCHAR(255),
    canonical_url VARCHAR(2048),
    robots_txt_present BOOLEAN DEFAULT false,
    sitemap_url VARCHAR(2048),
    language_detected VARCHAR(10),
    
    -- Quality metrics
    extraction_success BOOLEAN DEFAULT true,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Timestamps
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    crawled_count INT DEFAULT 1,
    
    -- Audit
    created_by VARCHAR(100) DEFAULT 'system',
    updated_by VARCHAR(100) DEFAULT 'system'
);

CREATE INDEX idx_site_metadata_domain ON site_metadata(domain);
CREATE INDEX idx_site_metadata_extracted_at ON site_metadata(extracted_at DESC);
CREATE INDEX idx_site_metadata_confidence ON site_metadata(confidence_score DESC);
CREATE INDEX idx_site_metadata_status_code ON site_metadata(status_code);


-- ============================================================================
-- TABLE: site_technologies
-- Detected technology stack for each site
-- ============================================================================

CREATE TABLE IF NOT EXISTS site_technologies (
    id BIGSERIAL PRIMARY KEY,
    site_id BIGINT NOT NULL REFERENCES site_metadata(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    
    -- Technology categories
    cms VARCHAR(100),
    programming_language VARCHAR(100),
    server_software VARCHAR(100),
    web_framework VARCHAR(100),
    cdn_provider VARCHAR(100),
    
    -- Technology lists
    frontend_frameworks TEXT[],
    backend_frameworks TEXT[],
    libraries TEXT[],
    analytics_tools TEXT[],
    payment_providers TEXT[],
    chat_tools TEXT[],
    monitoring_tools TEXT[],
    container_orchestration VARCHAR(100),
    
    -- Metadata
    total_technologies INT,
    detection_confidence FLOAT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_site_technologies_domain ON site_technologies(domain);
CREATE INDEX idx_site_technologies_site_id ON site_technologies(site_id);
CREATE INDEX idx_site_technologies_cms ON site_technologies(cms);
CREATE INDEX idx_site_technologies_language ON site_technologies(programming_language);


-- ============================================================================
-- TABLE: site_seo_data
-- SEO metrics and analysis results
-- ============================================================================

CREATE TABLE IF NOT EXISTS site_seo_data (
    id BIGSERIAL PRIMARY KEY,
    site_id BIGINT NOT NULL REFERENCES site_metadata(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    
    -- SEO scores (0-100)
    title_score FLOAT,
    description_score FLOAT,
    heading_score FLOAT,
    content_score FLOAT,
    mobile_score FLOAT,
    technical_score FLOAT,
    overall_seo_score FLOAT,
    
    -- Content analysis
    word_count INT,
    paragraph_count INT,
    image_count INT,
    images_with_alt INT,
    heading_structure JSON,
    
    -- Keywords
    detected_keywords TEXT[],
    keyword_density FLOAT,
    
    -- Structured data
    has_json_ld BOOLEAN DEFAULT false,
    has_schema_org BOOLEAN DEFAULT false,
    schema_types TEXT[],
    
    -- Technical SEO
    has_canonical BOOLEAN DEFAULT false,
    has_robots_meta BOOLEAN DEFAULT false,
    language_attribute VARCHAR(10),
    
    -- Links
    internal_links INT DEFAULT 0,
    external_links INT DEFAULT 0,
    broken_links INT DEFAULT 0,
    
    -- Metadata
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_site_seo_domain ON site_seo_data(domain);
CREATE INDEX idx_site_seo_site_id ON site_seo_data(site_id);
CREATE INDEX idx_site_seo_overall_score ON site_seo_data(overall_seo_score DESC);
CREATE INDEX idx_site_seo_keyword ON site_seo_data USING GIN(detected_keywords);


-- ============================================================================
-- TABLE: site_hosting_data
-- IP and hosting information
-- ============================================================================

CREATE TABLE IF NOT EXISTS site_hosting_data (
    id BIGSERIAL PRIMARY KEY,
    site_id BIGINT NOT NULL REFERENCES site_metadata(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    
    -- IP Information
    ip_address INET,
    country_code VARCHAR(2),
    country_name VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT,
    
    -- ISP/Organization
    isp VARCHAR(255),
    organization VARCHAR(255),
    autonomous_system INT,
    as_organization VARCHAR(255),
    
    -- Hosting
    hosting_provider VARCHAR(255),
    is_cdn BOOLEAN DEFAULT false,
    is_vps BOOLEAN DEFAULT false,
    is_shared_hosting BOOLEAN DEFAULT false,
    
    -- SSL Certificate
    ssl_certificate_issuer VARCHAR(255),
    ssl_valid BOOLEAN DEFAULT false,
    ssl_expiry_date DATE,
    
    -- Reverse DNS
    reverse_dns VARCHAR(255),
    
    -- Metadata
    looked_up_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_site_hosting_domain ON site_hosting_data(domain);
CREATE INDEX idx_site_hosting_site_id ON site_hosting_data(site_id);
CREATE INDEX idx_site_hosting_country ON site_hosting_data(country_code);
CREATE INDEX idx_site_hosting_provider ON site_hosting_data(hosting_provider);
CREATE INDEX idx_site_hosting_ip ON site_hosting_data(ip_address);


-- ============================================================================
-- TABLE: site_backlinks
-- Estimated backlink data
-- ============================================================================

CREATE TABLE IF NOT EXISTS site_backlinks (
    id BIGSERIAL PRIMARY KEY,
    site_id BIGINT NOT NULL REFERENCES site_metadata(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    
    -- Backlink metrics
    total_backlinks INT DEFAULT 0,
    unique_referring_domains INT DEFAULT 0,
    backlink_quality_score FLOAT,
    
    -- Top referring domains
    top_referrers TEXT[],
    top_referrer_counts INT[],
    
    -- Metrics
    domain_authority FLOAT,
    page_authority FLOAT,
    spam_score FLOAT,
    
    -- Analysis
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100)
);

CREATE INDEX idx_site_backlinks_domain ON site_backlinks(domain);
CREATE INDEX idx_site_backlinks_site_id ON site_backlinks(site_id);
CREATE INDEX idx_site_backlinks_authority ON site_backlinks(domain_authority DESC);


-- ============================================================================
-- TABLE: site_traffic_estimate
-- Traffic estimation and popularity metrics
-- ============================================================================

CREATE TABLE IF NOT EXISTS site_traffic_estimate (
    id BIGSERIAL PRIMARY KEY,
    site_id BIGINT NOT NULL REFERENCES site_metadata(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    
    -- Traffic estimates
    monthly_visitors INT,
    monthly_pageviews INT,
    bounce_rate FLOAT,
    avg_session_duration FLOAT,
    
    -- Confidence
    estimate_confidence FLOAT,
    data_source VARCHAR(100),
    
    -- Trend
    trend VARCHAR(20), -- 'up', 'down', 'stable'
    trend_percentage FLOAT,
    
    -- Social signals
    facebook_shares INT DEFAULT 0,
    twitter_mentions INT DEFAULT 0,
    linkedin_shares INT DEFAULT 0,
    
    -- Metrics
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_site_traffic_domain ON site_traffic_estimate(domain);
CREATE INDEX idx_site_traffic_site_id ON site_traffic_estimate(site_id);
CREATE INDEX idx_site_traffic_visitors ON site_traffic_estimate(monthly_visitors DESC);


-- ============================================================================
-- TABLE: metadata_extraction_log
-- Audit trail for all extraction operations
-- ============================================================================

CREATE TABLE IF NOT EXISTS metadata_extraction_log (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL,
    
    -- Operation details
    operation VARCHAR(50), -- 'extract', 'update', 'delete'
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    
    -- Extraction details
    url_accessed VARCHAR(2048),
    http_status INT,
    response_time_ms FLOAT,
    
    -- Field counts
    fields_extracted INT,
    fields_missing INT,
    
    -- Metadata
    extracted_by VARCHAR(100),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100)
);

CREATE INDEX idx_extraction_log_domain ON metadata_extraction_log(domain);
CREATE INDEX idx_extraction_log_timestamp ON metadata_extraction_log(extracted_at DESC);
CREATE INDEX idx_extraction_log_success ON metadata_extraction_log(success);
CREATE INDEX idx_extraction_log_batch ON metadata_extraction_log(batch_id);


-- ============================================================================
-- TABLE: metadata_errors
-- Error tracking and debugging
-- ============================================================================

CREATE TABLE IF NOT EXISTS metadata_errors (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL,
    
    -- Error details
    error_type VARCHAR(100),
    error_message TEXT,
    error_stack TEXT,
    
    -- Context
    extraction_stage VARCHAR(100),
    attempted_at TIMESTAMP,
    retry_count INT DEFAULT 0,
    
    -- Resolution
    resolved BOOLEAN DEFAULT false,
    resolution_notes TEXT,
    resolved_at TIMESTAMP,
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_errors_domain ON metadata_errors(domain);
CREATE INDEX idx_errors_timestamp ON metadata_errors(created_at DESC);
CREATE INDEX idx_errors_type ON metadata_errors(error_type);
CREATE INDEX idx_errors_resolved ON metadata_errors(resolved);


-- ============================================================================
-- MATERIALIZED VIEW: seo_performance_summary
-- Summary of SEO metrics across all sites
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS seo_performance_summary AS
SELECT
    sm.domain,
    sm.title,
    sm.status_code,
    sd.overall_seo_score,
    sd.word_count,
    sd.image_count,
    sd.internal_links,
    sd.external_links,
    sb.domain_authority,
    st.monthly_visitors,
    sm.confidence_score,
    sm.extracted_at
FROM site_metadata sm
LEFT JOIN site_seo_data sd ON sm.id = sd.site_id
LEFT JOIN site_backlinks sb ON sm.id = sb.site_id
LEFT JOIN site_traffic_estimate st ON sm.id = st.site_id
WHERE sm.extraction_success = true
ORDER BY sd.overall_seo_score DESC;

CREATE INDEX idx_seo_summary_domain ON seo_performance_summary(domain);
CREATE INDEX idx_seo_summary_score ON seo_performance_summary(overall_seo_score);


-- ============================================================================
-- MATERIALIZED VIEW: technology_distribution
-- Distribution of technologies across domains
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS technology_distribution AS
SELECT
    cms,
    programming_language,
    COUNT(*) as site_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM site_technologies
WHERE cms IS NOT NULL OR programming_language IS NOT NULL
GROUP BY cms, programming_language
ORDER BY site_count DESC;

CREATE INDEX idx_tech_dist_count ON technology_distribution(site_count DESC);


-- ============================================================================
-- MATERIALIZED VIEW: hosting_provider_analysis
-- Analysis of hosting providers
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS hosting_provider_analysis AS
SELECT
    sh.hosting_provider,
    sh.country_code,
    COUNT(*) as site_count,
    COUNT(DISTINCT sh.country_code) as country_diversity,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM site_hosting_data sh
WHERE sh.hosting_provider IS NOT NULL
GROUP BY sh.hosting_provider, sh.country_code
ORDER BY site_count DESC;

CREATE INDEX idx_hosting_provider ON hosting_provider_analysis(hosting_provider);


-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_seo_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_site_seo_updated
BEFORE UPDATE ON site_seo_data
FOR EACH ROW
EXECUTE FUNCTION update_seo_last_updated();


CREATE OR REPLACE FUNCTION update_metadata_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_metadata_updated
BEFORE UPDATE ON site_metadata
FOR EACH ROW
EXECUTE FUNCTION update_metadata_last_updated();


-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

INSERT INTO site_metadata (domain, url, status_code, title, meta_description, confidence_score)
VALUES
    ('example-bd.com', 'https://example-bd.com', 200, 'Example Site', 'Example description', 0.85),
    ('test-site.org.bd', 'https://test-site.org.bd', 200, 'Test Website', 'Testing metadata extraction', 0.92)
ON CONFLICT DO NOTHING;


-- ============================================================================
-- STATISTICS AND ANALYSIS
-- ============================================================================

COMMENT ON TABLE site_metadata IS 'Core metadata for all discovered sites';
COMMENT ON TABLE site_technologies IS 'Technology stack detection results';
COMMENT ON TABLE site_seo_data IS 'SEO analysis and scoring';
COMMENT ON TABLE site_hosting_data IS 'IP and hosting information';
COMMENT ON TABLE site_backlinks IS 'Backlink and authority data';
COMMENT ON TABLE site_traffic_estimate IS 'Traffic estimation metrics';
COMMENT ON TABLE metadata_extraction_log IS 'Audit trail of extraction operations';
COMMENT ON TABLE metadata_errors IS 'Error tracking and debugging';

-- Vacuum and analyze
VACUUM ANALYZE site_metadata;
VACUUM ANALYZE site_technologies;
VACUUM ANALYZE site_seo_data;
VACUUM ANALYZE site_hosting_data;
VACUUM ANALYZE site_backlinks;
VACUUM ANALYZE site_traffic_estimate;

COMMIT;
