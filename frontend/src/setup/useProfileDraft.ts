import { computed, reactive, ref, watch } from "vue"

import type { Locale, Profile } from "@/api/profile"
import { STEP_ORDER, stepFingerprint } from "./flow"
import type { EditableStepId } from "./flow"
import { createProfileDraft, emptyPendingActivity, profileFingerprint } from "./model"
import type { ActivityField, ProfileDraft } from "./model"

export type SetupMode = "setup" | "settings"

/** 设置窗口内的编辑会话；已保存基线只在提交成功或初始路径回填后变化。 */
export function useProfileDraft(initialProfile: Profile | null, initialLocale: Locale) {
  const mode: SetupMode = initialProfile === null ? "setup" : "settings"
  const locale = ref<Locale>(initialProfile?.language ?? initialLocale)
  const draft = reactive<ProfileDraft>(createProfileDraft(initialProfile, locale.value))
  const savedDraft = ref<ProfileDraft>(createProfileDraft(initialProfile, locale.value))
  const baseline = ref(profileFingerprint(savedDraft.value))
  const pendingActivity = reactive(emptyPendingActivity())
  const rememberedScenes = reactive<ProfileDraft["scenes"]>({})
  let pathTouched = false

  const pendingActivityFields = computed(() => (Object.keys(pendingActivity) as ActivityField[])
    .filter((field) => pendingActivity[field].trim().length > 0))
  const changedSteps = computed(() => new Set(STEP_ORDER.filter((id): id is EditableStepId => id !== "review")
    .filter((id) => stepFingerprint(draft, id) !== stepFingerprint(savedDraft.value, id)
      || (id === "activity" && pendingActivityFields.value.length > 0))))
  const isDirty = computed(() => profileFingerprint(draft) !== baseline.value || pendingActivityFields.value.length > 0)

  watch(locale, (value, previous) => {
    if (previous !== undefined) draft.language = value
    document.documentElement.lang = value === "zh" ? "zh-CN" : "en"
    document.title = value === "zh" ? "Tunalo 设置" : "Tunalo Settings"
  }, { immediate: true })

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

  function rememberScene(id: keyof ProfileDraft["scenes"], playlist: string): void {
    rememberedScenes[id] = playlist
  }

  function commit(profile: Profile): void {
    Object.assign(draft, createProfileDraft(profile, locale.value))
    savedDraft.value = createProfileDraft(profile, locale.value)
    baseline.value = profileFingerprint(draft)
    for (const id of Object.keys(rememberedScenes) as Array<keyof ProfileDraft["scenes"]>) delete rememberedScenes[id]
  }

  return {
    mode, locale, draft, savedDraft, pendingActivity, pendingActivityFields,
    rememberedScenes, changedSteps, isDirty,
    setLocale, updatePath, acceptDetectedPath, rememberScene, commit,
  }
}

export type ProfileEditor = ReturnType<typeof useProfileDraft>
