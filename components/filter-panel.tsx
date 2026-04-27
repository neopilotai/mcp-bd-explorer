'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';

interface FilterPanelProps {
  filters: {
    category: string;
    country: string;
    minTraffic: number;
    status: string;
    technologies: string[];
  };
  onChange: (filters: any) => void;
}

const CATEGORIES = ['all', 'government', 'education', 'e-commerce', 'news', 'business', 'healthcare', 'banking'];
const TECHNOLOGIES = ['WordPress', 'Next.js', 'Django', 'Laravel', 'PHP', 'Node.js', 'React', 'Vue.js'];
const STATUSES = ['active', 'inactive', 'archived'];

export default function FilterPanel({ filters, onChange }: FilterPanelProps) {
  return (
    <div className="space-y-4">
      {/* Category Filter */}
      <Card className="border-border/60 bg-card/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-foreground">Category</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Select value={filters.category} onValueChange={(value) => onChange({ ...filters, category: value })}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CATEGORIES.map((cat) => (
                <SelectItem key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Status Filter */}
      <Card className="border-border/60 bg-card/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-foreground">Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Select value={filters.status} onValueChange={(value) => onChange({ ...filters, status: value })}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {STATUSES.map((status) => (
                <SelectItem key={status} value={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Traffic Filter */}
      <Card className="border-border/60 bg-card/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-foreground">Min. Traffic</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Slider
            value={[filters.minTraffic]}
            onValueChange={(value) => onChange({ ...filters, minTraffic: value[0] })}
            max={500000}
            step={10000}
            className="w-full"
          />
          <p className="text-sm text-muted-foreground text-center">{(filters.minTraffic / 1000).toFixed(0)}K visitors</p>
        </CardContent>
      </Card>

      {/* Technologies Filter */}
      <Card className="border-border/60 bg-card/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-foreground">Technologies</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {TECHNOLOGIES.map((tech) => (
            <div key={tech} className="flex items-center space-x-2">
              <Checkbox
                id={tech}
                checked={filters.technologies.includes(tech)}
                onCheckedChange={(checked) => {
                  const updated = checked
                    ? [...filters.technologies, tech]
                    : filters.technologies.filter((t) => t !== tech);
                  onChange({ ...filters, technologies: updated });
                }}
              />
              <Label htmlFor={tech} className="font-normal cursor-pointer text-sm">
                {tech}
              </Label>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Reset Filters */}
      <button
        onClick={() =>
          onChange({
            category: 'all',
            country: 'all',
            minTraffic: 0,
            status: 'active',
            technologies: [],
          })
        }
        className="w-full px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground border border-border/60 rounded-lg transition"
      >
        Reset Filters
      </button>
    </div>
  );
}
