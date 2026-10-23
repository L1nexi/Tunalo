import type { ActivityField, PreferenceLayer, ProfileDraft } from "@/setup/profile/model"
import type { usePlaylistScan } from "@/setup/wallpaper/usePlaylistScan"
import type { ProfileEditor } from "@/setup/profile/useProfileDraft"
import { useSceneRemovalNotice } from "@/setup/scenes/useSceneRemovalNotice"
import { useSetupFeedback } from "./useSetupFeedback"
import { useStepNavigation } from "./useStepNavigation"

/** 编辑操作负责清理对应反馈；步骤导航和提交校验共享同一份编辑会话。 */
export function useSetupFlow(editor: ProfileEditor, scan: ReturnType<typeof usePlaylistScan>) {
  const navigation = useStepNavigation(editor, scan)
  const feedback = useSetupFeedback(editor, navigation)
  const { draft, pendingActivity, pendingActivityFields } = editor
  const { stepError, clearStepFeedback } = feedback
  const removeScene = useSceneRemovalNotice(editor, () => clearStepFeedback("scenes"))

  function updatePath(value: string): void {
    editor.updatePath(value)
    clearStepFeedback("wallpaper")
  }

  function updateScenes(value: ProfileDraft["scenes"]): void {
    editor.updateScenes(value)
    clearStepFeedback("scenes")
  }

  function updatePreferenceLayers(value: PreferenceLayer[]): void {
    editor.updatePreferenceLayers(value)
    clearStepFeedback("scheduling")
  }

  function addPreferenceLayer(): void {
    editor.addPreferenceLayer()
    clearStepFeedback("scheduling")
  }

  function updateDisturbance(value: ProfileDraft["disturbance"]): void {
    draft.disturbance = value
    clearStepFeedback("scheduling")
  }

  function updateActivity(value: ProfileDraft["activity"]): void {
    draft.activity = value
    const keepPendingWarning = stepError.value === "pendingActivity" && pendingActivityFields.value.length > 0
    clearStepFeedback("activity")
    if (keepPendingWarning) stepError.value = "pendingActivity"
  }

  function updatePendingActivity(field: ActivityField, value: string): void {
    pendingActivity[field] = value
    if (stepError.value === "pendingActivity" && pendingActivityFields.value.length === 0)
      stepError.value = null
  }

  return {
    ...navigation,
    ...feedback,
    updatePath,
    updateScenes,
    removeScene,
    updatePreferenceLayers,
    addPreferenceLayer,
    updateDisturbance,
    updateActivity,
    updatePendingActivity,
  }
}

export type SetupFlow = ReturnType<typeof useSetupFlow>
export type SetupNavigationItem = SetupFlow["steps"]["value"][number]
