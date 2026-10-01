import { computed, nextTick, ref, shallowRef } from "vue"

import { ApiError } from "@/api/profile"
import type { ValidationIssue } from "@/api/profile"
import { COPY } from "./copy"
import { describeError } from "./errorMessages"
import { evaluateSteps, STEP_ORDER, stepForIssue, WIDE_STEPS } from "./flow"
import type { StepId } from "./flow"
import { validationIssueField } from "./model"
import type { ActivityField, ProfileDraft } from "./model"
import type { usePlaylistScan } from "./usePlaylistScan"
import type { ProfileEditor } from "./useProfileDraft"

/** 将编辑、跨步骤校验和错误定位收在同一处，步骤视图只接收自己的字段。 */
export function useSetupFlow(editor: ProfileEditor, scan: ReturnType<typeof usePlaylistScan>) {
  const { draft, locale, mode, pendingActivity, pendingActivityFields, changedSteps } = editor
  const copy = computed(() => COPY[locale.value])
  const activeStep = ref<StepId>("wallpaper")
  const previousSection = ref<StepId>("wallpaper")
  const stepError = ref<"validation" | "fieldValidation" | "pendingActivity" | null>(null)
  const validationIssues = ref<ValidationIssue[]>([])
  const submissionFailure = shallowRef<unknown>(null)
  const timingOpen = ref(false)
  const evaluation = computed(() => evaluateSteps(draft, scan.ready.value, scan.usablePlaylists.value))
  const allValid = computed(() => Object.values(evaluation.value.validity).every(Boolean))
  const missingSteps = computed(() => STEP_ORDER.filter((id) => id !== "review" && !isStepValid(id))
    .map((id) => ({ id, ...copy.value.steps[id] })))
  const steps = computed(() => STEP_ORDER.map((id) => ({
    id,
    title: id === "review" ? (mode === "setup" ? copy.value.nav.reviewSetup : copy.value.nav.reviewSettings) : copy.value.steps[id].title,
    status: stepStatus(id),
    nextRequired: id === missingSteps.value[0]?.id,
  })))
  const activeHeading = computed(() => {
    const content = copy.value
    switch (activeStep.value) {
      case "wallpaper": return { title: content.wallpaper.title, description: content.wallpaper.description }
      case "weather": return { title: content.weather.title, description: content.weather.description }
      case "scenes": return { title: content.scenes.title, description: content.scenes.description }
      case "scheduling": return { title: content.preferences.title, description: content.preferences.description }
      case "activity": return { title: content.activity.title, description: content.activity.description }
      case "review": return {
        title: mode === "setup" ? content.nav.reviewSetup : content.nav.reviewSettings,
        description: content.review.description,
      }
    }
  })
  const stepContentClass = computed(() => WIDE_STEPS.has(activeStep.value) ? "max-w-4xl" : "max-w-[47.5rem]")
  const stepErrorText = computed(() => stepError.value ? copy.value.errors[stepError.value] : "")
  const submissionError = computed(() => submissionFailure.value ? describeError(submissionFailure.value, locale.value) : "")
  const issuesByStep = computed<Record<StepId, Record<string, string[]>>>(() => {
    const grouped = Object.fromEntries(STEP_ORDER.map((id) => [id, {}])) as Record<StepId, Record<string, string[]>>
    for (const issue of validationIssues.value) {
      const fields = grouped[stepForIssue(issue.path)]
      const field = validationIssueField(issue.path)
      fields[field] ??= []
      fields[field].push(copy.value.errors.issueCodes[issue.code as keyof typeof copy.value.errors.issueCodes] ?? issue.message)
    }
    return grouped
  })

  function isStepValid(id: StepId): boolean {
    return id === "review" ? allValid.value : evaluation.value.validity[id]
  }

  function stepStatus(id: StepId): string {
    if (id === "review") return ""
    if (mode === "settings") return changedSteps.value.has(id) ? copy.value.nav.changed : ""
    if (!isStepValid(id)) return copy.value.nav.pending
    if ((id === "scheduling" || id === "activity") && !changedSteps.value.has(id)) return copy.value.nav.defaultReady
    return copy.value.nav.complete
  }

  async function focusStep(errorFirst: boolean): Promise<void> {
    await nextTick()
    const target = errorFirst
      ? [...document.querySelectorAll<HTMLElement>("#setup-step-content [aria-invalid='true']")]
        .find((element) => element.getClientRects().length > 0)
      : null
    ;(target ?? document.getElementById("setup-step-heading"))?.focus()
  }

  function navigateTo(id: StepId): void {
    if (activeStep.value !== "review" && id === "review") previousSection.value = activeStep.value
    activeStep.value = id
    stepError.value = null
    submissionFailure.value = null
    void focusStep(false)
  }

  function navigateToStep(id: StepId): void {
    const needsAttention = activeStep.value === "review" && !isStepValid(id)
    navigateTo(id)
    if (needsAttention) {
      stepError.value = "validation"
      void focusStep(true)
    }
  }

  function clearStepFeedback(id: StepId): void {
    validationIssues.value = validationIssues.value.filter((issue) => stepForIssue(issue.path) !== id)
    if (activeStep.value === id) stepError.value = null
    submissionFailure.value = null
  }

  function clearWeatherFieldFeedback(field: "api_key" | "location"): void {
    validationIssues.value = validationIssues.value.filter((issue) =>
      !(issue.path[0] === "weather" && issue.path[1] === field))
    if (activeStep.value === "weather" && isStepValid("weather") &&
      !validationIssues.value.some((issue) => stepForIssue(issue.path) === "weather")) stepError.value = null
    submissionFailure.value = null
  }

  function updatePath(value: string): void {
    editor.updatePath(value)
    clearStepFeedback("wallpaper")
  }

  function updateScenes(value: ProfileDraft["scenes"]): void {
    draft.scenes = value
    clearStepFeedback("scenes")
  }

  function updateMatching(value: ProfileDraft["matching"]): void {
    draft.matching = value
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
    if (stepError.value === "pendingActivity" && pendingActivityFields.value.length === 0) stepError.value = null
  }

  function prepareSubmission(): boolean {
    if (pendingActivityFields.value.length > 0) {
      navigateToStep("activity")
      stepError.value = "pendingActivity"
      void focusStep(true)
      return false
    }
    if (!allValid.value) {
      activeStep.value = missingSteps.value[0]?.id ?? "wallpaper"
      stepError.value = "validation"
      void focusStep(true)
      return false
    }
    return mode !== "settings" || editor.isDirty.value
  }

  function reportSubmissionFailure(error: unknown): void {
    if (!(error instanceof ApiError) || !error.payload.issues?.length) {
      submissionFailure.value = error
      return
    }
    validationIssues.value = error.payload.issues
    activeStep.value = STEP_ORDER.find((id) => error.payload.issues?.some((issue) => stepForIssue(issue.path) === id)) ?? "review"
    if (error.payload.issues.some((issue) => issue.path[0] === "disturbance")) timingOpen.value = true
    stepError.value = "fieldValidation"
    submissionFailure.value = null
    void focusStep(true)
  }

  function clearSubmissionFailure(): void {
    submissionFailure.value = null
  }

  function resetFeedback(): void {
    validationIssues.value = []
    stepError.value = null
    submissionFailure.value = null
  }

  return {
    activeStep, previousSection, steps, activeHeading, stepContentClass,
    evaluation, allValid, missingSteps, stepError, stepErrorText, submissionError, issuesByStep, timingOpen,
    isStepValid, navigateTo, navigateToStep, clearStepFeedback, clearWeatherFieldFeedback,
    updatePath, updateScenes, updateMatching, updateDisturbance, updateActivity, updatePendingActivity,
    prepareSubmission, reportSubmissionFailure, clearSubmissionFailure, resetFeedback,
  }
}

export type SetupFlow = ReturnType<typeof useSetupFlow>
export type SetupNavigationItem = SetupFlow["steps"]["value"][number]
