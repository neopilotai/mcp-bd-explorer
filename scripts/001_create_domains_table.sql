-- Create domains table to store Bangladeshi website information
CREATE TABLE IF NOT EXISTS public.domains (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  domain VARCHAR(255) UNIQUE NOT NULL,
  title TEXT,
  description TEXT,
  category VARCHAR(100),
  tags TEXT[], -- Array of tags
  status VARCHAR(20) DEFAULT 'active', -- active, inactive, pending
  last_crawled TIMESTAMP WITH TIME ZONE,
  response_time INTEGER, -- in milliseconds
  ssl_enabled BOOLEAN DEFAULT false,
  server_info JSONB, -- Store server headers and tech stack info
  contact_info JSONB, -- Store contact details if found
  social_links JSONB, -- Store social media links
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_domains_domain ON public.domains(domain);
CREATE INDEX IF NOT EXISTS idx_domains_category ON public.domains(category);
CREATE INDEX IF NOT EXISTS idx_domains_status ON public.domains(status);
CREATE INDEX IF NOT EXISTS idx_domains_tags ON public.domains USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_domains_created_at ON public.domains(created_at);

-- Create crawl_logs table to track crawling activities
CREATE TABLE IF NOT EXISTS public.crawl_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  domain_id UUID REFERENCES public.domains(id) ON DELETE CASCADE,
  crawl_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  status VARCHAR(20), -- success, failed, timeout
  response_code INTEGER,
  response_time INTEGER,
  error_message TEXT,
  changes_detected JSONB, -- Store what changed since last crawl
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crawl_logs_domain_id ON public.crawl_logs(domain_id);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_crawl_date ON public.crawl_logs(crawl_date);

-- Create categories table for better organization
CREATE TABLE IF NOT EXISTS public.categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) UNIQUE NOT NULL,
  description TEXT,
  color VARCHAR(7), -- Hex color code
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default categories
INSERT INTO public.categories (name, description, color) VALUES
  ('Government', 'Government and public sector websites', '#3B82F6'),
  ('Education', 'Educational institutions and learning platforms', '#10B981'),
  ('Business', 'Corporate and business websites', '#F59E0B'),
  ('News & Media', 'News outlets and media organizations', '#EF4444'),
  ('E-commerce', 'Online shopping and marketplace platforms', '#8B5CF6'),
  ('Technology', 'Tech companies and IT services', '#06B6D4'),
  ('Healthcare', 'Medical and healthcare services', '#84CC16'),
  ('Banking & Finance', 'Financial institutions and services', '#F97316'),
  ('Entertainment', 'Entertainment and lifestyle websites', '#EC4899'),
  ('NGO & Non-profit', 'Non-governmental and charitable organizations', '#6366F1')
ON CONFLICT (name) DO NOTHING;

-- Enable Row Level Security (RLS) for public access
-- Since this is a public database, we'll allow read access to all
-- But restrict write access to authenticated users only

-- For domains table - public read, authenticated write
ALTER TABLE public.domains ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access to domains" ON public.domains FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to insert domains" ON public.domains FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Allow authenticated users to update domains" ON public.domains FOR UPDATE USING (auth.uid() IS NOT NULL);
CREATE POLICY "Allow authenticated users to delete domains" ON public.domains FOR DELETE USING (auth.uid() IS NOT NULL);

-- For crawl_logs table - public read, authenticated write
ALTER TABLE public.crawl_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access to crawl_logs" ON public.crawl_logs FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to insert crawl_logs" ON public.crawl_logs FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- For categories table - public read, authenticated write
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access to categories" ON public.categories FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to manage categories" ON public.categories FOR ALL USING (auth.uid() IS NOT NULL);
