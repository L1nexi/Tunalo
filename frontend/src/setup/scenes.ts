import type { ContextVariable, SceneAssociations, SemanticItem } from "@/api/profile"

export type SceneEditorState = { kind: "presets" } | { kind: "create" } | { kind: "edit"; id: string }

export const SCENE_VARIABLES: ContextVariable[] = ["time", "activity", "season", "weather"]

export const SCENE_ITEMS: Record<ContextVariable, SemanticItem[]> = {
  time: ["dawn", "day", "sunset", "night"],
  activity: ["work", "leisure"],
  season: ["spring", "summer", "autumn", "winter"],
  weather: ["clear", "cloudy", "rain", "snow"],
}

export function associationKey(associations: SceneAssociations): string {
  return SCENE_VARIABLES.map((variable) => [...(associations[variable] ?? [])].sort().join(",")).join("|")
}
