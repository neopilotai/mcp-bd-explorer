import { type NextRequest, NextResponse } from "next/server"
import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"

interface CrawlRequest {
  domain: string
  force?: boolean
}

interface CrawlResult {
  domain: string
  title?: string
  description?: string
  status_code: number
  response_time: number
  page_size: number
  has_ssl: boolean
  server?: string
  content_type?: string
  meta_keywords?: string
  meta_author?: string
  language?: string
  favicon_url?: string
  error_message?: string
}

async function crawlWebsite(domain: string): Promise<CrawlResult> {
  const startTime = Date.now()

  try {
    // Ensure domain has protocol
    const url = domain.startsWith("http") ? domain : `https://${domain}`

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "User-Agent": "MCP-BD-Explorer/1.0 (Website Directory Crawler)",
      },
      redirect: "follow",
      signal: AbortSignal.timeout(30000), // 30 second timeout
    })

    const responseTime = Date.now() - startTime
    const html = await response.text()
    const pageSize = new Blob([html]).size

    // Extract metadata from HTML
    const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i)
    const descriptionMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i)
    const keywordsMatch = html.match(/<meta[^>]*name=["']keywords["'][^>]*content=["']([^"']+)["']/i)
    const authorMatch = html.match(/<meta[^>]*name=["']author["'][^>]*content=["']([^"']+)["']/i)
    const langMatch = html.match(/<html[^>]*lang=["']([^"']+)["']/i)

    // Extract favicon
    const faviconMatch = html.match(/<link[^>]*rel=["'](?:icon|shortcut icon)["'][^>]*href=["']([^"']+)["']/i)
    let faviconUrl = faviconMatch ? faviconMatch[1] : null
    if (faviconUrl && !faviconUrl.startsWith("http")) {
      const baseUrl = new URL(url)
      faviconUrl = faviconUrl.startsWith("/")
        ? `${baseUrl.protocol}//${baseUrl.host}${faviconUrl}`
        : `${baseUrl.protocol}//${baseUrl.host}/${faviconUrl}`
    }

    return {
      domain: new URL(url).hostname,
      title: titleMatch ? titleMatch[1].trim() : undefined,
      description: descriptionMatch ? descriptionMatch[1].trim() : undefined,
      status_code: response.status,
      response_time: responseTime,
      page_size: pageSize,
      has_ssl: url.startsWith("https://"),
      server: response.headers.get("server") || undefined,
      content_type: response.headers.get("content-type") || undefined,
      meta_keywords: keywordsMatch ? keywordsMatch[1].trim() : undefined,
      meta_author: authorMatch ? authorMatch[1].trim() : undefined,
      language: langMatch ? langMatch[1].trim() : undefined,
      favicon_url: faviconUrl || undefined,
    }
  } catch (error) {
    const responseTime = Date.now() - startTime
    return {
      domain: domain.replace(/^https?:\/\//, ""),
      status_code: 0,
      response_time: responseTime,
      page_size: 0,
      has_ssl: false,
      error_message: error instanceof Error ? error.message : "Unknown error",
    }
  }
}

export async function POST(request: NextRequest) {
  try {
    const body: CrawlRequest = await request.json()
    const { domain, force = false } = body

    if (!domain) {
      return NextResponse.json({ error: "Domain is required" }, { status: 400 })
    }

    const cookieStore = cookies()
    const supabase = createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    })

    // Check if domain exists and when it was last crawled
    const { data: existingDomain } = await supabase
      .from("domains")
      .select("*")
      .eq("domain", domain.replace(/^https?:\/\//, ""))
      .single()

    // Skip if recently crawled (within 24 hours) unless forced
    if (existingDomain && !force) {
      const lastCrawled = new Date(existingDomain.last_crawled)
      const hoursSinceLastCrawl = (Date.now() - lastCrawled.getTime()) / (1000 * 60 * 60)

      if (hoursSinceLastCrawl < 24) {
        return NextResponse.json({
          message: "Domain was recently crawled",
          domain: existingDomain,
          skipped: true,
        })
      }
    }

    // Perform the crawl
    const crawlResult = await crawlWebsite(domain)

    // Log the crawl attempt
    await supabase.from("crawl_logs").insert({
      domain: crawlResult.domain,
      status_code: crawlResult.status_code,
      response_time: crawlResult.response_time,
      error_message: crawlResult.error_message,
      crawled_at: new Date().toISOString(),
    })

    // Update or insert domain data
    const domainData = {
      domain: crawlResult.domain,
      title: crawlResult.title,
      description: crawlResult.description,
      status: crawlResult.status_code >= 200 && crawlResult.status_code < 300 ? "active" : "inactive",
      last_crawled: new Date().toISOString(),
      response_time: crawlResult.response_time,
      page_size: crawlResult.page_size,
      has_ssl: crawlResult.has_ssl,
      server: crawlResult.server,
      content_type: crawlResult.content_type,
      meta_keywords: crawlResult.meta_keywords,
      meta_author: crawlResult.meta_author,
      language: crawlResult.language,
      favicon_url: crawlResult.favicon_url,
    }

    if (existingDomain) {
      const { data: updatedDomain } = await supabase
        .from("domains")
        .update(domainData)
        .eq("id", existingDomain.id)
        .select()
        .single()

      return NextResponse.json({
        message: "Domain updated successfully",
        domain: updatedDomain,
        crawlResult,
      })
    } else {
      const { data: newDomain } = await supabase.from("domains").insert(domainData).select().single()

      return NextResponse.json(
        {
          message: "Domain added successfully",
          domain: newDomain,
          crawlResult,
        },
        { status: 201 },
      )
    }
  } catch (error) {
    console.error("Crawl API error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
