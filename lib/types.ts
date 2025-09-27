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
  ssl_enabled: boolean
  server_info?: any
  contact_info?: any
  social_links?: any
  created_at: string
  updated_at: string
}

export interface CrawlLog {
  id: string
  domain_id: string
  crawl_date: string
  status: "success" | "failed" | "timeout"
  response_code?: number
  response_time?: number
  error_message?: string
  changes_detected?: any
  created_at: string
}

export interface Category {
  id: string
  name: string
  description?: string
  color?: string
  created_at: string
}
