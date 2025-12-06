import { type NextRequest, NextResponse } from "next/server"
import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"
import { validateEnvVariables, createErrorResponse } from "@/lib/utils/error-handler"
import { logger } from "@/lib/utils/logger"

export async function GET() {
  try {
    if (!validateEnvVariables(["NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_ANON_KEY"])) {
      logger.error("Missing Supabase environment variables")
      return NextResponse.json(
        { error: "Server not properly configured" },
        { status: 500 }
      )
    }

    const cookieStore = await cookies()
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL,
      process.env.SUPABASE_ANON_KEY,
      {
        cookies: {
          get(name: string) {
            return cookieStore.get(name)?.value
          },
        },
      }
    )

    const { data: categories, error } = await supabase
      .from("categories")
      .select(`
        *,
        domain_count:domains(count)
      `)
      .order("name")

    if (error) {
      console.error("[v0] Database error:", error)
      return NextResponse.json({ error: "Failed to fetch categories" }, { status: 500 })
    }

    // Transform the data to include domain counts
    const categoriesWithCounts =
      categories?.map((category) => ({
        ...category,
        domain_count: category.domain_count?.[0]?.count || 0,
      })) || []

    return NextResponse.json({
      categories: categoriesWithCounts,
    })
  } catch (error) {
    const appError = createErrorResponse(error, "Failed to fetch categories", "GET /api/categories")
    return NextResponse.json({ error: appError.message }, { status: appError.statusCode })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, description, color } = body

    if (!name) {
      logger.warn("Category creation attempted without name")
      return NextResponse.json({ error: "Category name is required" }, { status: 400 })
    }

    if (!validateEnvVariables(["NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"])) {
      logger.error("Missing Supabase service role key")
      return NextResponse.json(
        { error: "Server not properly configured" },
        { status: 500 }
      )
    }

    const cookieStore = await cookies()
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL,
      process.env.SUPABASE_SERVICE_ROLE_KEY,
      {
        cookies: {
          get(name: string) {
            return cookieStore.get(name)?.value
          },
        },
      }
    )

    const { data: newCategory, error } = await supabase
      .from("categories")
      .insert({
        name,
        description: description || null,
        color: color || "#3B82F6",
        created_at: new Date().toISOString(),
      })
      .select()
      .single()

    if (error) {
      console.error("[v0] Database error:", error)
      return NextResponse.json({ error: "Failed to create category" }, { status: 500 })
    }

    return NextResponse.json(
      {
        message: "Category created successfully",
        category: newCategory,
      },
      { status: 201 }
    )
  } catch (error) {
    const appError = createErrorResponse(error, "Failed to create category", "POST /api/categories")
    return NextResponse.json({ error: appError.message }, { status: appError.statusCode })
  }
}
