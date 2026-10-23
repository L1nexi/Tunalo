import { computed, reactive, ref, watch } from "vue"

import type { Locale, Profile, SceneProfile } from "@/api/profile"
import { STEP_ORDER, stepFingerprint } from "@/setup/workflow/steps"
import type { EditableStepId } from "@/setup/workflow/steps"
import {
  createProfileDraft,
  emptyPendingActivity,
  normalizePreferenceTiers,
  profileFingerprint,
} from "./model"
import type { ActivityField, PreferenceLayer, ProfileDraft } from "./model"

export type SetupMode = "setup" | "settings"

/** 设置窗口内的编辑会话；已保存基线只在提交成功或初始路径回填后变化。 */
export function useProfileDraft(initialProfile: Profile | null, initialLocale: Locale) {
  const mode: SetupMode = initialProfile === null ? "setup" : "settings"
  const locale = ref<Locale>(initialProfile?.language ?? initialLocale)
  const draft = reactive<ProfileDraft>(createProfileDraft(initialProfile, locale.value))
  const savedDraft = ref<ProfileDraft>(createProfileDraft(initialProfile, locale.value))
  const baseline = ref(profileFingerprint(savedDraft.value))
  const pendingActivity = reactive(emptyPendingActivity())
  const submitting = ref(false)
  const preferenceLayers = ref<PreferenceLayer[]>([])
  let nextLayerId = 0
  let pathTouched = false

  function resetPreferenceLayers(): void {
    preferenceLayers.value = draft.matching.preference_tiers.map((variables) => ({
      id: nextLayerId++,
      variables: [...variables],
    }))
  }
  resetPreferenceLayers()

  function updatePreferenceLayers(layers: PreferenceLayer[]): void {
    preferenceLayers.value = layers
    draft.matching = { preference_tiers: normalizePreferenceTiers(layers.map((layer) => layer.variables)) }
  }

  function addPreferenceLayer(): void {
    updatePreferenceLayers([...preferenceLayers.value, { id: nextLayerId++, variables: [] }])
  }

  function updateScenes(scenes: Record<string, SceneProfile>): void {
    draft.scenes = scenes
  }

  function removeScene(id: string): { name: string; restore: () => void } {
    const scene = draft.scenes[id]!
    const remaining = { ...draft.scenes }
    delete remaining[id]
    updateScenes(remaining)
    return {
      name: scene.name,
      restore: () => updateScenes({ ...draft.scenes, [id]: scene }),
    }
  }

  const pendingActivityFields = computed(() =>
    (Object.keys(pendingActivity) as ActivityField[]).filter(
      (field) => pendingActivity[field].trim().length > 0,
    ),
  )
  const changedSteps = computed(
    () =>
      new Set(
        STEP_ORDER.filter((id): id is EditableStepId => id !== "review").filter(
          (id) =>
            stepFingerprint(draft, id) !== stepFingerprint(savedDraft.value, id) ||
            (id === "activity" && pendingActivityFields.value.length > 0),
        ),
      ),
  )
  const isDirty = computed(
    () => profileFingerprint(draft) !== baseline.value || pendingActivityFields.value.length > 0,
  )

  watch(
    locale,
    (value, previous) => {
      if (previous !== undefined) draft.language = value
      document.documentElement.lang = value === "zh" ? "zh-CN" : "en"
      document.title = value === "zh" ? "Tunalo 设置" : "Tunalo Settings"
    },
    { immediate: true },
  )

  function setLocale(value: unknown): void {
    if (value === "zh" || value === "en") locale.value = value
  }

  function updatePath(value: string): void {
    pathTouched = true
    draft.wallpaper_engine_path = value
  }

  function acceptDetectedPath(): void {
    if (pathTouched) return
    // 只合并探测路径，保留扫描期间其他用户编辑的脏标记。
    baseline.value = profileFingerprint({
      ...savedDraft.value,
      wallpaper_engine_path: draft.wallpaper_engine_path,
    })
  }

  function commit(profile: Profile): void {
    Object.assign(draft, createProfileDraft(profile, locale.value))
    savedDraft.value = createProfileDraft(profile, locale.value)
    baseline.value = profileFingerprint(draft)
    resetPreferenceLayers()
  }

  return {
    mode,
    locale,
    draft,
    savedDraft,
    pendingActivity,
    pendingActivityFields,
    preferenceLayers,
    changedSteps,
    isDirty,
    submitting,
    updatePreferenceLayers,
    addPreferenceLayer,
    setLocale,
    updatePath,
    updateScenes,
    removeScene,
    acceptDetectedPath,
    commit,
  }
}

export type ProfileEditor = ReturnType<typeof useProfileDraft>
