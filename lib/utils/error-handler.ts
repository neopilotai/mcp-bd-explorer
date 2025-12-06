import type { NextResponse } from "next/server"
import { logger } from "./logger"

export interface AppError {
  code: string
  message: string
  statusCode: number
  details?: Record<string, unknown>
}

// Custom error class for type-safe error handling
export class APIError extends Error {
  constructor(
    public code: string,
    public statusCode: number,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = "APIError"
  }
}

// Error response builder
export const createErrorResponse = (
  error: unknown,
  defaultMessage: string,
  context: string
): AppError => {
  if (error instanceof APIError) {
    logger.error(`${context}: ${error.message}`, error, {
      code: error.code,
      statusCode: error.statusCode,
    })
    return {
      code: error.code,
      message: error.message,
      statusCode: error.statusCode,
      details: error.details,
    }
  }

  const message = error instanceof Error ? error.message : String(error)
  logger.error(`${context}: ${message}`, error)

  return {
    code: "INTERNAL_ERROR",
    message: defaultMessage,
    statusCode: 500,
  }
}

// Validation error helper
export const createValidationError = (field: string, message: string) => {
  return new APIError(
    "VALIDATION_ERROR",
    400,
    `Validation failed: ${message}`,
    { field, message }
  )
}

// Environment variable validation
export const validateEnvVariables = (vars: string[]): boolean => {
  const missing = vars.filter(v => !process.env[v])
  if (missing.length > 0) {
    logger.error("Missing environment variables", undefined, {
      missing,
    })
    return false
  }
  return true
}
