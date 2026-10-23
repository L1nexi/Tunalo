import type { ActivityProfile, ContextVariable, Locale, Profile, SceneProfile } from "@/api/profile"
import { copyActivity } from "./activity"
import { hasValidPreferences, normalizePreferenceTiers } from "./preferences"
import { copyScenes, sortedScenes } from "./scenes"
import { DISTURBANCE_PRESETS, requireNonNegativeInteger } from "./timing"

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

export function profileFingerprint(draft: ProfileDraft): string {
  return JSON.stringify({
    ...draft,
    scenes: sortedScenes(draft.scenes),
    matching: { preference_tiers: normalizePreferenceTiers(draft.matching.preference_tiers) },
  })
}
