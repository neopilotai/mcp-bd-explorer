type LogLevel = "debug" | "info" | "warn" | "error"

interface LogContext {
  timestamp: string
  level: LogLevel
  prefix: string
  message: string
  data?: Record<string, unknown>
}

// Format log message with consistent prefix
const formatLog = (level: LogLevel, message: string, data?: Record<string, unknown>): LogContext => {
  return {
    timestamp: new Date().toISOString(),
    level,
    prefix: "[v0]",
    message,
    data,
  }
}

// Main logger interface
export const logger = {
  debug: (message: string, data?: Record<string, unknown>) => {
    const log = formatLog("debug", message, data)
    console.debug(`${log.prefix} [${log.level.toUpperCase()}]`, message, data)
  },

  info: (message: string, data?: Record<string, unknown>) => {
    const log = formatLog("info", message, data)
    console.info(`${log.prefix} [${log.level.toUpperCase()}]`, message, data)
  },

  warn: (message: string, data?: Record<string, unknown>) => {
    const log = formatLog("warn", message, data)
    console.warn(`${log.prefix} [${log.level.toUpperCase()}]`, message, data)
  },

  error: (message: string, error?: unknown, data?: Record<string, unknown>) => {
    const log = formatLog("error", message, data)
    const errorMessage = error instanceof Error ? error.message : String(error)
    console.error(`${log.prefix} [${log.level.toUpperCase()}]`, message, {
      error: errorMessage,
      stack: error instanceof Error ? error.stack : undefined,
      ...data,
    })
  },

  // API-specific logging with request/response tracking
  apiCall: (method: string, endpoint: string, status?: number, duration?: number) => {
    const log = formatLog("info", `API ${method} ${endpoint}`, {
      method,
      endpoint,
      status,
      duration: duration ? `${duration}ms` : undefined,
    })
    console.info(`${log.prefix} [API]`, `${method} ${endpoint}`, { status, duration })
  },

  // Error with full context for debugging
  apiError: (endpoint: string, error: unknown, statusCode?: number) => {
    const errorMessage = error instanceof Error ? error.message : String(error)
    console.error(`${prefix} [API_ERROR]`, `Failed: ${endpoint}`, {
      error: errorMessage,
      statusCode,
      stack: error instanceof Error ? error.stack : undefined,
    })
  },
}

const prefix = "[v0]"
