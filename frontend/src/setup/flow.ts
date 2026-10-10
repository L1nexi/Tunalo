import type { PlaylistScanResult } from "@/api/profile"
import { hasValidTiming, sceneFingerprint } from "./model.ts"
import type { ProfileDraft } from "./model.ts"

export const STEP_ORDER = [
  "wallpaper",
  "weather",
  "scenes",
  "scheduling",
  "review",
] as const

export type StepId = (typeof STEP_ORDER)[number]
export type EditableStepId = Exclude<StepId, "review">

// 双栏/多列布局的步骤，主内容区允许比普通表单页（760px）更宽。
export const WIDE_STEPS: ReadonlySet<StepId> = new Set(["scenes"])

export interface StepEvaluation {
  validity: Record<EditableStepId, boolean>
}

export function stepFingerprint(draft: ProfileDraft, id: EditableStepId): string {
  switch (id) {
    case "wallpaper": return JSON.stringify(draft.wallpaper_engine_path)
    case "weather": return JSON.stringify(draft.weather)
    case "scenes": return sceneFingerprint(draft.scenes)
    case "scheduling": return JSON.stringify([draft.matching, draft.disturbance])
  }
}

export function stepForIssue(path: Array<string | number>): StepId {
  const root = path[0]
  if (root === "wallpaper_engine_path") return "wallpaper"
  if (root === "weather") return "weather"
  if (root === "scenes") return "scenes"
  if (root === "matching" || root === "disturbance") return "scheduling"
  return "review"
}

export function evaluateSteps(
  draft: ProfileDraft,
  wallpaperReady: boolean,
  playlists: PlaylistScanResult["playlists"],
): StepEvaluation {
  // 草稿坐标只会是 null 或有限数：输入解析过滤非有限值，后端 JSON 无法携带 NaN/Infinity。
  const location = draft.weather.location
  const locationValid =
    location.latitude !== null &&
    location.latitude >= -90 &&
    location.latitude <= 90 &&
    location.longitude !== null &&
    location.longitude >= -180 &&
    location.longitude <= 180

  const available = new Set(playlists.map((playlist) => playlist.name))
  const assignments = Object.values(draft.scenes)
  const scenesValid =
    assignments.length > 0 && assignments.every((playlist) => Boolean(playlist && available.has(playlist)))

  return {
    validity: {
      wallpaper: wallpaperReady,
      weather: draft.weather.api_key.trim().length > 0 && locationValid,
      scenes: scenesValid,
      scheduling: hasValidTiming(draft.disturbance),
    },
  }
}
