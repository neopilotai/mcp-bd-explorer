import { type NextRequest, NextResponse } from "next/server"
import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"

interface BatchCrawlRequest {
  domains: string[]
  force?: boolean
  category?: string
}

export async function POST(request: NextRequest) {
  try {
    const body: BatchCrawlRequest = await request.json()
    const { domains, force = false, category } = body

    if (!domains || !Array.isArray(domains) || domains.length === 0) {
      return NextResponse.json({ error: "Domains array is required" }, { status: 400 })
    }

    if (domains.length > 50) {
      return NextResponse.json({ error: "Maximum 50 domains per batch" }, { status: 400 })
    }

    const cookieStore = cookies()
    const supabase = createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    })

    const results = []
    const errors = []

    // Process domains in parallel with concurrency limit
    const concurrencyLimit = 5
    const chunks = []
    for (let i = 0; i < domains.length; i += concurrencyLimit) {
      chunks.push(domains.slice(i, i + concurrencyLimit))
    }

    for (const chunk of chunks) {
      const chunkPromises = chunk.map(async (domain) => {
        try {
          // Call the single crawl API
          const crawlResponse = await fetch(`${request.nextUrl.origin}/api/crawler/crawl`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ domain, force }),
          })

          const crawlResult = await crawlResponse.json()

          // If category is specified and domain was successfully crawled, update category
          if (category && crawlResult.domain && !crawlResult.error) {
            await supabase.from("domains").update({ category }).eq("domain", crawlResult.domain.domain)
          }

          return {
            domain,
            success: crawlResponse.ok,
            result: crawlResult,
          }
        } catch (error) {
          return {
            domain,
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
          }
        }
      })

      const chunkResults = await Promise.all(chunkPromises)

      chunkResults.forEach((result) => {
        if (result.success) {
          results.push(result)
        } else {
          errors.push(result)
        }
      })

      // Small delay between chunks to avoid overwhelming the server
      if (chunks.indexOf(chunk) < chunks.length - 1) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
      }
    }

    return NextResponse.json({
      message: `Batch crawl completed. ${results.length} successful, ${errors.length} failed.`,
      successful: results,
      failed: errors,
      summary: {
        total: domains.length,
        successful: results.length,
        failed: errors.length,
      },
    })
  } catch (error) {
    console.error("Batch crawl API error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
