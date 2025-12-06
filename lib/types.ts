// Domain represents a tracked Bangladeshi website
export interface Domain {
  id: string
  domain: string
  title?: string
  description?: string
  category?: string
  tags?: string[]
  status: "active" | "inactive" | "pending"
  last_crawled?: string
  response_time?: number
  ssl_enabled?: boolean
  server_info?: Record<string, unknown>
  contact_info?: Record<string, unknown>
  social_links?: Record<string, unknown>
  created_at: string
  updated_at?: string
}

// CrawlLog tracks individual crawl attempts
export interface CrawlLog {
  id: string
  domain_id?: string
  domain?: string
  response_code?: number
  response_time?: number
  error_message?: string
  crawl_date: string
  status?: "success" | "failed" | "timeout"
  changes_detected?: Record<string, unknown>
  robots_txt_content?: string
  robots_txt_checked?: boolean
  whois_checked?: boolean
  ssl_checked?: boolean
  dns_resolved?: boolean
  created_at?: string
}

// Category for organizing domains
export interface Category {
  id: string
  name: string
  description?: string
  color?: string
  created_at: string
}

// DNS records for a domain
export interface DnsRecord {
  id: string
  domain_id: string
  record_type: string
  name?: string
  value?: string
  ttl?: number
  priority?: number
  created_at: string
  updated_at?: string
}

// SSL certificate information
export interface SslCert {
  id: string
  domain_id: string
  issuer?: string
  subject?: string
  fingerprint?: string
  serial_number?: string
  signature_algorithm?: string
  san_domains?: string[]
  valid_from?: string
  valid_to?: string
  is_valid?: boolean
  is_expired?: boolean
  is_self_signed?: boolean
  key_size?: number
  certificate_chain?: Record<string, unknown>
  created_at: string
  updated_at?: string
}

// WHOIS information for a domain
export interface Whois {
  id: string
  domain_id: string
  registrar?: string
  registrant_name?: string
  registrant_email?: string
  registrant_organization?: string
  registrant_country?: string
  creation_date?: string
  expiration_date?: string
  updated_date?: string
  name_servers?: string[]
  status?: string[]
  dnssec?: boolean
  admin_contact?: Record<string, unknown>
  tech_contact?: Record<string, unknown>
  billing_contact?: Record<string, unknown>
  raw_whois?: string
  created_at: string
  updated_at?: string
}

// Job for scheduled crawling tasks
export interface Job {
  id: string
  domain_id?: string
  job_type: string
  status: "pending" | "running" | "completed" | "failed"
  priority?: number
  attempts?: number
  max_attempts?: number
  scheduled_at?: string
  started_at?: string
  completed_at?: string
  retry_after?: string
  error_message?: string
  metadata?: Record<string, unknown>
  created_at: string
  updated_at?: string
}

// API error response
export interface ApiError {
  error: string
  code?: string
  statusCode: number
  timestamp: string
}

// Generic API response wrapper
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
  timestamp?: string
}

// Pagination info
export interface Pagination {
  page: number
  limit: number
  total: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

// Domains API response
export interface DomainsApiResponse {
  domains: Domain[]
  pagination: Pagination
  filters?: {
    search?: string
    category?: string
    status?: string
    sortBy?: string
    sortOrder?: string
  }
}

// Categories API response
export interface CategoriesApiResponse {
  categories: (Category & { domain_count?: number })[]
}

// Crawl result from crawler
export interface CrawlResult {
  domain: string
  title?: string
  description?: string
  response_code: number
  response_time: number
  page_size?: number
  ssl_enabled?: boolean
  server?: string
  content_type?: string
  error_message?: string
}
