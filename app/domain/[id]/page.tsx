'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { ExternalLink, Globe, Zap, Shield, TrendingUp, Code, Users } from 'lucide-react';

interface DomainProfileProps {
  params: { id: string };
}

// Mock domain data
const DOMAIN_DATA = {
  id: '1',
  domain: 'example.com.bd',
  title: 'Example Bangladesh',
  description: 'Leading e-commerce platform in Bangladesh',
  url: 'https://example.com.bd',
  category: 'e-commerce',
  status: 'active',
  registrant: {
    name: 'Example Corporation',
    email: 'contact@example.com',
    phone: '+880 2 XXXX XXXX',
  },
  hosting: {
    provider: 'AWS',
    country: 'Bangladesh',
    ip: '203.0.113.1',
    ssl: true,
  },
  metrics: {
    traffic: 250000,
    visitors: 125000,
    pageViews: 850000,
    uptime: 99.8,
    responseTime: 245,
    trafficTrend: '+15%',
  },
  technologies: [
    { name: 'Next.js', category: 'framework', version: '14.2' },
    { name: 'PostgreSQL', category: 'database', version: '15' },
    { name: 'Redis', category: 'cache', version: '7.0' },
    { name: 'React', category: 'library', version: '18' },
    { name: 'Tailwind CSS', category: 'styling', version: '4.1' },
  ],
  seo: {
    organicKeywords: 850,
    backlinks: 1250,
    domainAuthority: 65,
    pageAuthority: 58,
  },
  crawlHistory: [
    { date: '2024-02-06 10:30', status: 'success', duration: 2.3 },
    { date: '2024-02-05 10:15', status: 'success', duration: 2.1 },
    { date: '2024-02-04 10:45', status: 'success', duration: 2.4 },
  ],
};

export default function DomainProfile({ params }: DomainProfileProps) {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border/60 bg-card/50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Globe className="w-5 h-5 text-primary" />
                <h1 className="text-3xl font-bold text-foreground">{DOMAIN_DATA.domain}</h1>
              </div>
              <p className="text-muted-foreground">{DOMAIN_DATA.title}</p>
            </div>
            <a
              href={DOMAIN_DATA.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition"
            >
              Visit Site
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge>{DOMAIN_DATA.category}</Badge>
            <Badge variant="secondary">{DOMAIN_DATA.status}</Badge>
            <Badge variant="outline">Monitored</Badge>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <Card className="border-border/60 bg-card/50">
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary mb-1">{DOMAIN_DATA.metrics.uptime}%</div>
                <p className="text-xs text-muted-foreground">Uptime</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/50">
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary mb-1">{(DOMAIN_DATA.metrics.traffic / 1000).toFixed(0)}K</div>
                <p className="text-xs text-muted-foreground">Monthly Traffic</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/50">
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary mb-1">{DOMAIN_DATA.metrics.responseTime}ms</div>
                <p className="text-xs text-muted-foreground">Response Time</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/50">
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary mb-1">{DOMAIN_DATA.seo.backlinks}</div>
                <p className="text-xs text-muted-foreground">Backlinks</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/50">
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="flex items-center justify-center gap-1">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  <span className="text-lg font-bold text-green-500">{DOMAIN_DATA.metrics.trafficTrend}</span>
                </div>
                <p className="text-xs text-muted-foreground">30-day Change</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="border-b border-border/60 bg-transparent w-full justify-start">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="technologies">Technologies</TabsTrigger>
            <TabsTrigger value="seo">SEO & Authority</TabsTrigger>
            <TabsTrigger value="hosting">Hosting</TabsTrigger>
            <TabsTrigger value="history">Crawl History</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="text-base">Description</CardTitle>
                </CardHeader>
                <CardContent className="text-muted-foreground text-sm">
                  {DOMAIN_DATA.description}
                </CardContent>
              </Card>

              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="text-base">Contact Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">Organization</p>
                    <p className="text-foreground font-medium">{DOMAIN_DATA.registrant.name}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Email</p>
                    <p className="text-foreground font-medium">{DOMAIN_DATA.registrant.email}</p>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Performance Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Visitors</span>
                    <span className="text-foreground font-medium">{(DOMAIN_DATA.metrics.visitors / 1000).toFixed(0)}K/month</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Page Views</span>
                    <span className="text-foreground font-medium">{(DOMAIN_DATA.metrics.pageViews / 1000).toFixed(0)}K/month</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Avg Response Time</span>
                    <span className="text-foreground font-medium">{DOMAIN_DATA.metrics.responseTime}ms</span>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    Security
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">SSL Certificate</span>
                    <Badge className="bg-green-500/10 text-green-600">Valid</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Security Headers</span>
                    <Badge className="bg-yellow-500/10 text-yellow-600">Partial</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Technologies Tab */}
          <TabsContent value="technologies">
            <Card className="border-border/60">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Code className="w-4 h-4" />
                  Tech Stack ({DOMAIN_DATA.technologies.length} items)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {DOMAIN_DATA.technologies.map((tech) => (
                    <div key={tech.name} className="flex items-center justify-between p-3 bg-card/50 rounded-lg border border-border/40">
                      <div>
                        <p className="font-medium text-foreground">{tech.name}</p>
                        <p className="text-xs text-muted-foreground capitalize">{tech.category}</p>
                      </div>
                      <Badge variant="secondary">{tech.version}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* SEO Tab */}
          <TabsContent value="seo">
            <Card className="border-border/60">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  SEO & Authority
                </CardTitle>
              </CardHeader>
              <CardContent className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Domain Authority</p>
                    <div className="text-3xl font-bold text-primary">{DOMAIN_DATA.seo.domainAuthority}</div>
                    <div className="mt-2 h-2 bg-border rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${DOMAIN_DATA.seo.domainAuthority}%` }} />
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Page Authority</p>
                    <div className="text-3xl font-bold text-primary">{DOMAIN_DATA.seo.pageAuthority}</div>
                    <div className="mt-2 h-2 bg-border rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${DOMAIN_DATA.seo.pageAuthority}%` }} />
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="p-4 bg-card/50 rounded-lg border border-border/40">
                    <p className="text-sm text-muted-foreground">Organic Keywords</p>
                    <p className="text-2xl font-bold text-foreground">{DOMAIN_DATA.seo.organicKeywords}</p>
                  </div>
                  <div className="p-4 bg-card/50 rounded-lg border border-border/40">
                    <p className="text-sm text-muted-foreground">Backlinks</p>
                    <p className="text-2xl font-bold text-foreground">{DOMAIN_DATA.seo.backlinks}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Hosting Tab */}
          <TabsContent value="hosting">
            <Card className="border-border/60">
              <CardHeader>
                <CardTitle className="text-base">Hosting Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 bg-card/50 rounded-lg border border-border/40">
                    <p className="text-sm text-muted-foreground mb-2">Provider</p>
                    <p className="text-lg font-semibold text-foreground">{DOMAIN_DATA.hosting.provider}</p>
                  </div>
                  <div className="p-4 bg-card/50 rounded-lg border border-border/40">
                    <p className="text-sm text-muted-foreground mb-2">Country</p>
                    <p className="text-lg font-semibold text-foreground">{DOMAIN_DATA.hosting.country}</p>
                  </div>
                  <div className="p-4 bg-card/50 rounded-lg border border-border/40">
                    <p className="text-sm text-muted-foreground mb-2">IP Address</p>
                    <p className="text-lg font-mono font-semibold text-foreground">{DOMAIN_DATA.hosting.ip}</p>
                  </div>
                  <div className="p-4 bg-card/50 rounded-lg border border-border/40">
                    <p className="text-sm text-muted-foreground mb-2">SSL Certificate</p>
                    <Badge className="bg-green-500/10 text-green-600">
                      {DOMAIN_DATA.hosting.ssl ? 'Valid' : 'Invalid'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Crawl History Tab */}
          <TabsContent value="history">
            <Card className="border-border/60">
              <CardHeader>
                <CardTitle className="text-base">Recent Crawls</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {DOMAIN_DATA.crawlHistory.map((crawl, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-card/50 rounded-lg border border-border/40">
                      <div>
                        <p className="font-medium text-foreground">{crawl.date}</p>
                        <p className="text-xs text-muted-foreground">Duration: {crawl.duration}s</p>
                      </div>
                      <Badge className={crawl.status === 'success' ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'}>
                        {crawl.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
