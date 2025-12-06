"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Globe,
  Plus,
  Edit,
  Trash2,
  Activity,
  Database,
  RefreshCw,
  Settings,
  AlertCircle,
  CheckCircle,
  Clock,
} from "lucide-react"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"
import type { Domain, Category, CrawlLog } from "@/lib/types"
import type { User } from "@supabase/supabase-js"
import { useRouter } from "next/navigation"

export default function AdminDashboard() {
  const [domains, setDomains] = useState<Domain[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [crawlLogs, setCrawlLogs] = useState<CrawlLog[]>([])
  const [stats, setStats] = useState({
    totalDomains: 0,
    activeDomains: 0,
    inactiveDomains: 0,
    pendingDomains: 0,
    totalCategories: 0,
    recentCrawls: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [isAddDomainOpen, setIsAddDomainOpen] = useState(false)
  const [isAddCategoryOpen, setIsAddCategoryOpen] = useState(false)
  const [isAddingDomain, setIsAddingDomain] = useState(false)
  const [isAddingCategory, setIsAddingCategory] = useState(false)
  const [newDomain, setNewDomain] = useState({ domain: "", title: "", description: "", category: "", tags: "" })
  const [newCategory, setNewCategory] = useState({ name: "", description: "", color: "#3B82F6" })
  const router = useRouter()

  const supabase = createClient()

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const {
          data: { user },
          error,
        } = await supabase.auth.getUser()
        if (error) throw error

        if (!user) {
          router.push("/auth/login")
          return
        }

        setUser(user)
        setAuthLoading(false)
        fetchData()
      } catch (error) {
        console.error("[v0] Auth error:", error)
        router.push("/auth/login")
      }
    }

    checkAuth()

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === "SIGNED_OUT" || !session) {
        router.push("/auth/login")
      } else if (session?.user) {
        setUser(session.user)
        setAuthLoading(false)
      }
    })

    return () => subscription.unsubscribe()
  }, [router, supabase.auth])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      const domainsRes = await fetch("/api/domains?limit=50")
      if (!domainsRes.ok) throw new Error("Failed to fetch domains")
      const domainsData = await domainsRes.json()

      const categoriesRes = await fetch("/api/categories")
      if (!categoriesRes.ok) throw new Error("Failed to fetch categories")
      const categoriesData = await categoriesRes.json()

      const { data: logsData, error: logsError } = await supabase
        .from("crawl_logs")
        .select("*")
        .order("crawl_date", { ascending: false })
        .limit(20)

      if (logsError) throw logsError

      const domainsList = domainsData.domains || []
      const categoriesList = categoriesData.categories || []
      const totalDomains = domainsData.pagination?.total || domainsList.length || 0
      const activeDomains = domainsList.filter((d: Domain) => d.status === "active").length || 0
      const inactiveDomains = domainsList.filter((d: Domain) => d.status === "inactive").length || 0
      const pendingDomains = domainsList.filter((d: Domain) => d.status === "pending").length || 0
      const totalCategories = categoriesList.length || 0
      const recentCrawls =
        logsData?.filter((log) => new Date(log.crawl_date || "") > new Date(Date.now() - 24 * 60 * 60 * 1000)).length ||
        0

      setDomains(domainsList)
      setCategories(categoriesList)
      setCrawlLogs(logsData || [])
      setStats({
        totalDomains,
        activeDomains,
        inactiveDomains,
        pendingDomains,
        totalCategories,
        recentCrawls,
      })
    } catch (error) {
      console.error("[v0] Error fetching data:", error)
      setError(error instanceof Error ? error.message : "Failed to load data")
    } finally {
      setLoading(false)
    }
  }

  const handleAddDomain = async () => {
    try {
      if (!newDomain.domain) {
        setError("Domain is required")
        return
      }

      setIsAddingDomain(true)
      setError(null)

      const response = await fetch("/api/domains", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain: newDomain.domain,
          title: newDomain.title || null,
          description: newDomain.description || null,
          category: newDomain.category || null,
          tags: newDomain.tags ? newDomain.tags.split(",").map((tag) => tag.trim()) : null,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error || "Failed to add domain")
        return
      }

      setIsAddDomainOpen(false)
      setNewDomain({ domain: "", title: "", description: "", category: "", tags: "" })
      setSuccessMessage("Domain added successfully")
      setTimeout(() => setSuccessMessage(null), 3000)
      fetchData()
    } catch (error) {
      console.error("[v0] Error adding domain:", error)
      setError(error instanceof Error ? error.message : "Failed to add domain")
    } finally {
      setIsAddingDomain(false)
    }
  }

  const handleAddCategory = async () => {
    try {
      if (!newCategory.name) {
        setError("Category name is required")
        return
      }

      setIsAddingCategory(true)
      setError(null)

      const response = await fetch("/api/categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newCategory.name,
          description: newCategory.description || null,
          color: newCategory.color,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error || "Failed to add category")
        return
      }

      setIsAddCategoryOpen(false)
      setNewCategory({ name: "", description: "", color: "#3B82F6" })
      setSuccessMessage("Category added successfully")
      setTimeout(() => setSuccessMessage(null), 3000)
      fetchData()
    } catch (error) {
      console.error("[v0] Error adding category:", error)
      setError(error instanceof Error ? error.message : "Failed to add category")
    } finally {
      setIsAddingCategory(false)
    }
  }

  const handleDeleteDomain = async (id: string, domain: string) => {
    if (!confirm(`Are you sure you want to delete ${domain}?`)) return

    try {
      setError(null)
      const { error: deleteError } = await supabase.from("domains").delete().eq("id", id)

      if (deleteError) throw deleteError

      setSuccessMessage("Domain deleted successfully")
      setTimeout(() => setSuccessMessage(null), 3000)
      fetchData()
    } catch (error) {
      console.error("[v0] Error deleting domain:", error)
      setError(error instanceof Error ? error.message : "Failed to delete domain")
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

  const getCrawlStatusIcon = (responseCode?: number) => {
    if (!responseCode) return <AlertCircle className="h-4 w-4 text-gray-400" />
    if (responseCode >= 200 && responseCode < 300) return <CheckCircle className="h-4 w-4 text-green-400" />
    if (responseCode >= 500) return <AlertCircle className="h-4 w-4 text-red-400" />
    return <Clock className="h-4 w-4 text-yellow-400" />
  }

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push("/auth/login")
    } catch (error) {
      console.error("[v0] Logout error:", error)
      setError(error instanceof Error ? error.message : "Logout failed")
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Checking authentication...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
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
              <Badge variant="secondary">Admin</Badge>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/search" className="text-muted-foreground hover:text-foreground transition-colors">
                Search
              </Link>
              <Link href="/categories" className="text-muted-foreground hover:text-foreground transition-colors">
                Categories
              </Link>
              <Button variant="outline" size="sm" onClick={fetchData}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <span>{user.email}</span>
                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {successMessage && (
          <div className="mb-6 p-4 rounded-md bg-green-500/10 border border-green-500/20 flex items-start space-x-3">
            <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-green-400">Success</h3>
              <p className="text-sm text-green-300 mt-1">{successMessage}</p>
            </div>
            <button onClick={() => setSuccessMessage(null)} className="text-green-400 hover:text-green-300">
              ✕
            </button>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 rounded-md bg-red-500/10 border border-red-500/20 flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-red-400">Error</h3>
              <p className="text-sm text-red-300 mt-1">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
              ✕
            </button>
          </div>
        )}

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-4">Admin Dashboard</h1>
          <p className="text-muted-foreground text-lg">Manage domains, categories, and monitor system health</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-card/50 border-border/60">
            <CardHeader className="pb-3">
              <CardTitle className="text-2xl font-bold text-primary">{stats.totalDomains}</CardTitle>
              <CardDescription>Total Domains</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-muted-foreground">
                <Database className="h-4 w-4 mr-1" />
                All tracked domains
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/60">
            <CardHeader className="pb-3">
              <CardTitle className="text-2xl font-bold text-green-400">{stats.activeDomains}</CardTitle>
              <CardDescription>Active Domains</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-muted-foreground">
                <CheckCircle className="h-4 w-4 mr-1" />
                Currently online
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/60">
            <CardHeader className="pb-3">
              <CardTitle className="text-2xl font-bold text-primary">{stats.totalCategories}</CardTitle>
              <CardDescription>Categories</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-muted-foreground">
                <Settings className="h-4 w-4 mr-1" />
                Organization types
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/60">
            <CardHeader className="pb-3">
              <CardTitle className="text-2xl font-bold text-primary">{stats.recentCrawls}</CardTitle>
              <CardDescription>Recent Crawls</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-muted-foreground">
                <Activity className="h-4 w-4 mr-1" />
                Last 24 hours
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="domains" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="domains">Domains</TabsTrigger>
            <TabsTrigger value="categories">Categories</TabsTrigger>
            <TabsTrigger value="crawls">Crawl Logs</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="domains" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-foreground">Domain Management</h2>
              <Dialog open={isAddDomainOpen} onOpenChange={setIsAddDomainOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Domain
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Domain</DialogTitle>
                    <DialogDescription>Add a new domain to the database for tracking.</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="domain">Domain *</Label>
                      <Input
                        id="domain"
                        placeholder="example.com"
                        value={newDomain.domain}
                        onChange={(e) => setNewDomain({ ...newDomain, domain: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="title">Title</Label>
                      <Input
                        id="title"
                        placeholder="Website title"
                        value={newDomain.title}
                        onChange={(e) => setNewDomain({ ...newDomain, title: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="description">Description</Label>
                      <Textarea
                        id="description"
                        placeholder="Brief description of the website"
                        value={newDomain.description}
                        onChange={(e) => setNewDomain({ ...newDomain, description: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="category">Category</Label>
                      <Select
                        value={newDomain.category}
                        onValueChange={(value) => setNewDomain({ ...newDomain, category: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map((category) => (
                            <SelectItem key={category.id} value={category.name}>
                              {category.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="tags">Tags (comma-separated)</Label>
                      <Input
                        id="tags"
                        placeholder="tag1, tag2, tag3"
                        value={newDomain.tags}
                        onChange={(e) => setNewDomain({ ...newDomain, tags: e.target.value })}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddDomainOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddDomain} disabled={!newDomain.domain || isAddingDomain}>
                      {isAddingDomain ? "Adding..." : "Add Domain"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            <Card className="bg-card/50 border-border/60">
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Domain</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Added</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {loading ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8">
                          <div className="flex items-center justify-center space-x-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                            <span className="text-muted-foreground">Loading domains...</span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : domains.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                          No domains found. Add your first domain to get started.
                        </TableCell>
                      </TableRow>
                    ) : (
                      domains.map((domain) => (
                        <TableRow key={domain.id}>
                          <TableCell className="font-mono text-sm">{domain.domain}</TableCell>
                          <TableCell className="max-w-[200px] truncate">{domain.title || "-"}</TableCell>
                          <TableCell>{domain.category || "-"}</TableCell>
                          <TableCell>
                            <Badge className={getStatusColor(domain.status)} variant="outline">
                              {domain.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {new Date(domain.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm">
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-red-400 hover:text-red-300"
                                onClick={() => handleDeleteDomain(domain.id, domain.domain)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="categories" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-foreground">Category Management</h2>
              <Dialog open={isAddCategoryOpen} onOpenChange={setIsAddCategoryOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Category
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Category</DialogTitle>
                    <DialogDescription>Create a new category for organizing domains.</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="categoryName">Name *</Label>
                      <Input
                        id="categoryName"
                        placeholder="Category name"
                        value={newCategory.name}
                        onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="categoryDescription">Description</Label>
                      <Textarea
                        id="categoryDescription"
                        placeholder="Category description"
                        value={newCategory.description}
                        onChange={(e) => setNewCategory({ ...newCategory, description: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="categoryColor">Color</Label>
                      <Input
                        id="categoryColor"
                        type="color"
                        value={newCategory.color}
                        onChange={(e) => setNewCategory({ ...newCategory, color: e.target.value })}
                        className="h-10 w-20"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddCategoryOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddCategory} disabled={!newCategory.name || isAddingCategory}>
                      {isAddingCategory ? "Adding..." : "Add Category"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map((category) => (
                <Card key={category.id} className="bg-card/50 border-border/60">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: category.color || "#3B82F6" }}
                        />
                        <CardTitle className="text-lg">{category.name}</CardTitle>
                      </div>
                    </div>
                    {category.description && (
                      <CardDescription className="text-sm">{category.description}</CardDescription>
                    )}
                  </CardHeader>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="crawls" className="space-y-6">
            <h2 className="text-xl font-semibold text-foreground">Recent Crawl Logs</h2>
            <Card className="bg-card/50 border-border/60">
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Status</TableHead>
                      <TableHead>Response</TableHead>
                      <TableHead>Time</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Error</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {crawlLogs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                          No crawl logs found.
                        </TableCell>
                      </TableRow>
                    ) : (
                      crawlLogs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell>{getCrawlStatusIcon(log.response_code)}</TableCell>
                          <TableCell>{log.response_code || "-"}</TableCell>
                          <TableCell>{log.response_time ? `${log.response_time}ms` : "-"}</TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {log.crawl_date ? new Date(log.crawl_date).toLocaleString() : "-"}
                          </TableCell>
                          <TableCell className="text-red-400 text-sm max-w-[200px] truncate">
                            {log.error_message || "-"}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <h2 className="text-xl font-semibold text-foreground">System Settings</h2>
            <Card className="bg-card/50 border-border/60">
              <CardHeader>
                <CardTitle>Crawler Configuration</CardTitle>
                <CardDescription>Configure the web crawler settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">Settings panel coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
