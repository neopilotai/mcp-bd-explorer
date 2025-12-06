"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Globe, ExternalLink, Clock, Shield, Filter, SortAsc, AlertCircle } from 'lucide-react'
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"
import type { Domain } from "@/lib/types"

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [domains, setDomains] = useState<Domain[]>([])
  const [filteredDomains, setFilteredDomains] = useState<Domain[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [sortBy, setSortBy] = useState<string>("created_at")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [retrying, setRetrying] = useState(false)

  const supabase = createClient()

  useEffect(() => {
    fetchDomains()
  }, [])

  useEffect(() => {
    filterAndSortDomains()
  }, [domains, searchQuery, selectedCategory, sortBy, statusFilter])

  const fetchDomains = async (isRetry = false) => {
    try {
      if (isRetry) setRetrying(true)
      else setLoading(true)
      setError(null)

      const { data, error: queryError } = await supabase
        .from("domains")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(100)

      if (queryError) throw queryError
      setDomains(data || [])
    } catch (error) {
      console.error("[v0] Error fetching domains:", error)
      setError(error instanceof Error ? error.message : "Failed to load domains")
    } finally {
      if (isRetry) setRetrying(false)
      else setLoading(false)
    }
  }

  const filterAndSortDomains = () => {
    let filtered = [...domains]

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (domain) =>
          domain.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
          domain.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          domain.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          domain.tags?.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    // Category filter
    if (selectedCategory !== "all") {
      filtered = filtered.filter((domain) => domain.category === selectedCategory)
    }

    // Status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((domain) => domain.status === statusFilter)
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "domain":
          return a.domain.localeCompare(b.domain)
        case "title":
          return (a.title || "").localeCompare(b.title || "")
        case "category":
          return (a.category || "").localeCompare(b.category || "")
        case "response_time":
          return (a.response_time || 0) - (b.response_time || 0)
        case "created_at":
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      }
    })

    setFilteredDomains(filtered)
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

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      Government: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      Education: "bg-green-500/10 text-green-400 border-green-500/20",
      Business: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
      "News & Media": "bg-red-500/10 text-red-400 border-red-500/20",
      "E-commerce": "bg-purple-500/10 text-purple-400 border-purple-500/20",
      Technology: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
      Healthcare: "bg-lime-500/10 text-lime-400 border-lime-500/20",
      "Banking & Finance": "bg-orange-500/10 text-orange-400 border-orange-500/20",
      Entertainment: "bg-pink-500/10 text-pink-400 border-pink-500/20",
      "NGO & Non-profit": "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    }
    return colors[category] || "bg-gray-500/10 text-gray-400 border-gray-500/20"
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
              <Link href="/search" className="text-primary font-medium">
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

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-4">Search Bangladeshi Websites</h1>
          <p className="text-muted-foreground text-lg">Discover and explore domains across Bangladesh's digital landscape</p>
        </div>

        {/* Search and Filters */}
        <div className="mb-8 space-y-4">
          {/* Search Bar */}
          <div className="relative max-w-2xl">
            <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search domains, titles, descriptions, or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-12 text-base bg-background border-border/60"
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium text-foreground">Filters:</span>
            </div>

            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="Government">Government</SelectItem>
                <SelectItem value="Education">Education</SelectItem>
                <SelectItem value="Business">Business</SelectItem>
                <SelectItem value="News & Media">News & Media</SelectItem>
                <SelectItem value="E-commerce">E-commerce</SelectItem>
                <SelectItem value="Technology">Technology</SelectItem>
                <SelectItem value="Healthcare">Healthcare</SelectItem>
                <SelectItem value="Banking & Finance">Banking & Finance</SelectItem>
                <SelectItem value="Entertainment">Entertainment</SelectItem>
                <SelectItem value="NGO & Non-profit">NGO & Non-profit</SelectItem>
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex items-center space-x-2">
              <SortAsc className="h-4 w-4 text-muted-foreground" />
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created_at">Recently Added</SelectItem>
                  <SelectItem value="domain">Domain Name</SelectItem>
                  <SelectItem value="title">Title</SelectItem>
                  <SelectItem value="category">Category</SelectItem>
                  <SelectItem value="response_time">Response Time</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="space-y-6">
          {/* Results Count */}
          <div className="flex items-center justify-between">
            <p className="text-muted-foreground">
              {loading ? "Loading..." : `${filteredDomains.length} domains found`}
            </p>
          </div>

          {error && (
            <Card className="bg-red-500/10 border-red-500/20">
              <CardContent className="p-4 flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-red-400">Error loading domains</h3>
                  <p className="text-sm text-red-300 mt-1">{error}</p>
                  <Button variant="outline" size="sm" onClick={() => fetchDomains(true)} className="mt-3" disabled={retrying}>
                    {retrying ? "Retrying..." : "Try Again"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Domain Cards */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="bg-card/50 border-border/60 animate-pulse">
                  <CardHeader>
                    <div className="h-4 bg-muted rounded w-3/4"></div>
                    <div className="h-3 bg-muted rounded w-1/2"></div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="h-3 bg-muted rounded"></div>
                      <div className="h-3 bg-muted rounded w-2/3"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredDomains.length === 0 ? (
            <Card className="bg-card/50 border-border/60 text-center py-12">
              <CardContent>
                <Globe className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-foreground mb-2">No domains found</h3>
                <p className="text-muted-foreground">
                  Try adjusting your search terms or filters to find more results.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredDomains.map((domain) => (
                <Card key={domain.id} className="bg-card/50 border-border/60 hover:bg-card/70 transition-colors">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-lg font-semibold text-foreground truncate">
                          {domain.title || domain.domain}
                        </CardTitle>
                        <CardDescription className="text-primary font-mono text-sm">{domain.domain}</CardDescription>
                      </div>
                      <div className="flex items-center space-x-2 ml-2">
                        {(domain.has_ssl || domain.ssl_enabled) && (
                          <Shield className="h-4 w-4 text-green-400" title="SSL Enabled" />
                        )}
                        <Button variant="ghost" size="sm" asChild>
                          <a href={`https://${domain.domain}`} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {domain.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">{domain.description}</p>
                    )}

                    <div className="flex flex-wrap gap-2">
                      {domain.category && (
                        <Badge className={getCategoryColor(domain.category)} variant="outline">
                          {domain.category}
                        </Badge>
                      )}
                      <Badge className={getStatusColor(domain.status)} variant="outline">
                        {domain.status}
                      </Badge>
                    </div>

                    {domain.tags && domain.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {domain.tags.slice(0, 3).map((tag, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                        {domain.tags.length > 3 && (
                          <Badge variant="secondary" className="text-xs">
                            +{domain.tags.length - 3}
                          </Badge>
                        )}
                      </div>
                    )}

                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center space-x-1">
                        <Clock className="h-3 w-3" />
                        <span>{domain.response_time ? `${domain.response_time}ms` : "N/A"}</span>
                      </div>
                      <div>Added {new Date(domain.created_at).toLocaleDateString()}</div>
                    </div>

                    <Button variant="outline" size="sm" className="w-full bg-transparent" asChild>
                      <Link href={`/domain/${domain.domain}`}>View Details</Link>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
