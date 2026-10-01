import { computed, ref } from "vue"
import { toast } from "vue-sonner"

import { applyProfile, createInitialProfile } from "@/api/profile"
import { COPY } from "./copy"
import { buildProfile } from "./model"
import type { ProfileEditor } from "./useProfileDraft"
import type { SetupFlow } from "./useSetupFlow"
import type { WeatherServices } from "./useWeatherServices"

/** 提交成功后才接受服务端返回的基线；只有首次设置在成功后关闭窗口。 */
export function useProfileSubmission(
  editor: ProfileEditor,
  flow: SetupFlow,
  weather: WeatherServices,
  closeWindow: () => Promise<void>,
) {
  const submitting = ref(false)
  const copy = computed(() => COPY[editor.locale.value])

  async function submitProfile(allowUnverifiedWeather = false): Promise<void> {
    if (submitting.value || weather.locating.value || !flow.prepareSubmission()) return
    const hasVerifiedKey = weather.hasVerifiedKey.value
    if (!allowUnverifiedWeather && !hasVerifiedKey && weather.offerUnverifiedSave()) return

    submitting.value = true
    flow.clearSubmissionFailure()
    try {
      const profile = buildProfile(editor.draft)
      const skipWeatherValidation = allowUnverifiedWeather || hasVerifiedKey
      const committed = editor.mode === "setup"
        ? await createInitialProfile(profile, skipWeatherValidation)
        : await applyProfile(profile, skipWeatherValidation)
      editor.commit(committed)
      flow.resetFeedback()
      weather.clearSaveFeedback()
      if (editor.mode === "setup") {
        toast.success(copy.value.review.setupSuccess)
        await closeWindow()
      } else {
        toast.success(copy.value.review.success)
      }
    } catch (error) {
      if (allowUnverifiedWeather || !weather.offerUnverifiedSave(error)) flow.reportSubmissionFailure(error)
    } finally {
      submitting.value = false
    }
  }

  return { submitting, submitProfile }
}
