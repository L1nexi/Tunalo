import { computed, ref, shallowRef } from "vue"
import type { Ref } from "vue"

import { ApiError, detectLocation, validateWeatherConnection } from "@/api/profile"
import type { Locale } from "@/api/profile"
import { COPY } from "@/setup/copy"
import { describeNetworkFailure, describeWeatherTestError, isSoftWeatherFailure } from "@/setup/errorMessages"
import type { ProfileDraft } from "@/setup/profile/model"
import { hasValidLocation } from "@/setup/profile/model"

/** 天气连接测试与位置估算共享天气草稿，验证结果只用于被测试的坐标。 */
export function useWeatherServices(
  weather: Ref<ProfileDraft["weather"]>,
  locale: Ref<Locale>,
  onEdit: (field: "location") => void,
) {
  const copy = computed(() => COPY[locale.value])
  const validatingWeather = ref(false)
  const weatherFailureKind = ref<null | "invalid" | "quota" | "connection">(null)
  const weatherTestedAt = ref<number | null>(null)
  const weatherValidationError = ref("")
  const weatherValidationFailure = shallowRef<unknown>(null)
  const verifiedLocation = ref<string | null>(null)
  const weatherSaveDialogOpen = ref(false)
  const weatherSaveFailure = ref("")
  const locating = ref(false)
  const locationDetectionStatus = ref<"idle" | "success" | "error">("idle")
  const locationDetectionError = ref("")
  const locationDetectionCity = ref<string | null>(null)
  const locationFingerprint = computed(() => JSON.stringify([weather.value.location.latitude, weather.value.location.longitude]))
  const canTestWeather = computed(() => hasValidLocation(weather.value.location))
  const hasVerifiedLocation = computed(() => verifiedLocation.value === locationFingerprint.value)
  const weatherConnectionState = computed<"untested" | "valid" | "invalid" | "quota">(() => {
    if (weatherFailureKind.value === "invalid") return "invalid"
    if (weatherFailureKind.value === "quota") return "quota"
    return hasVerifiedLocation.value ? "valid" : "untested"
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

  function updateLocation(value: ProfileDraft["weather"]["location"]): void {
    if (value.latitude !== weather.value.location.latitude || value.longitude !== weather.value.location.longitude) {
      verifiedLocation.value = null
      weatherTestedAt.value = null
      weatherFailureKind.value = null
      weatherValidationFailure.value = null
      weatherValidationError.value = ""
    }
    weather.value.location = value
    locationDetectionStatus.value = "idle"
    locationDetectionError.value = ""
    locationDetectionCity.value = null
    onEdit("location")
  }

  async function testWeatherConnection(): Promise<void> {
    if (validatingWeather.value) return
    const location = { ...weather.value.location }
    if (!hasValidLocation(location)) {
      weatherValidationError.value = copy.value.weather.validationMissing
      return
    }
    const testedLocation = locationFingerprint.value
    validatingWeather.value = true
    weatherValidationError.value = ""
    weatherValidationFailure.value = null
    weatherFailureKind.value = null
    try {
      await validateWeatherConnection(location)
      if (locationFingerprint.value === testedLocation) {
        verifiedLocation.value = testedLocation
        weatherTestedAt.value = Date.now()
      }
    } catch (error) {
      if (locationFingerprint.value === testedLocation) {
        const issueCodes = error instanceof ApiError ? (error.payload.issues ?? []).map((issue) => issue.code) : []
        if (issueCodes.includes("weather_location_invalid")) {
          weatherFailureKind.value = "invalid"
          verifiedLocation.value = null
        } else if (issueCodes.includes("weather_api_quota_exceeded")) {
          weatherFailureKind.value = "quota"
        } else {
          weatherFailureKind.value = "connection"
        }
        weatherValidationFailure.value = error
        if (verifiedLocation.value !== testedLocation) weatherTestedAt.value = Date.now()
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
    // 保存成功只清提交侧反馈；失败分类与失败详情是一体状态，原样保留，
    // 状态区继续准确显示上次测试结果（含真实原因），不与本次保存结果混淆。
    weatherSaveFailure.value = ""
  }

  return {
    validatingWeather, canTestWeather, weatherConnectionState, weatherTestedAtText, weatherConnectionError, weatherValidationError,
    locating, locationDetectionStatus, locationDetectionError, locationDetectionCity,
    weatherSaveDialogOpen, weatherSaveFailure, hasVerifiedLocation,
    updateLocation, testWeatherConnection, detectCity, offerUnverifiedSave, clearSaveFeedback,
  }
}

export type WeatherServices = ReturnType<typeof useWeatherServices>
