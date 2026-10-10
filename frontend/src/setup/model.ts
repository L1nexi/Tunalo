import type { Locale, Profile, ContextVariable, SceneId } from "@/api/profile"

export interface ProfileDraft {
  version: 2
  setup_complete: true
  wallpaper_engine_path: string
  language: Locale | null
  weather: {
    api_key: string
    location: {
      latitude: number | null
      longitude: number | null
    }
  }
  scenes: Partial<Record<SceneId, string>>
  matching: {
    preference_tiers: ContextVariable[][]
  }
  disturbance: {
    startup_grace_seconds: number | null
    idle_before_switch_seconds: number | null
    maximum_deferral_minutes: number | null
    cycle_interval_minutes: number | null
  }
}

export const DISTURBANCE_PRESETS = {
  eager: {
    startup_grace_seconds: 5,
    idle_before_switch_seconds: 10,
    maximum_deferral_minutes: 30,
    cycle_interval_minutes: 5,
  },
  responsive: {
    startup_grace_seconds: 15,
    idle_before_switch_seconds: 15,
    maximum_deferral_minutes: 45,
    cycle_interval_minutes: 10,
  },
  balanced: {
    startup_grace_seconds: 15,
    idle_before_switch_seconds: 20,
    maximum_deferral_minutes: 60,
    cycle_interval_minutes: 15,
  },
  quiet: {
    startup_grace_seconds: 30,
    idle_before_switch_seconds: 60,
    maximum_deferral_minutes: 180,
    cycle_interval_minutes: 30,
  },
  minimal: {
    startup_grace_seconds: 60,
    idle_before_switch_seconds: 120,
    maximum_deferral_minutes: 300,
    cycle_interval_minutes: 60,
  },
} as const

export type DisturbancePreset = keyof typeof DISTURBANCE_PRESETS

export function parseNumberInput(value: string | number): number | null {
  if (value === "") return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

/** 防打扰计时值全部为不小于 0 的整数；保存可用性与错误跳转的折叠区展开共用同一规则。 */
export function hasValidTiming(disturbance: ProfileDraft["disturbance"]): boolean {
  return Object.values(disturbance).every(isNonNegativeInteger)
}

export function isNonNegativeInteger(value: number | null): value is number {
  return value !== null && Number.isInteger(value) && value >= 0
}

export function validationIssueField(path: Array<string | number>): string {
  const root = typeof path[0] === "string" ? path[0] : "profile"
  if (root === "scenes") return root
  if (root === "weather" && path[1] === "location") {
    return typeof path[2] === "string" ? `weather.location.${path[2]}` : "weather.location"
  }
  if (["weather", "disturbance", "matching"].includes(root) && typeof path[1] === "string") {
    return `${root}.${path[1]}`
  }
  return root
}

function requireNonNegativeInteger(value: number | null): number {
  if (!isNonNegativeInteger(value)) throw new Error("non_negative_integer_required")
  return value
}

export function createProfileDraft(profile: Profile | null, locale: Locale): ProfileDraft {
  if (profile !== null) {
    return {
      version: 2,
      setup_complete: true,
      wallpaper_engine_path: profile.wallpaper_engine_path,
      language: profile.language,
      weather: {
        api_key: profile.weather.api_key,
        location: {
          latitude: profile.weather.location.latitude,
          longitude: profile.weather.location.longitude,
        },
      },
      scenes: { ...profile.scenes },
      matching: { preference_tiers: profile.matching.preference_tiers.map((tier) => [...tier]) },
      disturbance: { ...profile.disturbance },
    }
  }
  return {
    version: 2,
    setup_complete: true,
    wallpaper_engine_path: "",
    language: locale,
    weather: {
      api_key: "",
      location: {
        latitude: null,
        longitude: null,
      },
    },
    scenes: {
      day_work: "",
      day_leisure: "",
      night_work: "",
      night_leisure: "",
      rain: "",
    },
    matching: {
      preference_tiers: [],
    },
    disturbance: { ...DISTURBANCE_PRESETS.balanced },
  }
}

export function buildProfile(draft: ProfileDraft): Profile {
  const latitude = draft.weather.location.latitude
  const longitude = draft.weather.location.longitude
  if (latitude === null || longitude === null) {
    throw new Error("location_coordinates_required")
  }

  return {
    version: 2,
    setup_complete: true,
    wallpaper_engine_path: draft.wallpaper_engine_path,
    language: draft.language,
    weather: {
      api_key: draft.weather.api_key,
      location: {
        latitude,
        longitude,
      },
    },
    scenes: { ...draft.scenes },
    matching: { preference_tiers: draft.matching.preference_tiers.map((tier) => [...tier]) },
    disturbance: {
      startup_grace_seconds: requireNonNegativeInteger(draft.disturbance.startup_grace_seconds),
      idle_before_switch_seconds: requireNonNegativeInteger(draft.disturbance.idle_before_switch_seconds),
      maximum_deferral_minutes: requireNonNegativeInteger(draft.disturbance.maximum_deferral_minutes),
      cycle_interval_minutes: requireNonNegativeInteger(draft.disturbance.cycle_interval_minutes),
    },
  }

}

export function detectDisturbancePreset(draft: Pick<ProfileDraft, "disturbance">): DisturbancePreset | "custom" {
  const match = Object.entries(DISTURBANCE_PRESETS).find(([, values]) =>
    Object.entries(values).every(
      ([key, value]) => draft.disturbance[key as keyof ProfileDraft["disturbance"]] === value,
    ),
  )
  return (match?.[0] as DisturbancePreset | undefined) ?? "custom"
}

// 场景是封闭集合：序列化前按场景 ID 排序，映射键序不参与变化判定，
// 取消再恢复原绑定不会因对象键序被误判为未保存修改。
function sortedScenes(scenes: ProfileDraft["scenes"]): ProfileDraft["scenes"] {
  return Object.fromEntries(
    (Object.keys(scenes) as Array<keyof ProfileDraft["scenes"]>)
      .sort()
      .map((id) => [id, scenes[id]]),
  )
}

/** 场景映射的规范化指纹，供整体与分步指纹共用同一语义。 */
export function sceneFingerprint(scenes: ProfileDraft["scenes"]): string {
  return JSON.stringify(sortedScenes(scenes))
}

export function profileFingerprint(draft: ProfileDraft): string {
  return JSON.stringify({ ...draft, scenes: sortedScenes(draft.scenes) })
}
