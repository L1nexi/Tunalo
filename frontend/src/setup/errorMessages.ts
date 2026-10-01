import { ApiError } from "@/api/profile"
import type { Locale } from "@/api/profile"
import { COPY } from "./copy"

export function describeNetworkFailure(error: ApiError, locale: Locale): string {
  const copy = COPY[locale]
  const { reason, http_status: status } = error.payload
  if (reason === "http_status" && status !== undefined) {
    if (status === 429) return copy.errors.httpRateLimited
    if (status === 403) return copy.errors.httpForbidden
    if (status >= 500) return copy.errors.httpServerError
    return copy.errors.httpOther(status)
  }
  const messages = copy.errors.networkReasons as Record<string, string>
  return reason ? (messages[reason] ?? "") : ""
}

export function describeError(error: unknown, locale: Locale): string {
  const copy = COPY[locale]
  if (!(error instanceof ApiError)) return copy.errors.generic
  if (error.payload.error === "profile_already_exists") return copy.errors.profileAlreadyExists
  if (error.payload.error === "profile_apply_timeout") return copy.errors.applyTimeout
  if (error.payload.error === "profile_apply_unavailable") return copy.errors.applyUnavailable
  if (error.payload.error === "weather_validation_unavailable") {
    return `${copy.errors.weatherValidationUnavailable} ${describeNetworkFailure(error, locale)}`.trim()
  }
  if (error.payload.stage) {
    const stage = copy.errors.stages[error.payload.stage]
    return `${stage}: ${error.payload.detail || error.payload.error}`
  }
  return error.message || copy.errors.generic
}

export function describeScanError(error: unknown, locale: Locale): string {
  const copy = COPY[locale]
  if (!(error instanceof ApiError)) return copy.errors.generic
  const messages = copy.errors.scanCodes as Record<string, string>
  return messages[error.payload.error] ?? error.message
}

export function describeWeatherTestError(error: unknown, locale: Locale): string {
  const copy = COPY[locale]
  if (!(error instanceof ApiError)) return copy.errors.generic
  const issue = error.payload.issues?.[0]
  if (issue) {
    const messages = copy.errors.issueCodes as Record<string, string>
    return messages[issue.code] ?? copy.errors.generic
  }
  return error.payload.error === "weather_validation_unavailable"
    ? describeError(error, locale)
    : copy.errors.generic
}

export function isSoftWeatherFailure(error: unknown): boolean {
  return error instanceof ApiError && (
    error.payload.error === "weather_validation_unavailable"
    || error.payload.issues?.some((issue) => issue.code === "weather_api_quota_exceeded") === true
  )
}
