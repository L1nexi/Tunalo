import type { ContextVariable, SceneAssociations, SemanticItem } from "@/api/profile"

export type ScenePresetGroup = ContextVariable | "time_activity"

export type ScenePresetId =
  | SemanticItem
  | `${"day" | "night"}_${"work" | "leisure"}`

export interface ScenePreset {
  id: ScenePresetId
  associations: SceneAssociations
}

export const PRESET_GROUPS = ["season", "time", "activity", "weather", "time_activity"] as const

export const SCENE_PRESETS: Record<ScenePresetGroup, ScenePreset[]> = {
  season: [
    { id: "spring", associations: { season: ["spring"] } },
    { id: "summer", associations: { season: ["summer"] } },
    { id: "autumn", associations: { season: ["autumn"] } },
    { id: "winter", associations: { season: ["winter"] } },
  ],
  time: [
    { id: "dawn", associations: { time: ["dawn"] } },
    { id: "day", associations: { time: ["day"] } },
    { id: "sunset", associations: { time: ["sunset"] } },
    { id: "night", associations: { time: ["night"] } },
  ],
  activity: [
    { id: "work", associations: { activity: ["work"] } },
    { id: "leisure", associations: { activity: ["leisure"] } },
  ],
  weather: [
    { id: "clear", associations: { weather: ["clear"] } },
    { id: "cloudy", associations: { weather: ["cloudy"] } },
    { id: "rain", associations: { weather: ["rain"] } },
    { id: "snow", associations: { weather: ["snow"] } },
  ],
  time_activity: [
    { id: "day_work", associations: { time: ["day"], activity: ["work"] } },
    { id: "day_leisure", associations: { time: ["day"], activity: ["leisure"] } },
    { id: "night_work", associations: { time: ["night"], activity: ["work"] } },
    { id: "night_leisure", associations: { time: ["night"], activity: ["leisure"] } },
  ],
}
