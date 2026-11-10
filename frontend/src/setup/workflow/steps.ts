import type { PlaylistScanResult } from "@/api/profile"
import { activityConflicts, hasValidLocation, hasValidPreferences, hasValidTiming, playlistBindingStatus, preferenceFingerprint, sceneFingerprint } from "@/setup/profile/model"
import type { ProfileDraft } from "@/setup/profile/model"

export const STEP_ORDER = [
  "wallpaper",
  "weather",
  "scenes",
  "scheduling",
  "activity",
  "review",
] as const

export type StepId = (typeof STEP_ORDER)[number]
export type EditableStepId = Exclude<StepId, "review">

// 双栏/多列布局的步骤，主内容区允许比普通表单页（760px）更宽。
export const WIDE_STEPS: ReadonlySet<StepId> = new Set(["scenes", "activity"])

export interface StepEvaluation {
  validity: Record<EditableStepId, boolean>
  conflicts: string[]
}

export function stepFingerprint(draft: ProfileDraft, id: EditableStepId): string {
  switch (id) {
    case "wallpaper": return JSON.stringify(draft.wallpaper_engine_path)
    case "weather": return JSON.stringify(draft.weather)
    case "scenes": return sceneFingerprint(draft.scenes)
    case "scheduling": return JSON.stringify([preferenceFingerprint(draft.matching), draft.disturbance])
    case "activity": return JSON.stringify(draft.activity)
  }
}

export function stepForIssue(path: Array<string | number>): StepId {
  const root = path[0]
  if (root === "wallpaper_engine_path") return "wallpaper"
  if (root === "weather") return "weather"
  if (root === "scenes") return "scenes"
  if (root === "matching" || root === "disturbance") return "scheduling"
  if (root === "activity") return "activity"
  return "review"
}

export function evaluateSteps(
  draft: ProfileDraft,
  wallpaperReady: boolean,
  playlists: PlaylistScanResult["playlists"],
): StepEvaluation {
  const available = new Set(playlists.map((playlist) => playlist.name))
  const assignments = Object.values(draft.scenes)
  const scenesValid =
    assignments.length > 0 && assignments.every((scene) => scene.name.trim().length > 0 && Object.values(scene.associations).some((items) => items.length > 0) && playlistBindingStatus(scene.playlist, available) === "bound")
  const conflicts = activityConflicts(draft)

  return {
    validity: {
      wallpaper: wallpaperReady,
      weather: hasValidLocation(draft.weather.location),
      scenes: scenesValid,
      scheduling: hasValidTiming(draft.disturbance) && hasValidPreferences(draft.matching),
      activity: conflicts.length === 0,
    },
    conflicts,
  }
}
