import { computed, ref, shallowRef } from "vue"

import { ApiError } from "@/api/profile"
import type { ValidationIssue } from "@/api/profile"
import { COPY } from "@/setup/copy"
import { describeError } from "@/setup/errorMessages"
import { STEP_ORDER, stepForIssue } from "./steps"
import type { StepId } from "./steps"
import { hasValidTiming } from "@/setup/profile/model"
import type { ProfileEditor } from "@/setup/profile/useProfileDraft"
import type { StepNavigation } from "./useStepNavigation"

function validationIssueField(path: Array<string | number>): string {
  const root = typeof path[0] === "string" ? path[0] : "profile"
  if (root === "activity" || root === "scenes") return root
  if (root === "weather" && path[1] === "location") {
    return typeof path[2] === "string" ? `weather.location.${path[2]}` : "weather.location"
  }
  if (["weather", "disturbance", "matching"].includes(root) && typeof path[1] === "string") {
    return `${root}.${path[1]}`
  }
  return root
}

/** 统一提交前检查、服务端字段错误和修改后的反馈清理。 */
export function useSetupFeedback(editor: ProfileEditor, navigation: StepNavigation) {
  const { draft, locale, mode, pendingActivityFields } = editor
  const { activeStep, allValid, missingSteps, isStepValid, focusStep } = navigation
  const copy = computed(() => COPY[locale.value])
  const stepError = ref<"validation" | "fieldValidation" | "pendingActivity" | null>(null)
  const validationIssues = ref<ValidationIssue[]>([])
  const submissionFailure = shallowRef<unknown>(null)
  const timingOpen = ref(false)
  const stepErrorText = computed(() => (stepError.value ? copy.value.errors[stepError.value] : ""))
  const submissionError = computed(() =>
    submissionFailure.value ? describeError(submissionFailure.value, locale.value) : "",
  )
  const issuesByStep = computed<Record<StepId, Record<string, string[]>>>(() => {
    const grouped = Object.fromEntries(STEP_ORDER.map((id) => [id, {}])) as Record<
      StepId,
      Record<string, string[]>
    >
    for (const issue of validationIssues.value) {
      const fields = grouped[stepForIssue(issue.path)]
      const field = validationIssueField(issue.path)
      fields[field] ??= []
      fields[field].push(
        issue.path[0] === "matching"
          ? copy.value.preferences.invalidPreferences
          : (copy.value.errors.issueCodes[issue.code as keyof typeof copy.value.errors.issueCodes] ??
              issue.message),
      )
    }
    return grouped
  })

  function navigateTo(id: StepId): void {
    navigation.navigateTo(id)
    stepError.value = null
    submissionFailure.value = null
  }

  function navigateToStep(id: StepId): void {
    const needsAttention = activeStep.value === "review" && !isStepValid(id)
    navigateTo(id)
    if (!needsAttention) return
    if (id === "scheduling" && !hasValidTiming(draft.disturbance)) timingOpen.value = true
    stepError.value = "validation"
    void focusStep(true)
  }

  function clearStepFeedback(id: StepId): void {
    validationIssues.value = validationIssues.value.filter((issue) => stepForIssue(issue.path) !== id)
    if (activeStep.value === id) stepError.value = null
    submissionFailure.value = null
  }

  function clearWeatherFieldFeedback(field: "api_key" | "location"): void {
    validationIssues.value = validationIssues.value.filter(
      (issue) => !(issue.path[0] === "weather" && issue.path[1] === field),
    )
    if (
      activeStep.value === "weather" &&
      isStepValid("weather") &&
      !validationIssues.value.some((issue) => stepForIssue(issue.path) === "weather")
    )
      stepError.value = null
    submissionFailure.value = null
  }

  function prepareSubmission(): boolean {
    if (pendingActivityFields.value.length > 0) {
      navigateToStep("activity")
      stepError.value = "pendingActivity"
      void focusStep(true)
      return false
    }
    if (!allValid.value) {
      activeStep.value = missingSteps.value[0].id
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
    activeStep.value =
      STEP_ORDER.find((id) => error.payload.issues?.some((issue) => stepForIssue(issue.path) === id)) ??
      "review"
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
    stepError,
    stepErrorText,
    submissionError,
    issuesByStep,
    timingOpen,
    navigateTo,
    navigateToStep,
    clearStepFeedback,
    clearWeatherFieldFeedback,
    prepareSubmission,
    reportSubmissionFailure,
    clearSubmissionFailure,
    resetFeedback,
  }
}
