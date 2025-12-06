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
  response_code: number
  response_time: number
  page_size: number
  ssl_enabled: boolean
  server?: string
  content_type?: string
  error_message?: string
}

async function crawlWebsite(domain: string): Promise<CrawlResult> {
  const startTime = Date.now()

  try {
    const url = domain.startsWith("http") ? domain : `https://${domain}`

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "User-Agent": "MCP-BD-Explorer/1.0 (Website Directory Crawler)",
      },
      redirect: "follow",
      signal: AbortSignal.timeout(30000),
    })

    const responseTime = Date.now() - startTime
    const html = await response.text()
    const pageSize = new Blob([html]).size

    const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i)
    const descriptionMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i)

    return {
      domain: new URL(url).hostname || domain,
      title: titleMatch ? titleMatch[1].trim() : undefined,
      description: descriptionMatch ? descriptionMatch[1].trim() : undefined,
      response_code: response.status,
      response_time: responseTime,
      page_size: pageSize,
      ssl_enabled: url.startsWith("https://"),
      server: response.headers.get("server") || undefined,
      content_type: response.headers.get("content-type") || undefined,
    }
  } catch (error) {
    const responseTime = Date.now() - startTime
    return {
      domain: domain.replace(/^https?:\/\//, ""),
      response_code: 0,
      response_time: responseTime,
      page_size: 0,
      ssl_enabled: false,
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

    const { data: existingDomain, error: fetchError } = await supabase
      .from("domains")
      .select("*")
      .eq("domain", domain.replace(/^https?:\/\//, ""))
      .single()

    if (fetchError && fetchError.code !== "PGRST116") {
      throw fetchError
    }

    if (existingDomain && !force) {
      const lastCrawled = new Date(existingDomain.last_crawled || 0)
      const hoursSinceLastCrawl = (Date.now() - lastCrawled.getTime()) / (1000 * 60 * 60)

      if (hoursSinceLastCrawl < 24) {
        return NextResponse.json({
          message: "Domain was recently crawled",
          domain: existingDomain,
          skipped: true,
        })
      }
    }

    const crawlResult = await crawlWebsite(domain)

    const { error: logError } = await supabase.from("crawl_logs").insert({
      domain_id: existingDomain?.id || null,
      response_code: crawlResult.response_code,
      response_time: crawlResult.response_time,
      error_message: crawlResult.error_message,
      crawl_date: new Date().toISOString(),
      status: crawlResult.response_code >= 200 && crawlResult.response_code < 300 ? "success" : "failed",
    })

    if (logError) {
      console.error("[v0] Failed to log crawl:", logError)
    }

    const domainData = {
      domain: crawlResult.domain,
      title: crawlResult.title,
      description: crawlResult.description,
      status: crawlResult.response_code >= 200 && crawlResult.response_code < 300 ? "active" : "inactive",
      last_crawled: new Date().toISOString(),
      response_time: crawlResult.response_time,
      ssl_enabled: crawlResult.ssl_enabled,
      server_info: crawlResult.server ? { server: crawlResult.server, content_type: crawlResult.content_type } : null,
    }

    if (existingDomain) {
      const { data: updatedDomain, error: updateError } = await supabase
        .from("domains")
        .update(domainData)
        .eq("id", existingDomain.id)
        .select()
        .single()

      if (updateError) throw updateError

      return NextResponse.json({
        message: "Domain updated successfully",
        domain: updatedDomain,
        crawlResult,
      })
    } else {
      const { data: newDomain, error: insertError } = await supabase
        .from("domains")
        .insert(domainData)
        .select()
        .single()

      if (insertError) throw insertError

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
    console.error("[v0] Crawl API error:", error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 },
    )
  }
}
