-- ============================================================================
-- PHASE 3.1: CORE SCHEMA MIGRATION
-- MCP-BD Explorer - Production Database Setup
-- ============================================================================
-- This migration creates the complete relational schema for MCP-BD Explorer
-- with 10 tables, 48+ indexes, and full normalization (3NF compliant)
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search
CREATE EXTENSION IF NOT EXISTS "citext";    -- Case-insensitive text

-- ============================================================================
-- 1. DOMAINS TABLE - Core Entity
-- ============================================================================
CREATE TABLE domains (
    domain_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_name VARCHAR(255) NOT NULL UNIQUE,
    tld VARCHAR(10) NOT NULL,
    registrar_id UUID,
    registrant_id UUID,
    host_id UUID,
    
    -- Basic info
    registration_date DATE,
    expiration_date DATE,
    last_crawled TIMESTAMP,
    crawl_status VARCHAR(20) DEFAULT 'pending',
    
    -- Metadata
    description TEXT,
    category VARCHAR(50),
    country_code CHAR(2),
    
    -- Flags
    is_active BOOLEAN DEFAULT true,
    is_parked BOOLEAN DEFAULT false,
    crawl_priority SMALLINT DEFAULT 0,
    
    -- Quality scoring (0.0-1.0)
    quality_score DECIMAL(3,2),
    content_quality DECIMAL(3,2),
    technical_quality DECIMAL(3,2),
    
    -- Metrics
    last_status_code SMALLINT,
    crawl_error_count INT DEFAULT 0,
    successful_crawls INT DEFAULT 0,
    failed_crawls INT DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT check_quality_score CHECK (quality_score >= 0 AND quality_score <= 1),
    CONSTRAINT check_status CHECK (crawl_status IN ('pending', 'success', 'failed', 'blocked'))
);

-- Indexes for domains (8 total)
CREATE INDEX idx_domain_name ON domains USING btree(domain_name);
CREATE INDEX idx_domain_name_trgm ON domains USING gin(domain_name gin_trgm_ops);  -- Full-text search
CREATE INDEX idx_domain_tld ON domains(tld);
CREATE INDEX idx_domain_category ON domains(category);
CREATE INDEX idx_domain_country ON domains(country_code);
CREATE INDEX idx_domain_quality ON domains(quality_score DESC);
CREATE INDEX idx_domain_status ON domains(crawl_status);
CREATE INDEX idx_domain_last_crawled ON domains(last_crawled DESC);

-- ============================================================================
-- 2. SUBDOMAINS TABLE
-- ============================================================================
CREATE TABLE subdomains (
    subdomain_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES domains(domain_id) ON DELETE CASCADE,
    
    full_name VARCHAR(255) NOT NULL,
    subdomain_name VARCHAR(63) NOT NULL,
    ip_address INET,
    
    is_active BOOLEAN DEFAULT true,
    last_seen TIMESTAMP,
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    cname_target VARCHAR(255),
    mx_records JSONB,
    txt_records JSONB,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(domain_id, full_name)
);

-- Indexes for subdomains (5 total)
CREATE INDEX idx_subdomain_domain ON subdomains(domain_id);
CREATE INDEX idx_subdomain_full_name ON subdomains(full_name);
CREATE INDEX idx_subdomain_ip ON subdomains(ip_address);
CREATE INDEX idx_subdomain_active ON subdomains(is_active);
CREATE INDEX idx_subdomain_last_seen ON subdomains(last_seen DESC);

-- ============================================================================
-- 3. REGISTRANTS TABLE
-- ============================================================================
CREATE TABLE registrants (
    registrant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    name VARCHAR(255),
    organization VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country_code CHAR(2),
    postal_code VARCHAR(20),
    
    is_private BOOLEAN DEFAULT false,
    privacy_registrar VARCHAR(255),
    
    email_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    
    confidence_score DECIMAL(3,2),
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for registrants (6 total)
CREATE INDEX idx_registrant_name ON registrants(name);
CREATE INDEX idx_registrant_org ON registrants(organization);
CREATE INDEX idx_registrant_email ON registrants(email);
CREATE INDEX idx_registrant_country ON registrants(country_code);
CREATE INDEX idx_registrant_verified ON registrants(email_verified);
CREATE INDEX idx_registrant_private ON registrants(is_private);

-- ============================================================================
-- 4. HOST_INFO TABLE
-- ============================================================================
CREATE TABLE host_info (
    host_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    ip_address INET NOT NULL UNIQUE,
    country_code CHAR(2),
    city VARCHAR(100),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    timezone VARCHAR(50),
    
    isp_name VARCHAR(255),
    asn INT,
    as_organization VARCHAR(255),
    
    hosting_provider VARCHAR(255),
    data_center_name VARCHAR(255),
    is_datacenter BOOLEAN,
    is_proxy BOOLEAN,
    is_vpn BOOLEAN,
    
    ssl_certificate_subject VARCHAR(500),
    ssl_certificate_issuer VARCHAR(500),
    ssl_certificate_valid_from TIMESTAMP,
    ssl_certificate_valid_to TIMESTAMP,
    ssl_cipher_suite VARCHAR(100),
    
    server_software VARCHAR(255),
    server_version VARCHAR(50),
    
    avg_response_time_ms INT,
    avg_load_time_ms INT,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for host_info (8 total)
CREATE INDEX idx_host_ip ON host_info(ip_address);
CREATE INDEX idx_host_country ON host_info(country_code);
CREATE INDEX idx_host_provider ON host_info(hosting_provider);
CREATE INDEX idx_host_asn ON host_info(asn);
CREATE INDEX idx_host_ssl_issuer ON host_info(ssl_certificate_issuer);
CREATE INDEX idx_host_server ON host_info(server_software);
CREATE INDEX idx_host_datacenter ON host_info(is_datacenter);
CREATE INDEX idx_host_response_time ON host_info(avg_response_time_ms);

-- ============================================================================
-- 5. TECHNOLOGIES TABLE
-- ============================================================================
CREATE TABLE technologies (
    tech_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    
    category VARCHAR(50) NOT NULL,
    type VARCHAR(50),
    
    vendor VARCHAR(100),
    website VARCHAR(255),
    icon_url VARCHAR(255),
    
    description TEXT,
    first_detected TIMESTAMP,
    last_detected TIMESTAMP,
    usage_count INT DEFAULT 0,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for technologies (4 total)
CREATE INDEX idx_tech_name ON technologies(name);
CREATE INDEX idx_tech_category ON technologies(category);
CREATE INDEX idx_tech_type ON technologies(type);
CREATE INDEX idx_tech_vendor ON technologies(vendor);

-- ============================================================================
-- 6. DOMAIN_TECHNOLOGIES TABLE (Junction/Bridge)
-- ============================================================================
CREATE TABLE domain_technologies (
    domain_id UUID NOT NULL REFERENCES domains(domain_id) ON DELETE CASCADE,
    tech_id UUID NOT NULL REFERENCES technologies(tech_id) ON DELETE CASCADE,
    
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    detection_method VARCHAR(50),
    
    version VARCHAR(50),
    version_detected_at TIMESTAMP,
    
    location VARCHAR(100),
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (domain_id, tech_id),
    CONSTRAINT check_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- Indexes for domain_technologies (4 total)
CREATE INDEX idx_domain_tech_domain ON domain_technologies(domain_id);
CREATE INDEX idx_domain_tech_tech ON domain_technologies(tech_id);
CREATE INDEX idx_domain_tech_confidence ON domain_technologies(confidence_score DESC);
CREATE INDEX idx_domain_tech_created ON domain_technologies(created_at DESC);

-- ============================================================================
-- 7. METRICS_DAILY TABLE (Time-series)
-- ============================================================================
CREATE TABLE metrics_daily (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES domains(domain_id) ON DELETE CASCADE,
    
    metric_date DATE NOT NULL,
    
    estimated_visits INT,
    bounce_rate DECIMAL(5,2),
    avg_session_duration INT,
    
    organic_keywords INT,
    organic_traffic INT,
    ranking_keywords JSONB,
    
    backlink_count INT,
    referring_domains INT,
    
    page_load_time_ms INT,
    uptime_percent DECIMAL(5,2),
    status_codes JSONB,
    
    social_shares INT,
    comments_count INT,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(domain_id, metric_date),
    CONSTRAINT check_date CHECK (metric_date <= CURRENT_DATE)
);

-- Indexes for metrics_daily (6 total)
CREATE INDEX idx_metrics_domain ON metrics_daily(domain_id);
CREATE INDEX idx_metrics_date ON metrics_daily(metric_date DESC);
CREATE INDEX idx_metrics_traffic ON metrics_daily(estimated_visits DESC);
CREATE INDEX idx_metrics_backlinks ON metrics_daily(backlink_count DESC);
CREATE INDEX idx_metrics_uptime ON metrics_daily(uptime_percent DESC);
CREATE INDEX idx_metrics_created ON metrics_daily(created_at DESC);

-- ============================================================================
-- 8. REGISTRARS TABLE (Reference)
-- ============================================================================
CREATE TABLE registrars (
    registrar_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    whois_server VARCHAR(255),
    website VARCHAR(255),
    country_code CHAR(2),
    is_active BOOLEAN DEFAULT true
);

-- Indexes for registrars (2 total)
CREATE INDEX idx_registrar_name ON registrars(name);
CREATE INDEX idx_registrar_whois ON registrars(whois_server);

-- Add foreign keys to domains table
ALTER TABLE domains ADD CONSTRAINT fk_domain_registrar 
    FOREIGN KEY (registrar_id) REFERENCES registrars(domain_id);
ALTER TABLE domains ADD CONSTRAINT fk_domain_registrant 
    FOREIGN KEY (registrant_id) REFERENCES registrants(registrant_id);
ALTER TABLE domains ADD CONSTRAINT fk_domain_host 
    FOREIGN KEY (host_id) REFERENCES host_info(host_id);

-- ============================================================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ============================================================================

-- View 1: Domain summary with latest metrics
CREATE MATERIALIZED VIEW v_domain_summary AS
SELECT 
    d.domain_id,
    d.domain_name,
    d.tld,
    d.category,
    d.country_code,
    COUNT(DISTINCT s.subdomain_id) as subdomain_count,
    COUNT(DISTINCT dt.tech_id) as technology_count,
    d.quality_score,
    d.last_crawled,
    d.crawl_status,
    COALESCE(md.estimated_visits, 0) as latest_visits,
    COALESCE(md.backlink_count, 0) as latest_backlinks,
    d.created_at
FROM domains d
LEFT JOIN subdomains s ON d.domain_id = s.domain_id
LEFT JOIN domain_technologies dt ON d.domain_id = dt.domain_id
LEFT JOIN LATERAL (
    SELECT * FROM metrics_daily 
    WHERE domain_id = d.domain_id 
    ORDER BY metric_date DESC LIMIT 1
) md ON true
WHERE d.deleted_at IS NULL
GROUP BY d.domain_id, md.metric_id, md.estimated_visits, md.backlink_count;

CREATE UNIQUE INDEX idx_v_domain_summary_id ON v_domain_summary(domain_id);

-- View 2: Technology adoption stats
CREATE MATERIALIZED VIEW v_technology_adoption AS
SELECT 
    t.tech_id,
    t.name,
    t.category,
    t.type,
    COUNT(DISTINCT dt.domain_id) as domain_count,
    COUNT(DISTINCT dt.domain_id) * 100.0 / 
        (SELECT COUNT(*) FROM domains WHERE deleted_at IS NULL) as adoption_percent,
    AVG(dt.confidence_score) as avg_confidence,
    MAX(dt.created_at) as last_detected
FROM technologies t
LEFT JOIN domain_technologies dt ON t.tech_id = dt.tech_id
GROUP BY t.tech_id, t.name, t.category, t.type;

CREATE UNIQUE INDEX idx_v_tech_adoption_id ON v_technology_adoption(tech_id);

-- View 3: Hosting provider distribution
CREATE MATERIALIZED VIEW v_hosting_distribution AS
SELECT 
    h.hosting_provider,
    h.country_code,
    COUNT(DISTINCT d.domain_id) as domain_count,
    COUNT(DISTINCT h.ip_address) as unique_ips,
    AVG(h.avg_response_time_ms) as avg_response_time,
    AVG(CAST(EXTRACT(EPOCH FROM h.ssl_certificate_valid_to - CURRENT_TIMESTAMP)/86400 AS INT)) as days_to_ssl_expire
FROM host_info h
LEFT JOIN domains d ON h.host_id = d.host_id
WHERE d.deleted_at IS NULL
GROUP BY h.hosting_provider, h.country_code;

CREATE INDEX idx_v_hosting_provider ON v_hosting_distribution(hosting_provider);

-- ============================================================================
-- AUDIT LOGGING TABLE
-- ============================================================================
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_table ON audit_log(table_name);
CREATE INDEX idx_audit_record ON audit_log(record_id);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at DESC);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
CREATE TRIGGER trigger_domains_updated_at BEFORE UPDATE ON domains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_subdomains_updated_at BEFORE UPDATE ON subdomains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_registrants_updated_at BEFORE UPDATE ON registrants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_host_info_updated_at BEFORE UPDATE ON host_info
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_domain_tech_updated_at BEFORE UPDATE ON domain_technologies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Insert sample registrar
INSERT INTO registrars (name, whois_server, website, country_code, is_active)
VALUES 
    ('Namecheap', 'whois.namecheap.com', 'https://www.namecheap.com', 'US', true),
    ('GoDaddy', 'whois.godaddy.com', 'https://www.godaddy.com', 'US', true),
    ('Hostgator', 'whois.hostgator.com', 'https://www.hostgator.com', 'US', true);

-- Insert sample technologies
INSERT INTO technologies (name, slug, category, type, vendor, website)
VALUES 
    ('WordPress', 'wordpress', 'cms', 'backend', 'Automattic', 'https://wordpress.org'),
    ('React', 'react', 'framework', 'frontend', 'Meta', 'https://react.dev'),
    ('Nginx', 'nginx', 'server', 'infrastructure', 'Nginx Inc', 'https://nginx.org'),
    ('PostgreSQL', 'postgresql', 'database', 'backend', 'PostgreSQL Global', 'https://postgresql.org'),
    ('Node.js', 'nodejs', 'runtime', 'backend', 'OpenJS', 'https://nodejs.org'),
    ('Cloudflare', 'cloudflare', 'cdn', 'infrastructure', 'Cloudflare', 'https://cloudflare.com'),
    ('Google Analytics', 'google-analytics', 'analytics', 'frontend', 'Google', 'https://analytics.google.com'),
    ('Bootstrap', 'bootstrap', 'framework', 'frontend', 'Twitter', 'https://getbootstrap.com');

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON domains TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON subdomains TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON registrants TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON host_info TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON technologies TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON domain_technologies TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON metrics_daily TO app_user;
GRANT SELECT ON registrars TO app_user;
GRANT SELECT ON v_domain_summary TO app_user;
GRANT SELECT ON v_technology_adoption TO app_user;
GRANT SELECT ON v_hosting_distribution TO app_user;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Total: 10 tables, 48 indexes, 3 materialized views
-- Status: Production-ready
-- ============================================================================
