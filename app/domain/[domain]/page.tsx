"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Globe,
  ExternalLink,
  Clock,
  Shield,
  Server,
  Activity,
  Calendar,
  Tag,
  LinkIcon,
  Mail,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  XCircle,
} from "lucide-react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import type { Domain, CrawlLog } from "@/lib/types"

export default function DomainDetailPage() {
  const params = useParams()
  const domainName = params.domain as string
  const [domain, setDomain] = useState<Domain | null>(null)
  const [crawlLogs, setCrawlLogs] = useState<CrawlLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const supabase = createClient()

  useEffect(() => {
    if (domainName) {
      fetchDomainDetails()
    }
  }, [domainName])

  const fetchDomainDetails = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch domain details
      const { data: domainData, error: domainError } = await supabase
        .from("domains")
        .select("*")
        .eq("domain", decodeURIComponent(domainName))
        .single()

      if (domainError) {
        if (domainError.code === "PGRST116") {
          setError("Domain not found")
        } else {
          throw domainError
        }
        return
      }

      // Fetch crawl logs
      const { data: logsData, error: logsError } = await supabase
        .from("crawl_logs")
        .select("*")
        .eq("domain_id", domainData.id)
        .order("crawl_date", { ascending: false })
        .limit(10)

      if (logsError) throw logsError

      setDomain(domainData)
      setCrawlLogs(logsData || [])
    } catch (error) {
      console.error("Error fetching domain details:", error)
      setError("Failed to load domain details")
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500/10 text-green-400 border-green-500/20"
      case "inactive":
        return "bg-red-500/10 text-red-400 border-red-500/20"
      case "pending":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/20"
    }
  }

  const getCrawlStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-400" />
      case "failed":
        return <XCircle className="h-4 w-4 text-red-400" />
      case "timeout":
        return <AlertCircle className="h-4 w-4 text-yellow-400" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const formatResponseTime = (ms?: number) => {
    if (!ms) return "N/A"
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        {/* Navigation */}
        <nav className="border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center space-x-4">
                <Link href="/" className="flex items-center space-x-2">
                  <Globe className="h-8 w-8 text-primary" />
                  <span className="text-xl font-bold text-foreground">MCP-BD Explorer</span>
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-muted rounded w-1/3"></div>
            <div className="h-4 bg-muted rounded w-1/2"></div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <div className="h-64 bg-muted rounded"></div>
                <div className="h-48 bg-muted rounded"></div>
              </div>
              <div className="space-y-6">
                <div className="h-32 bg-muted rounded"></div>
                <div className="h-48 bg-muted rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !domain) {
    return (
      <div className="min-h-screen bg-background">
        {/* Navigation */}
        <nav className="border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center space-x-4">
                <Link href="/" className="flex items-center space-x-2">
                  <Globe className="h-8 w-8 text-primary" />
                  <span className="text-xl font-bold text-foreground">MCP-BD Explorer</span>
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card className="bg-card/50 border-border/60 text-center py-12">
            <CardContent>
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">{error || "Domain not found"}</h3>
              <p className="text-muted-foreground mb-4">The domain you're looking for doesn't exist in our database.</p>
              <Button asChild>
                <Link href="/search">Back to Search</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/" className="flex items-center space-x-2">
                <Globe className="h-8 w-8 text-primary" />
                <span className="text-xl font-bold text-foreground">MCP-BD Explorer</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/search" className="text-muted-foreground hover:text-foreground transition-colors">
                Search
              </Link>
              <Link href="/categories" className="text-muted-foreground hover:text-foreground transition-colors">
                Categories
              </Link>
              <Button variant="outline" size="sm" asChild>
                <Link href="/admin">Admin</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <Button variant="ghost" className="mb-6" asChild>
          <Link href="/search">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Search
          </Link>
        </Button>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1 min-w-0">
              <h1 className="text-3xl font-bold text-foreground mb-2 text-balance">{domain.title || domain.domain}</h1>
              <div className="flex items-center space-x-4 text-muted-foreground">
                <span className="font-mono text-primary">{domain.domain}</span>
                <Badge className={getStatusColor(domain.status)} variant="outline">
                  {domain.status}
                </Badge>
                {domain.ssl_enabled && (
                  <div className="flex items-center space-x-1">
                    <Shield className="h-4 w-4 text-green-400" />
                    <span className="text-sm">SSL Enabled</span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-2 ml-4">
              <Button variant="outline" asChild>
                <a href={`https://${domain.domain}`} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Visit Site
                </a>
              </Button>
            </div>
          </div>

          {domain.description && <p className="text-muted-foreground text-lg text-pretty">{domain.description}</p>}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="technical">Technical</TabsTrigger>
                <TabsTrigger value="history">History</TabsTrigger>
                <TabsTrigger value="contact">Contact</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-6">
                {/* Basic Information */}
                <Card className="bg-card/50 border-border/60">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Globe className="h-5 w-5" />
                      <span>Basic Information</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Domain</label>
                        <p className="font-mono text-foreground">{domain.domain}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Category</label>
                        <p className="text-foreground">{domain.category || "Uncategorized"}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Status</label>
                        <Badge className={getStatusColor(domain.status)} variant="outline">
                          {domain.status}
                        </Badge>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Added</label>
                        <p className="text-foreground">{formatDate(domain.created_at)}</p>
                      </div>
                    </div>

                    {domain.tags && domain.tags.length > 0 && (
                      <div>
                        <label className="text-sm font-medium text-muted-foreground mb-2 block">Tags</label>
                        <div className="flex flex-wrap gap-2">
                          {domain.tags.map((tag, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              <Tag className="h-3 w-3 mr-1" />
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Performance Metrics */}
                <Card className="bg-card/50 border-border/60">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Activity className="h-5 w-5" />
                      <span>Performance</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">
                          {formatResponseTime(domain.response_time)}
                        </div>
                        <div className="text-sm text-muted-foreground">Response Time</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">{domain.ssl_enabled ? "Yes" : "No"}</div>
                        <div className="text-sm text-muted-foreground">SSL Certificate</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">
                          {domain.last_crawled ? formatDate(domain.last_crawled) : "Never"}
                        </div>
                        <div className="text-sm text-muted-foreground">Last Crawled</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="technical" className="space-y-6">
                <Card className="bg-card/50 border-border/60">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Server className="h-5 w-5" />
                      <span>Technical Details</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {domain.server_info ? (
                      <div className="space-y-3">
                        <pre className="bg-muted/50 p-4 rounded-lg text-sm overflow-x-auto">
                          {JSON.stringify(domain.server_info, null, 2)}
                        </pre>
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No technical information available.</p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="history" className="space-y-6">
                <Card className="bg-card/50 border-border/60">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Clock className="h-5 w-5" />
                      <span>Crawl History</span>
                    </CardTitle>
                    <CardDescription>Recent crawling attempts and their results</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {crawlLogs.length > 0 ? (
                      <div className="space-y-3">
                        {crawlLogs.map((log) => (
                          <div key={log.id} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                            <div className="flex items-center space-x-3">
                              {getCrawlStatusIcon(log.status)}
                              <div>
                                <div className="text-sm font-medium text-foreground">
                                  {log.status.charAt(0).toUpperCase() + log.status.slice(1)}
                                </div>
                                <div className="text-xs text-muted-foreground">{formatDate(log.crawl_date)}</div>
                              </div>
                            </div>
                            <div className="text-right">
                              {log.response_code && (
                                <div className="text-sm font-mono text-foreground">{log.response_code}</div>
                              )}
                              {log.response_time && (
                                <div className="text-xs text-muted-foreground">
                                  {formatResponseTime(log.response_time)}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No crawl history available.</p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="contact" className="space-y-6">
                <Card className="bg-card/50 border-border/60">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Mail className="h-5 w-5" />
                      <span>Contact Information</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {domain.contact_info ? (
                      <div className="space-y-3">
                        <pre className="bg-muted/50 p-4 rounded-lg text-sm overflow-x-auto">
                          {JSON.stringify(domain.contact_info, null, 2)}
                        </pre>
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No contact information available.</p>
                    )}

                    {domain.social_links && (
                      <div className="mt-6">
                        <h4 className="text-sm font-medium text-foreground mb-3">Social Links</h4>
                        <pre className="bg-muted/50 p-4 rounded-lg text-sm overflow-x-auto">
                          {JSON.stringify(domain.social_links, null, 2)}
                        </pre>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <Card className="bg-card/50 border-border/60">
              <CardHeader>
                <CardTitle className="text-lg">Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Response Time</span>
                  <span className="text-sm font-mono text-foreground">{formatResponseTime(domain.response_time)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">SSL Status</span>
                  <span className={`text-sm ${domain.ssl_enabled ? "text-green-400" : "text-red-400"}`}>
                    {domain.ssl_enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Last Updated</span>
                  <span className="text-sm text-muted-foreground">{formatDate(domain.updated_at)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Crawl Logs</span>
                  <span className="text-sm text-foreground">{crawlLogs.length}</span>
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <Card className="bg-card/50 border-border/60">
              <CardHeader>
                <CardTitle className="text-lg">Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" className="w-full bg-transparent" asChild>
                  <a href={`https://${domain.domain}`} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Visit Website
                  </a>
                </Button>
                <Button variant="outline" className="w-full bg-transparent" asChild>
                  <Link href={`/search?category=${encodeURIComponent(domain.category || "")}`}>
                    <LinkIcon className="h-4 w-4 mr-2" />
                    Similar Domains
                  </Link>
                </Button>
                <Button variant="outline" className="w-full bg-transparent" disabled>
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Crawl
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
