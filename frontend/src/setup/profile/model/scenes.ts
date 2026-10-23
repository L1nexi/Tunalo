import { CONTEXT_VARIABLES, type SceneProfile } from "@/api/profile"
import type { ProfileDraft } from "./draft"

export function copyScene(scene: SceneProfile): SceneProfile {
  return {
    ...scene,
    associations: Object.fromEntries(
      Object.entries(scene.associations).map(([variable, items]) => [variable, [...items]]),
    ),
  }
}

export function copyScenes(scenes: ProfileDraft["scenes"]): ProfileDraft["scenes"] {
  return Object.fromEntries(Object.entries(scenes).map(([id, scene]) => [id, copyScene(scene)]))
}

export function sortedScenes(scenes: ProfileDraft["scenes"]): ProfileDraft["scenes"] {
  return Object.fromEntries(
    Object.entries(scenes)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([id, scene]) => [
        id,
        {
          name: scene.name,
          playlist: scene.playlist,
          associations: Object.fromEntries(
            CONTEXT_VARIABLES.filter((variable) => scene.associations[variable]?.length).map((variable) => [
              variable,
              [...scene.associations[variable]!].sort(),
            ]),
          ),
        },
      ]),
  )
}

/** 场景映射的规范化指纹，供整体与分步指纹共用同一语义。 */
export function sceneFingerprint(scenes: ProfileDraft["scenes"]): string {
  return JSON.stringify(sortedScenes(scenes))
}
