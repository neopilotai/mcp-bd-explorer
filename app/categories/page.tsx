"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Globe, TrendingUp } from "lucide-react"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"
import type { Category } from "@/lib/types"

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [domainCounts, setDomainCounts] = useState<{ [key: string]: number }>({})
  const [loading, setLoading] = useState(true)

  const supabase = createClient()

  useEffect(() => {
    fetchCategoriesAndCounts()
  }, [])

  const fetchCategoriesAndCounts = async () => {
    try {
      setLoading(true)

      // Fetch categories
      const { data: categoriesData, error: categoriesError } = await supabase
        .from("categories")
        .select("*")
        .order("name")

      if (categoriesError) throw categoriesError

      // Fetch domain counts by category
      const { data: domainsData, error: domainsError } = await supabase.from("domains").select("category")

      if (domainsError) throw domainsError

      // Count domains by category
      const counts: { [key: string]: number } = {}
      domainsData?.forEach((domain) => {
        if (domain.category) {
          counts[domain.category] = (counts[domain.category] || 0) + 1
        }
      })

      setCategories(categoriesData || [])
      setDomainCounts(counts)
    } catch (error) {
      console.error("Error fetching categories:", error)
    } finally {
      setLoading(false)
    }
  }

  const getCategoryColor = (color?: string) => {
    if (!color) return "bg-gray-500/10 text-gray-400 border-gray-500/20"

    const colorMap: { [key: string]: string } = {
      "#3B82F6": "bg-blue-500/10 text-blue-400 border-blue-500/20",
      "#10B981": "bg-green-500/10 text-green-400 border-green-500/20",
      "#F59E0B": "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
      "#EF4444": "bg-red-500/10 text-red-400 border-red-500/20",
      "#8B5CF6": "bg-purple-500/10 text-purple-400 border-purple-500/20",
      "#06B6D4": "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
      "#84CC16": "bg-lime-500/10 text-lime-400 border-lime-500/20",
      "#F97316": "bg-orange-500/10 text-orange-400 border-orange-500/20",
      "#EC4899": "bg-pink-500/10 text-pink-400 border-pink-500/20",
      "#6366F1": "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    }

    return colorMap[color] || "bg-gray-500/10 text-gray-400 border-gray-500/20"
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
              <Link href="/categories" className="text-primary font-medium">
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
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-4">Website Categories</h1>
          <p className="text-muted-foreground text-lg">
            Explore Bangladeshi websites organized by industry and purpose
          </p>
        </div>

        {/* Categories Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <Card key={i} className="bg-card/50 border-border/60 animate-pulse">
                <CardHeader>
                  <div className="h-6 bg-muted rounded w-3/4"></div>
                  <div className="h-4 bg-muted rounded w-1/2"></div>
                </CardHeader>
                <CardContent>
                  <div className="h-4 bg-muted rounded w-1/4"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {categories.map((category) => (
              <Card
                key={category.id}
                className={`cursor-pointer transition-all hover:scale-105 ${getCategoryColor(category.color)} border`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold">{category.name}</CardTitle>
                    <TrendingUp className="h-5 w-5 opacity-60" />
                  </div>
                  {category.description && (
                    <CardDescription className="text-sm opacity-80">{category.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Badge variant="secondary" className="text-xs">
                      {domainCounts[category.name] || 0} domains
                    </Badge>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full bg-background/50 hover:bg-background/80"
                    asChild
                  >
                    <Link href={`/search?category=${encodeURIComponent(category.name)}`}>Explore Category</Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Statistics */}
        <div className="mt-12 bg-card/30 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">Category Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{categories.length}</div>
              <div className="text-sm text-muted-foreground">Total Categories</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {Object.values(domainCounts).reduce((sum, count) => sum + count, 0)}
              </div>
              <div className="text-sm text-muted-foreground">Total Domains</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {Math.round(Object.values(domainCounts).reduce((sum, count) => sum + count, 0) / categories.length)}
              </div>
              <div className="text-sm text-muted-foreground">Avg per Category</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{Math.max(...Object.values(domainCounts), 0)}</div>
              <div className="text-sm text-muted-foreground">Largest Category</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
