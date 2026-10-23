import type { ContextVariable, SceneAssociations, SemanticItem } from "@/api/profile"

export type ScenePresetGroup = ContextVariable | "time_activity" | "season_weather"

export type ScenePresetId =
  | SemanticItem
  | `${"day" | "night"}_${"work" | "leisure"}`
  | "winter_clear"
  | "winter_precipitation"
  | "summer_clear"
  | "summer_rain"

export interface ScenePreset {
  id: ScenePresetId
  associations: SceneAssociations
}

export const PRESET_SECTIONS = [
  { id: "single", groups: ["season", "time", "activity", "weather"] },
  { id: "double", groups: ["time_activity", "season_weather"] },
] as const

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
  season_weather: [
    { id: "winter_clear", associations: { season: ["winter"], weather: ["clear"] } },
    { id: "winter_precipitation", associations: { season: ["winter"], weather: ["rain", "snow"] } },
    { id: "summer_clear", associations: { season: ["summer"], weather: ["clear"] } },
    { id: "summer_rain", associations: { season: ["summer"], weather: ["rain"] } },
  ],
}
