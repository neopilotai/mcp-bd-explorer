import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Search, Globe, TrendingUp, Shield, Database, Users } from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Globe className="h-8 w-8 text-primary" />
                <span className="text-xl font-bold text-foreground">MCP-BD Explorer</span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/search" className="text-muted-foreground hover:text-foreground transition-colors">
                Search
              </Link>
              <Link href="/categories" className="text-muted-foreground hover:text-foreground transition-colors">
                Categories
              </Link>
              <Link href="/about" className="text-muted-foreground hover:text-foreground transition-colors">
                About
              </Link>
              <Button variant="outline" size="sm" asChild>
                <Link href="/admin">Admin</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 lg:py-32">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl text-balance">
              The complete database of <span className="text-primary">Bangladeshi websites</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-muted-foreground text-pretty max-w-2xl mx-auto">
              Discover, explore, and analyze Bangladesh's digital landscape. Access comprehensive data on domains,
              technologies, and digital presence across the country.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="text-base px-8" asChild>
                <Link href="/search">Start Exploring</Link>
              </Button>
              <Button variant="outline" size="lg" className="text-base px-8 bg-transparent" asChild>
                <Link href="/categories">Browse Categories</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Search Section */}
      <section className="py-16 bg-card/50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search domains, companies, or technologies..."
                className="pl-10 h-12 text-base bg-background border-border/60"
              />
              <Button className="absolute right-2 top-1/2 -translate-y-1/2" size="sm">
                Search
              </Button>
            </div>
            <div className="mt-4 flex flex-wrap gap-2 justify-center">
              <Badge variant="secondary">government.bd</Badge>
              <Badge variant="secondary">e-commerce</Badge>
              <Badge variant="secondary">news</Badge>
              <Badge variant="secondary">education</Badge>
              <Badge variant="secondary">banking</Badge>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="bg-card/50 border-border/60">
              <CardHeader className="pb-3">
                <CardTitle className="text-2xl font-bold text-primary">15,000+</CardTitle>
                <CardDescription>Domains tracked</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center text-sm text-muted-foreground">
                  <TrendingUp className="h-4 w-4 mr-1" />
                  Growing daily
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card/50 border-border/60">
              <CardHeader className="pb-3">
                <CardTitle className="text-2xl font-bold text-primary">95%</CardTitle>
                <CardDescription>Uptime monitoring</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center text-sm text-muted-foreground">
                  <Shield className="h-4 w-4 mr-1" />
                  Real-time status
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card/50 border-border/60">
              <CardHeader className="pb-3">
                <CardTitle className="text-2xl font-bold text-primary">50+</CardTitle>
                <CardDescription>Categories covered</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center text-sm text-muted-foreground">
                  <Database className="h-4 w-4 mr-1" />
                  Comprehensive data
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card/50 border-border/60">
              <CardHeader className="pb-3">
                <CardTitle className="text-2xl font-bold text-primary">24/7</CardTitle>
                <CardDescription>Automated crawling</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center text-sm text-muted-foreground">
                  <Users className="h-4 w-4 mr-1" />
                  Always updated
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Categories Preview */}
      <section className="py-16 bg-card/30">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-foreground mb-4">Explore by Category</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Browse websites organized by industry and purpose to discover Bangladesh's digital ecosystem.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {[
              { name: "Government", count: "2,500+", color: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
              { name: "Education", count: "3,200+", color: "bg-green-500/10 text-green-400 border-green-500/20" },
              { name: "Business", count: "4,800+", color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" },
              { name: "News & Media", count: "1,200+", color: "bg-red-500/10 text-red-400 border-red-500/20" },
              { name: "E-commerce", count: "2,100+", color: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
              { name: "Technology", count: "1,800+", color: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" },
              { name: "Healthcare", count: "900+", color: "bg-lime-500/10 text-lime-400 border-lime-500/20" },
              { name: "Banking", count: "150+", color: "bg-orange-500/10 text-orange-400 border-orange-500/20" },
              { name: "Entertainment", count: "600+", color: "bg-pink-500/10 text-pink-400 border-pink-500/20" },
              { name: "NGO", count: "800+", color: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20" },
            ].map((category) => (
              <Card
                key={category.name}
                className={`cursor-pointer transition-all hover:scale-105 ${category.color} border`}
              >
                <CardContent className="p-4 text-center">
                  <h3 className="font-semibold mb-1">{category.name}</h3>
                  <p className="text-sm opacity-80">{category.count}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-foreground mb-4">Comprehensive Digital Intelligence</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Advanced tools and insights to understand Bangladesh's digital landscape.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Database className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">Real-time Monitoring</h3>
                  <p className="text-muted-foreground">
                    Track website status, performance metrics, and technology changes across all monitored domains.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Shield className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">Security Analysis</h3>
                  <p className="text-muted-foreground">
                    SSL certificate monitoring, security headers analysis, and vulnerability tracking.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">Technology Stack Detection</h3>
                  <p className="text-muted-foreground">
                    Identify frameworks, CMS platforms, hosting providers, and technology trends.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-card/50 border border-border/60 rounded-lg p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Sample Domain Analysis</span>
                  <Badge variant="secondary">Live Data</Badge>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm">Response Time</span>
                    <span className="text-sm font-mono text-primary">245ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">SSL Status</span>
                    <span className="text-sm text-green-400">✓ Valid</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Technology</span>
                    <span className="text-sm font-mono">Next.js</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Last Crawled</span>
                    <span className="text-sm text-muted-foreground">2 min ago</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 bg-card/30">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Globe className="h-6 w-6 text-primary" />
                <span className="text-lg font-bold text-foreground">MCP-BD Explorer</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Comprehensive database of Bangladeshi websites and digital presence.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-4">Explore</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <Link href="/search" className="hover:text-foreground transition-colors">
                    Search Domains
                  </Link>
                </li>
                <li>
                  <Link href="/categories" className="hover:text-foreground transition-colors">
                    Categories
                  </Link>
                </li>
                <li>
                  <Link href="/statistics" className="hover:text-foreground transition-colors">
                    Statistics
                  </Link>
                </li>
                <li>
                  <Link href="/api" className="hover:text-foreground transition-colors">
                    API Access
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-4">Resources</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <Link href="/about" className="hover:text-foreground transition-colors">
                    About
                  </Link>
                </li>
                <li>
                  <Link href="/methodology" className="hover:text-foreground transition-colors">
                    Methodology
                  </Link>
                </li>
                <li>
                  <Link href="/contact" className="hover:text-foreground transition-colors">
                    Contact
                  </Link>
                </li>
                <li>
                  <Link href="/privacy" className="hover:text-foreground transition-colors">
                    Privacy Policy
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-4">Admin</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <Link href="/admin" className="hover:text-foreground transition-colors">
                    Dashboard
                  </Link>
                </li>
                <li>
                  <Link href="/admin/domains" className="hover:text-foreground transition-colors">
                    Manage Domains
                  </Link>
                </li>
                <li>
                  <Link href="/admin/crawl" className="hover:text-foreground transition-colors">
                    Crawl Status
                  </Link>
                </li>
                <li>
                  <Link href="/auth/login" className="hover:text-foreground transition-colors">
                    Login
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-border/40 text-center text-sm text-muted-foreground">
            <p>&copy; 2025 MCP-BD Explorer. Built for exploring Bangladesh's digital landscape.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
