import type { Locale } from "@/api/profile"
import { COPY, DISTURBANCE_LABELS, preferenceSummary } from "../copy"
import { detectDisturbancePreset } from "@/setup/profile/model"
import type { ProfileDraft } from "@/setup/profile/model"

export type ReviewWeatherState = "untested" | "valid" | "invalid" | "quota"

export function reviewLocation(draft: ProfileDraft, locale: Locale): string {
  const copy = COPY[locale]
  const { latitude, longitude } = draft.weather.location
  return latitude === null || longitude === null
    ? copy.common.notSet
    : copy.review.coordinates(latitude, longitude)
}

export function reviewWeather(state: ReviewWeatherState, locale: Locale): string {
  const copy = COPY[locale]
  switch (state) {
    case "valid":
      return copy.weather.keyValid
    case "invalid":
      return copy.errors.issueCodes.weather_api_key_invalid
    case "quota":
      return copy.errors.issueCodes.weather_api_quota_exceeded
    case "untested":
      return copy.review.weatherUntested
  }
}

/** 以设置步骤组织当前配置摘要，保留路径与主要选择的强调级别。 */
export function reviewGroups(draft: ProfileDraft, locale: Locale, weatherState: ReviewWeatherState) {
  const copy = COPY[locale]
  const preset = detectDisturbancePreset(draft)
  const scenes = Object.values(draft.scenes)
  return [
    {
      id: "wallpaper" as const,
      deEmphasized: true,
      rows: [
        {
          id: "wallpaper",
          label: copy.review.wallpaper,
          value: draft.wallpaper_engine_path || copy.common.notSet,
        },
      ],
    },
    {
      id: "weather" as const,
      rows: [
        { id: "weather", label: copy.review.weather, value: reviewWeather(weatherState, locale) },
        { id: "location", label: copy.review.location, value: reviewLocation(draft, locale) },
      ],
    },
    {
      id: "scenes" as const,
      rows: [
        {
          id: "scenes",
          label: copy.review.scenes,
          value: copy.review.sceneCount(
            scenes.filter((scene) => scene.playlist).length,
            scenes.filter((scene) => !scene.playlist).length,
          ),
        },
      ],
    },
    {
      id: "scheduling" as const,
      rows: [
        {
          id: "response",
          label: copy.review.response,
          value: preferenceSummary(draft.matching.preference_tiers, locale),
        },
        {
          id: "disturbance",
          label: copy.review.disturbance,
          value: preset === "custom" ? copy.common.custom : DISTURBANCE_LABELS[locale][preset],
        },
      ],
    },
    {
      id: "activity" as const,
      rows: [
        {
          id: "activity",
          label: copy.review.activity,
          value: copy.review.activityCount(
            draft.activity.work_title_keywords.length + draft.activity.leisure_title_keywords.length,
            draft.activity.work_processes.length + draft.activity.leisure_processes.length,
          ),
        },
      ],
    },
  ]
}
