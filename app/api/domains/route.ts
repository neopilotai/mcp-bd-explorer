import { type NextRequest, NextResponse } from "next/server"
import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const page = Number.parseInt(searchParams.get("page") || "1")
    const limit = Math.min(Number.parseInt(searchParams.get("limit") || "20"), 100)
    const search = searchParams.get("search") || ""
    const category = searchParams.get("category") || ""
    const status = searchParams.get("status") || ""
    const sortBy = searchParams.get("sortBy") || "last_crawled"
    const sortOrder = searchParams.get("sortOrder") || "desc"

    const cookieStore = cookies()
    const supabase = createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_ANON_KEY!, {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    })

    let query = supabase.from("domains").select("*", { count: "exact" })

    // Apply filters
    if (search) {
      query = query.or(
        `domain.ilike.%${search}%,title.ilike.%${search}%,description.ilike.%${search}%,tags.ilike.%${search}%`,
      )
    }

    if (category) {
      query = query.eq("category", category)
    }

    if (status) {
      query = query.eq("status", status)
    }

    // Apply sorting
    const ascending = sortOrder === "asc"
    query = query.order(sortBy, { ascending })

    // Apply pagination
    const from = (page - 1) * limit
    const to = from + limit - 1
    query = query.range(from, to)

    const { data: domains, error, count } = await query

    if (error) {
      console.error("Database error:", error)
      return NextResponse.json({ error: "Database error" }, { status: 500 })
    }

    const totalPages = Math.ceil((count || 0) / limit)

    return NextResponse.json({
      domains: domains || [],
      pagination: {
        page,
        limit,
        total: count || 0,
        totalPages,
        hasNext: page < totalPages,
        hasPrev: page > 1,
      },
      filters: {
        search,
        category,
        status,
        sortBy,
        sortOrder,
      },
    })
  } catch (error) {
    console.error("Domains API error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { domain, title, description, category, tags } = body

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

    // Check if domain already exists
    const { data: existingDomain } = await supabase
      .from("domains")
      .select("id")
      .eq("domain", domain.replace(/^https?:\/\//, ""))
      .single()

    if (existingDomain) {
      return NextResponse.json({ error: "Domain already exists" }, { status: 409 })
    }

    const { data: newDomain, error } = await supabase
      .from("domains")
      .insert({
        domain: domain.replace(/^https?:\/\//, ""),
        title,
        description,
        category,
        tags,
        status: "pending",
        created_at: new Date().toISOString(),
      })
      .select()
      .single()

    if (error) {
      console.error("Database error:", error)
      return NextResponse.json({ error: "Database error" }, { status: 500 })
    }

    return NextResponse.json(
      {
        message: "Domain added successfully",
        domain: newDomain,
      },
      { status: 201 },
    )
  } catch (error) {
    console.error("Add domain API error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
