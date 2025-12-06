import { logger } from "./logger"

export interface FetchOptions extends RequestInit {
  retries?: number
  retryDelay?: number
}

interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  statusCode: number
}

export async function apiCall<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<ApiResponse<T>> {
  const { retries = 3, retryDelay = 1000, ...fetchOptions } = options
  const startTime = Date.now()
  let lastError: Error | null = null

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      logger.debug(`Fetching ${endpoint}`, { attempt, retries })

      const response = await fetch(endpoint, {
        ...fetchOptions,
        headers: {
          "Content-Type": "application/json",
          ...fetchOptions.headers,
        },
      })

      const duration = Date.now() - startTime
      logger.apiCall(fetchOptions.method || "GET", endpoint, response.status, duration)

      const data = await response.json()

      if (!response.ok) {
        if (attempt < retries && response.status >= 500) {
          lastError = new Error(data.error || `HTTP ${response.status}`)
          await new Promise(resolve => setTimeout(resolve, retryDelay * attempt))
          continue
        }

        return {
          success: false,
          error: data.error || `HTTP ${response.status}`,
          statusCode: response.status,
        }
      }

      return {
        success: true,
        data,
        statusCode: response.status,
      }
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error))
      if (attempt < retries) {
        logger.warn(`Request failed (attempt ${attempt}/${retries})`, undefined, {
          error: lastError.message,
        })
        await new Promise(resolve => setTimeout(resolve, retryDelay * attempt))
        continue
      }
    }
  }

  logger.error(`Failed after ${retries} attempts`, lastError, { endpoint })
  return {
    success: false,
    error: lastError?.message || "Failed to fetch data",
    statusCode: 0,
  }
}
