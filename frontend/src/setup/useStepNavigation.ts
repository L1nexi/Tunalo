import { computed, nextTick, ref } from "vue"

import { COPY } from "./copy"
import { evaluateSteps, STEP_ORDER, WIDE_STEPS } from "./flow"
import type { StepId } from "./flow"
import type { usePlaylistScan } from "./usePlaylistScan"
import type { ProfileEditor } from "./useProfileDraft"

/** 维护步骤状态、标题和焦点；字段错误由反馈模块解释。 */
export function useStepNavigation(editor: ProfileEditor, scan: ReturnType<typeof usePlaylistScan>) {
  const { draft, locale, mode, changedSteps } = editor
  const copy = computed(() => COPY[locale.value])
  const activeStep = ref<StepId>("wallpaper")
  const previousSection = ref<StepId>("wallpaper")
  const evaluation = computed(() => evaluateSteps(draft, scan.ready.value, scan.usablePlaylists.value))
  const allValid = computed(() => Object.values(evaluation.value.validity).every(Boolean))
  const missingSteps = computed(() =>
    STEP_ORDER.filter((id) => id !== "review" && !isStepValid(id)).map((id) => ({
      id,
      ...copy.value.steps[id],
    })),
  )
  const steps = computed(() =>
    STEP_ORDER.map((id) => ({
      id,
      title:
        id === "review"
          ? mode === "setup"
            ? copy.value.nav.reviewSetup
            : copy.value.nav.reviewSettings
          : copy.value.steps[id].title,
      status: stepStatus(id),
      nextRequired: id === missingSteps.value[0]?.id,
    })),
  )
  const activeHeading = computed(() => {
    const content = copy.value
    const headings = {
      wallpaper: content.wallpaper,
      weather: content.weather,
      scenes: content.scenes,
      scheduling: content.preferences,
      activity: content.activity,
      review: {
        title: mode === "setup" ? content.nav.reviewSetup : content.nav.reviewSettings,
        description: content.review.description,
      },
    }
    const { title, description } = headings[activeStep.value]
    return { title, description }
  })
  const stepContentClass = computed(() =>
    WIDE_STEPS.has(activeStep.value) ? "max-w-4xl" : "max-w-[47.5rem]",
  )

  function isStepValid(id: StepId): boolean {
    return id === "review" ? allValid.value : evaluation.value.validity[id]
  }

  function stepStatus(id: StepId): string {
    if (id === "review") return ""
    if (mode === "settings") return changedSteps.value.has(id) ? copy.value.nav.changed : ""
    if (!isStepValid(id)) return copy.value.nav.pending
    if (id === "activity" && !changedSteps.value.has(id)) return copy.value.nav.optional
    if (id === "scheduling" && !changedSteps.value.has(id)) return copy.value.nav.defaultReady
    return copy.value.nav.complete
  }

  async function focusStep(errorFirst: boolean): Promise<void> {
    await nextTick()
    if (!errorFirst) document.getElementById("setup-step-content")?.scrollTo({ top: 0 })
    const target = errorFirst
      ? [...document.querySelectorAll<HTMLElement>("#setup-step-content [aria-invalid='true']")].find(
          (element) => element.getClientRects().length > 0,
        )
      : null
    ;(target ?? document.getElementById("setup-step-heading"))?.focus()
  }

  function navigateTo(id: StepId): void {
    if (activeStep.value !== "review" && id === "review") previousSection.value = activeStep.value
    activeStep.value = id
    void focusStep(false)
  }

  return {
    activeStep,
    previousSection,
    steps,
    activeHeading,
    stepContentClass,
    evaluation,
    allValid,
    missingSteps,
    isStepValid,
    navigateTo,
    focusStep,
  }
}

export type StepNavigation = ReturnType<typeof useStepNavigation>
