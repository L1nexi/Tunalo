import { computed, ref, shallowRef } from "vue"
import type { Ref } from "vue"

import { ApiError, detectLocation, validateWeatherKey } from "@/api/profile"
import type { Locale } from "@/api/profile"
import { COPY } from "./copy"
import { describeNetworkFailure, describeWeatherTestError, isSoftWeatherFailure } from "./errorMessages"
import type { ProfileDraft } from "./model"

/** 密钥验证与位置估算共享天气草稿，但独立于表单导航及 Profile 提交。 */
export function useWeatherServices(
  weather: Ref<ProfileDraft["weather"]>,
  locale: Ref<Locale>,
  onEdit: (field: "api_key" | "location") => void,
) {
  const copy = computed(() => COPY[locale.value])
  const validatingWeather = ref(false)
  const weatherFailureKind = ref<null | "invalid" | "quota" | "connection">(null)
  const weatherTestedAt = ref<number | null>(null)
  const weatherValidationError = ref("")
  const weatherValidationFailure = shallowRef<unknown>(null)
  const verifiedWeatherKey = ref<string | null>(null)
  const weatherSaveDialogOpen = ref(false)
  const weatherSaveFailure = ref("")
  const locating = ref(false)
  const locationDetectionStatus = ref<"idle" | "success" | "error">("idle")
  const locationDetectionError = ref("")
  const locationDetectionCity = ref<string | null>(null)
  const hasVerifiedKey = computed(() => verifiedWeatherKey.value === weather.value.api_key.trim())
  const weatherKeyState = computed<"untested" | "valid" | "invalid" | "quota">(() => {
    if (weatherFailureKind.value === "invalid") return "invalid"
    if (weatherFailureKind.value === "quota") return "quota"
    return hasVerifiedKey.value ? "valid" : "untested"
  })
  const weatherConnectionError = computed(() => {
    if (weatherFailureKind.value !== "connection") return ""
    const error = weatherValidationFailure.value
    const reason = error instanceof ApiError && error.payload.error === "weather_validation_unavailable"
      ? describeNetworkFailure(error, locale.value) : ""
    return copy.value.weather.connectionFailed(reason || copy.value.errors.generic)
  })
  const weatherTestedAtText = computed(() => weatherTestedAt.value === null ? "" :
    copy.value.weather.testedAt(new Date(weatherTestedAt.value).toLocaleString(locale.value === "zh" ? "zh-CN" : "en-US")))

  function updateApiKey(value: string): void {
    weather.value.api_key = value
    weatherFailureKind.value = null
    weatherValidationError.value = ""
    weatherValidationFailure.value = null
    if (value.trim() !== verifiedWeatherKey.value) weatherTestedAt.value = null
    onEdit("api_key")
  }

  function updateLocation(value: ProfileDraft["weather"]["location"]): void {
    weather.value.location = value
    locationDetectionStatus.value = "idle"
    locationDetectionError.value = ""
    locationDetectionCity.value = null
    onEdit("location")
  }

  async function testWeatherKey(): Promise<void> {
    const apiKey = weather.value.api_key.trim()
    if (!apiKey) {
      weatherValidationError.value = copy.value.weather.validationMissing
      return
    }
    validatingWeather.value = true
    weatherValidationError.value = ""
    weatherValidationFailure.value = null
    weatherFailureKind.value = null
    try {
      await validateWeatherKey(apiKey)
      if (weather.value.api_key.trim() === apiKey) {
        verifiedWeatherKey.value = apiKey
        weatherTestedAt.value = Date.now()
      }
    } catch (error) {
      if (weather.value.api_key.trim() === apiKey) {
        const issueCodes = error instanceof ApiError ? (error.payload.issues ?? []).map((issue) => issue.code) : []
        if (issueCodes.includes("weather_api_key_invalid")) {
          weatherFailureKind.value = "invalid"
          verifiedWeatherKey.value = null
        } else if (issueCodes.includes("weather_api_quota_exceeded")) {
          weatherFailureKind.value = "quota"
        } else {
          weatherFailureKind.value = "connection"
        }
        weatherValidationFailure.value = error
        if (verifiedWeatherKey.value !== apiKey) weatherTestedAt.value = Date.now()
      }
    } finally {
      validatingWeather.value = false
    }
  }

  async function detectCity(): Promise<void> {
    locating.value = true
    locationDetectionStatus.value = "idle"
    locationDetectionError.value = ""
    locationDetectionCity.value = null
    try {
      const detected = await detectLocation()
      updateLocation({ latitude: detected.latitude, longitude: detected.longitude })
      locationDetectionCity.value = detected.city ?? null
      locationDetectionStatus.value = "success"
    } catch (error) {
      locationDetectionStatus.value = "error"
      const detail = error instanceof ApiError ? describeNetworkFailure(error, locale.value) : ""
      locationDetectionError.value = `${copy.value.errors.locationValidationUnavailable} ${detail}`.trim()
    } finally {
      locating.value = false
    }
  }

  function offerUnverifiedSave(error: unknown = weatherValidationFailure.value): boolean {
    if (!isSoftWeatherFailure(error)) return false
    weatherSaveFailure.value = describeWeatherTestError(error, locale.value)
    weatherSaveDialogOpen.value = true
    return true
  }

  function clearSaveFeedback(): void {
    weatherValidationFailure.value = null
    weatherSaveFailure.value = ""
  }

  return {
    validatingWeather, weatherKeyState, weatherTestedAtText, weatherConnectionError, weatherValidationError,
    locating, locationDetectionStatus, locationDetectionError, locationDetectionCity,
    weatherSaveDialogOpen, weatherSaveFailure, hasVerifiedKey,
    updateApiKey, updateLocation, testWeatherKey, detectCity, offerUnverifiedSave, clearSaveFeedback,
  }
}

export type WeatherServices = ReturnType<typeof useWeatherServices>
