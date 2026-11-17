import { computed, nextTick, ref } from "vue"

import { COPY } from "@/setup/copy"
import { evaluateSteps, STEP_ORDER, WIDE_STEPS } from "./steps"
import type { StepId } from "./steps"
import type { usePlaylistScan } from "@/setup/wallpaper/usePlaylistScan"
import type { ProfileEditor } from "@/setup/profile/useProfileDraft"

export type PageId = StepId | "application"
export type PageFocus = "heading" | "error"

/** 统一页面选择、导航状态和进入页面后的焦点；Profile 校验仍以 StepId 为范围。 */
export function useSetupNavigation(editor: ProfileEditor, scan: ReturnType<typeof usePlaylistScan>) {
  const { draft, locale, mode, changedSteps } = editor
  const copy = computed(() => COPY[locale.value])
  const selectedPage = ref<PageId>("wallpaper")
  const previousPage = ref<PageId>("wallpaper")
  const activePage = computed(() => selectedPage.value)
  const evaluation = computed(() => evaluateSteps(draft, scan.ready.value, scan.usablePlaylists.value))
  const allValid = computed(() => Object.values(evaluation.value.validity).every(Boolean))
  const missingSteps = computed(() =>
    STEP_ORDER.filter((id) => id !== "review" && !isStepValid(id)).map((id) => ({
      id,
      ...copy.value.steps[id],
    })),
  )
  const navigationItems = computed(() => {
    const pages: PageId[] = ["application", ...STEP_ORDER]
    return pages.map((id) => ({
      id,
      title:
        id === "application"
          ? copy.value.application.title
          : id === "review"
            ? mode === "setup"
              ? copy.value.nav.reviewSetup
              : copy.value.nav.reviewSettings
            : copy.value.steps[id].title,
      status: id === "application" ? "" : stepStatus(id),
      nextRequired: id === missingSteps.value[0]?.id,
    }))
  })
  const activeHeading = computed(() => {
    const content = copy.value
    const headings = {
      application: content.application,
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
    const { title, description } = headings[activePage.value]
    return { title, description }
  })
  const contentClass = computed(() =>
    activePage.value !== "application" && WIDE_STEPS.has(activePage.value) ? "max-w-4xl" : "max-w-[47.5rem]",
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

  async function focusContent(focus: PageFocus): Promise<void> {
    await nextTick()
    if (focus === "heading") document.getElementById("setup-step-content")?.scrollTo({ top: 0 })
    const target = focus === "error"
      ? [...document.querySelectorAll<HTMLElement>("#setup-step-content [aria-invalid='true']")].find(
          (element) => element.getClientRects().length > 0,
        )
      : null
    ;(target ?? document.getElementById("setup-step-heading"))?.focus()
  }

  function navigateTo(id: PageId, focus: PageFocus = "heading"): void {
    if (activePage.value !== "review" && id === "review") previousPage.value = activePage.value
    selectedPage.value = id
    void focusContent(focus)
  }

  return {
    activePage,
    previousPage: computed(() => previousPage.value),
    navigationItems,
    activeHeading,
    contentClass,
    evaluation,
    allValid,
    missingSteps,
    isStepValid,
    navigateTo,
  }
}

export type SetupNavigation = ReturnType<typeof useSetupNavigation>
