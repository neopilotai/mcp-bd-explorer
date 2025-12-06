import { type NextRequest, NextResponse } from "next/server"
import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"

export async function GET(request: NextRequest) {
  try {
    if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.SUPABASE_SERVICE_ROLE_KEY) {
      console.error("[v0] Missing Supabase environment variables")
      return NextResponse.json({ error: "Server configuration error" }, { status: 500 })
    }

    const cookieStore = await cookies()
    const supabase = createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY, {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    })

    const { data: recentCrawls } = await supabase
      .from("crawl_logs")
      .select("*")
      .gte("crawl_date", new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
      .order("crawl_date", { ascending: false })

    const { data: domainStats } = await supabase.from("domains").select("status, category")

    const totalDomains = domainStats?.length || 0
    const activeDomains = domainStats?.filter((d) => d.status === "active").length || 0
    const inactiveDomains = domainStats?.filter((d) => d.status === "inactive").length || 0

    const categoryStats =
      domainStats?.reduce(
        (acc, domain) => {
          const category = domain.category || "uncategorized"
          acc[category] = (acc[category] || 0) + 1
          return acc
        },
        {} as Record<string, number>,
      ) || {}

    const recentCrawlsCount = recentCrawls?.length || 0
    const successfulCrawls = recentCrawls?.filter((c) => c.response_code >= 200 && c.response_code < 300).length || 0
    const failedCrawls = recentCrawlsCount - successfulCrawls

    const averageResponseTime = recentCrawls?.length
      ? recentCrawls.reduce((sum, crawl) => sum + (crawl.response_time || 0), 0) / recentCrawls.length
      : 0

    return NextResponse.json({
      crawler_status: "operational",
      statistics: {
        total_domains: totalDomains,
        active_domains: activeDomains,
        inactive_domains: inactiveDomains,
        recent_crawls_24h: recentCrawlsCount,
        successful_crawls_24h: successfulCrawls,
        failed_crawls_24h: failedCrawls,
        average_response_time: Math.round(averageResponseTime),
        category_distribution: categoryStats,
      },
      recent_crawls: recentCrawls?.slice(0, 10) || [],
    })
  } catch (error) {
    console.error("[v0] Crawler status API error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
