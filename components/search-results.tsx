'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ExternalLink, Globe, Zap, Eye } from 'lucide-react';
import Link from 'next/link';

interface SearchResultsProps {
  query: string;
  filters: {
    category: string;
    country: string;
    minTraffic: number;
    status: string;
    technologies: string[];
  };
}

// Mock data for demonstration
const MOCK_RESULTS = [
  {
    id: '1',
    domain: 'example.com.bd',
    title: 'Example Bangladesh',
    description: 'Leading e-commerce platform in Bangladesh',
    category: 'e-commerce',
    traffic: 250000,
    technologies: ['Next.js', 'PostgreSQL', 'Redis'],
    uptime: 99.8,
    lastCrawled: '2 hours ago',
  },
  {
    id: '2',
    domain: 'company.gov.bd',
    title: 'Government Agency Portal',
    description: 'Official government portal for services',
    category: 'government',
    traffic: 120000,
    technologies: ['WordPress', 'PHP', 'MySQL'],
    uptime: 98.5,
    lastCrawled: '4 hours ago',
  },
  {
    id: '3',
    domain: 'news.bd',
    title: 'Bangladesh News Network',
    description: 'Latest news and updates from Bangladesh',
    category: 'news',
    traffic: 450000,
    technologies: ['Node.js', 'React', 'Elasticsearch'],
    uptime: 99.9,
    lastCrawled: '1 hour ago',
  },
  {
    id: '4',
    domain: 'university.edu.bd',
    title: 'National University',
    description: 'Premier educational institution in Bangladesh',
    category: 'education',
    traffic: 80000,
    technologies: ['Django', 'PostgreSQL', 'Ubuntu'],
    uptime: 97.2,
    lastCrawled: '3 hours ago',
  },
];

export default function SearchResults({ query, filters }: SearchResultsProps) {
  const results = MOCK_RESULTS.filter((item) => {
    if (filters.category !== 'all' && item.category !== filters.category) return false;
    if (item.traffic < filters.minTraffic) return false;
    return item.domain.toLowerCase().includes(query.toLowerCase()) ||
      item.title.toLowerCase().includes(query.toLowerCase());
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Search Results</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Found {results.length} {results.length === 1 ? 'domain' : 'domains'}
          </p>
        </div>
      </div>

      {results.length === 0 ? (
        <Card className="border-border/60 bg-card/50">
          <CardContent className="py-12 text-center">
            <Globe className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
            <p className="text-muted-foreground">No domains found matching your criteria</p>
            <p className="text-xs text-muted-foreground/60 mt-2">Try adjusting your filters or search terms</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {results.map((result) => (
            <Link key={result.id} href={`/domain/${result.id}`}>
              <Card className="cursor-pointer border-border/60 bg-card hover:shadow-md hover:border-border transition-all duration-200">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <CardTitle className="text-lg font-semibold truncate text-foreground">
                          {result.domain}
                        </CardTitle>
                        <ExternalLink className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      </div>
                      <p className="text-sm text-foreground font-medium mb-2">{result.title}</p>
                      <p className="text-sm text-muted-foreground line-clamp-2">{result.description}</p>
                    </div>
                    <Badge className="flex-shrink-0 capitalize">{result.category}</Badge>
                  </div>
                </CardHeader>
                <Separator className="bg-border/40" />
                <CardContent className="pt-3">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Traffic</p>
                      <p className="text-lg font-semibold text-primary">{(result.traffic / 1000).toFixed(0)}K</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Uptime</p>
                      <p className="text-lg font-semibold text-primary">{result.uptime}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Last Crawled</p>
                      <p className="text-sm text-muted-foreground font-medium">{result.lastCrawled}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Tech Stack</p>
                      <p className="text-sm font-mono text-primary">{result.technologies[0]}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {result.technologies.map((tech) => (
                      <Badge key={tech} variant="secondary" className="text-xs">
                        {tech}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
