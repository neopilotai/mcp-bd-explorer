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
  TrendingUp,
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
  const [user, setUser] = useState<User | null>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [isAddDomainOpen, setIsAddDomainOpen] = useState(false)
  const [isAddCategoryOpen, setIsAddCategoryOpen] = useState(false)
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
        console.error("Auth error:", error)
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

      // Fetch domains
      const { data: domainsData, error: domainsError } = await supabase
        .from("domains")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(50)

      if (domainsError) throw domainsError

      // Fetch categories
      const { data: categoriesData, error: categoriesError } = await supabase
        .from("categories")
        .select("*")
        .order("name")

      if (categoriesError) throw categoriesError

      // Fetch recent crawl logs
      const { data: logsData, error: logsError } = await supabase
        .from("crawl_logs")
        .select("*")
        .order("crawl_date", { ascending: false })
        .limit(20)

      if (logsError) throw logsError

      // Calculate stats
      const totalDomains = domainsData?.length || 0
      const activeDomains = domainsData?.filter((d) => d.status === "active").length || 0
      const inactiveDomains = domainsData?.filter((d) => d.status === "inactive").length || 0
      const pendingDomains = domainsData?.filter((d) => d.status === "pending").length || 0
      const totalCategories = categoriesData?.length || 0
      const recentCrawls =
        logsData?.filter((log) => new Date(log.crawl_date) > new Date(Date.now() - 24 * 60 * 60 * 1000)).length || 0

      setDomains(domainsData || [])
      setCategories(categoriesData || [])
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
      console.error("Error fetching data:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddDomain = async () => {
    try {
      const { error } = await supabase.from("domains").insert({
        domain: newDomain.domain,
        title: newDomain.title || null,
        description: newDomain.description || null,
        category: newDomain.category || null,
        tags: newDomain.tags ? newDomain.tags.split(",").map((tag) => tag.trim()) : null,
        status: "pending",
        ssl_enabled: false,
      })

      if (error) throw error

      setIsAddDomainOpen(false)
      setNewDomain({ domain: "", title: "", description: "", category: "", tags: "" })
      fetchData()
    } catch (error) {
      console.error("Error adding domain:", error)
    }
  }

  const handleAddCategory = async () => {
    try {
      const { error } = await supabase.from("categories").insert({
        name: newCategory.name,
        description: newCategory.description || null,
        color: newCategory.color,
      })

      if (error) throw error

      setIsAddCategoryOpen(false)
      setNewCategory({ name: "", description: "", color: "#3B82F6" })
      fetchData()
    } catch (error) {
      console.error("Error adding category:", error)
    }
  }

  const handleDeleteDomain = async (id: string) => {
    try {
      const { error } = await supabase.from("domains").delete().eq("id", id)

      if (error) throw error

      fetchData()
    } catch (error) {
      console.error("Error deleting domain:", error)
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
        return <AlertCircle className="h-4 w-4 text-red-400" />
      case "timeout":
        return <Clock className="h-4 w-4 text-yellow-400" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />
    }
  }

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push("/auth/login")
    } catch (error) {
      console.error("Logout error:", error)
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
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-4">Admin Dashboard</h1>
          <p className="text-muted-foreground text-lg">Manage domains, categories, and monitor system health</p>
        </div>

        {/* Stats Cards */}
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

        {/* Main Content */}
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
                    <Button onClick={handleAddDomain} disabled={!newDomain.domain}>
                      Add Domain
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
                      [...Array(5)].map((_, i) => (
                        <TableRow key={i}>
                          <TableCell>
                            <div className="h-4 bg-muted rounded animate-pulse"></div>
                          </TableCell>
                          <TableCell>
                            <div className="h-4 bg-muted rounded animate-pulse"></div>
                          </TableCell>
                          <TableCell>
                            <div className="h-4 bg-muted rounded animate-pulse"></div>
                          </TableCell>
                          <TableCell>
                            <div className="h-4 bg-muted rounded animate-pulse"></div>
                          </TableCell>
                          <TableCell>
                            <div className="h-4 bg-muted rounded animate-pulse"></div>
                          </TableCell>
                          <TableCell>
                            <div className="h-4 bg-muted rounded animate-pulse"></div>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : domains.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                          No domains found
                        </TableCell>
                      </TableRow>
                    ) : (
                      domains.map((domain) => (
                        <TableRow key={domain.id}>
                          <TableCell className="font-mono text-primary">{domain.domain}</TableCell>
                          <TableCell className="max-w-48 truncate">{domain.title || "—"}</TableCell>
                          <TableCell>{domain.category || "—"}</TableCell>
                          <TableCell>
                            <Badge className={getStatusColor(domain.status)} variant="outline">
                              {domain.status}
                            </Badge>
                          </TableCell>
                          <TableCell>{new Date(domain.created_at).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm" asChild>
                                <Link href={`/domain/${domain.domain}`}>
                                  <Edit className="h-4 w-4" />
                                </Link>
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteDomain(domain.id)}
                                className="text-red-400 hover:text-red-300"
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
                        placeholder="Brief description of the category"
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
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddCategoryOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddCategory} disabled={!newCategory.name}>
                      Add Category
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {categories.map((category) => (
                <Card key={category.id} className="bg-card/50 border-border/60">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{category.name}</CardTitle>
                      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: category.color }}></div>
                    </div>
                    {category.description && <CardDescription>{category.description}</CardDescription>}
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">
                        {domains.filter((d) => d.category === category.name).length} domains
                      </span>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="crawls" className="space-y-6">
            <h2 className="text-xl font-semibold text-foreground">Recent Crawl Activity</h2>

            <Card className="bg-card/50 border-border/60">
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Status</TableHead>
                      <TableHead>Domain</TableHead>
                      <TableHead>Response Code</TableHead>
                      <TableHead>Response Time</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {crawlLogs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                          No crawl logs found
                        </TableCell>
                      </TableRow>
                    ) : (
                      crawlLogs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              {getCrawlStatusIcon(log.status)}
                              <span className="capitalize">{log.status}</span>
                            </div>
                          </TableCell>
                          <TableCell className="font-mono text-primary">
                            {domains.find((d) => d.id === log.domain_id)?.domain || "Unknown"}
                          </TableCell>
                          <TableCell>{log.response_code || "—"}</TableCell>
                          <TableCell>{log.response_time ? `${log.response_time}ms` : "—"}</TableCell>
                          <TableCell>{new Date(log.crawl_date).toLocaleString()}</TableCell>
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="bg-card/50 border-border/60">
                <CardHeader>
                  <CardTitle>Crawler Settings</CardTitle>
                  <CardDescription>Configure automated crawling behavior</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Crawl Interval</Label>
                    <Select defaultValue="daily">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="hourly">Hourly</SelectItem>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Timeout (seconds)</Label>
                    <Input type="number" defaultValue="30" />
                  </div>
                  <Button>Save Settings</Button>
                </CardContent>
              </Card>

              <Card className="bg-card/50 border-border/60">
                <CardHeader>
                  <CardTitle>Database Maintenance</CardTitle>
                  <CardDescription>Manage database operations</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button variant="outline" className="w-full bg-transparent">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh All Data
                  </Button>
                  <Button variant="outline" className="w-full bg-transparent">
                    <Database className="h-4 w-4 mr-2" />
                    Backup Database
                  </Button>
                  <Button variant="outline" className="w-full bg-transparent">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Generate Report
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
