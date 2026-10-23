import { CONTEXT_VARIABLES } from "@/api/profile"
import type { ActivityProfile, ContextVariable, Locale, Profile, SceneProfile } from "@/api/profile"

export interface ProfileDraft {
  version: 3
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
  scenes: Record<string, SceneProfile>
  matching: {
    preference_tiers: ContextVariable[][]
  }
  disturbance: {
    startup_grace_seconds: number | null
    idle_before_switch_seconds: number | null
    cycle_interval_minutes: number | null
  }
  activity: ActivityProfile
}

export interface PreferenceLayer {
  id: number
  variables: ContextVariable[]
}

export function normalizePreferenceTiers(tiers: ContextVariable[][]): ContextVariable[][] {
  return tiers.filter((tier) => tier.length > 0)
    .map((tier) => [...tier].sort((a, b) => CONTEXT_VARIABLES.indexOf(a) - CONTEXT_VARIABLES.indexOf(b)))
}

export function hasValidPreferences(matching: ProfileDraft["matching"]): boolean {
  const variables = matching.preference_tiers.flat()
  return matching.preference_tiers.every((tier) => tier.length > 0)
    && variables.every((variable) => CONTEXT_VARIABLES.includes(variable))
    && new Set(variables).size === variables.length
}

export function preferenceFingerprint(matching: ProfileDraft["matching"]): string {
  return JSON.stringify(normalizePreferenceTiers(matching.preference_tiers))
}

function copyActivity(activity: ActivityProfile | null): ActivityProfile {
  if (activity === null) return { work_processes: [], leisure_processes: [], work_title_keywords: [], leisure_title_keywords: [] }
  return {
    work_processes: [...activity.work_processes],
    leisure_processes: [...activity.leisure_processes],
    work_title_keywords: [...activity.work_title_keywords],
    leisure_title_keywords: [...activity.leisure_title_keywords],
  }
}

export type ActivityField = keyof ProfileDraft["activity"]
export type PendingActivity = Record<ActivityField, string>

export function emptyPendingActivity(): PendingActivity {
  return {
    work_processes: "",
    leisure_processes: "",
    work_title_keywords: "",
    leisure_title_keywords: "",
  }
}

export const DISTURBANCE_PRESETS = {
  eager: {
    startup_grace_seconds: 5,
    idle_before_switch_seconds: 10,
    cycle_interval_minutes: 5,
  },
  responsive: {
    startup_grace_seconds: 15,
    idle_before_switch_seconds: 15,
    cycle_interval_minutes: 10,
  },
  balanced: {
    startup_grace_seconds: 15,
    idle_before_switch_seconds: 20,
    cycle_interval_minutes: 15,
  },
  quiet: {
    startup_grace_seconds: 30,
    idle_before_switch_seconds: 60,
    cycle_interval_minutes: 30,
  },
  minimal: {
    startup_grace_seconds: 60,
    idle_before_switch_seconds: 120,
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
  if (root === "activity" || root === "scenes") return root
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
      version: 3,
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
      scenes: copyScenes(profile.scenes),
      matching: { preference_tiers: normalizePreferenceTiers(profile.matching.preference_tiers) },
      disturbance: { ...profile.disturbance },
      activity: copyActivity(profile.activity),
    }
  }

  return {
    version: 3,
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
    scenes: {},
    matching: {
      preference_tiers: [],
    },
    disturbance: { ...DISTURBANCE_PRESETS.balanced },
    activity: copyActivity(null),
  }
}

export function buildProfile(draft: ProfileDraft): Profile {
  const latitude = draft.weather.location.latitude
  const longitude = draft.weather.location.longitude
  if (latitude === null || longitude === null) {
    throw new Error("location_coordinates_required")
  }
  if (!hasValidPreferences(draft.matching)) throw new Error("invalid_preference_tiers")

  return {
    version: 3,
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
    scenes: copyScenes(draft.scenes),
    matching: { preference_tiers: normalizePreferenceTiers(draft.matching.preference_tiers) },
    disturbance: {
      startup_grace_seconds: requireNonNegativeInteger(draft.disturbance.startup_grace_seconds),
      idle_before_switch_seconds: requireNonNegativeInteger(draft.disturbance.idle_before_switch_seconds),
      cycle_interval_minutes: requireNonNegativeInteger(draft.disturbance.cycle_interval_minutes),
    },
    activity: {
      work_processes: [...draft.activity.work_processes],
      leisure_processes: [...draft.activity.leisure_processes],
      work_title_keywords: [...draft.activity.work_title_keywords],
      leisure_title_keywords: [...draft.activity.leisure_title_keywords],
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

export function normalizeProcess(value: string): string {
  return value.trim().toLocaleLowerCase().replace(/\.exe$/i, "")
}

export function normalizeTitle(value: string): string {
  return value.trim().toLocaleLowerCase()
}

export function activityConflicts(draft: ProfileDraft): string[] {
  const workProcesses = new Set(draft.activity.work_processes.map(normalizeProcess))
  const leisureProcesses = new Set(draft.activity.leisure_processes.map(normalizeProcess))
  const workTitles = new Set(draft.activity.work_title_keywords.map(normalizeTitle))
  const leisureTitles = new Set(draft.activity.leisure_title_keywords.map(normalizeTitle))

  return [
    ...[...workProcesses].filter((value) => leisureProcesses.has(value)),
    ...[...workTitles].filter((value) => leisureTitles.has(value)),
  ].filter(Boolean)
}

export function copyScene(scene: SceneProfile): SceneProfile {
  return {
    ...scene,
    associations: Object.fromEntries(Object.entries(scene.associations).map(([variable, items]) => [variable, [...items]])),
  }
}

export function copyScenes(scenes: ProfileDraft["scenes"]): ProfileDraft["scenes"] {
  return Object.fromEntries(Object.entries(scenes).map(([id, scene]) => [id, copyScene(scene)]))
}

function sortedScenes(scenes: ProfileDraft["scenes"]): ProfileDraft["scenes"] {
  return Object.fromEntries(Object.entries(scenes).sort(([a], [b]) => a.localeCompare(b)).map(([id, scene]) => [id, {
    name: scene.name,
    playlist: scene.playlist,
    associations: Object.fromEntries(CONTEXT_VARIABLES.filter((variable) => scene.associations[variable]?.length)
      .map((variable) => [variable, [...scene.associations[variable]!].sort()])),
  }]))
}

/** 场景映射的规范化指纹，供整体与分步指纹共用同一语义。 */
export function sceneFingerprint(scenes: ProfileDraft["scenes"]): string {
  return JSON.stringify(sortedScenes(scenes))
}

export function profileFingerprint(draft: ProfileDraft): string {
  return JSON.stringify({
    ...draft,
    scenes: sortedScenes(draft.scenes),
    matching: { preference_tiers: normalizePreferenceTiers(draft.matching.preference_tiers) },
  })
}
