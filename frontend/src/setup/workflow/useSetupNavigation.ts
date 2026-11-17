import { computed, nextTick, ref } from "vue"

import { COPY } from "@/setup/copy"
import { createSetupPages } from "./pages"
import type { PageId } from "./pages"
import { evaluateSteps, STEP_ORDER } from "./steps"
import type { StepId } from "./steps"
import type { usePlaylistScan } from "@/setup/wallpaper/usePlaylistScan"
import type { ProfileEditor } from "@/setup/profile/useProfileDraft"

export type PageFocus = "heading" | "error"

/** 统一页面选择、导航状态和进入页面后的焦点；Profile 校验仍以 StepId 为范围。 */
export function useSetupNavigation(editor: ProfileEditor, scan: ReturnType<typeof usePlaylistScan>) {
  const { draft, locale, mode, changedSteps } = editor
  const copy = computed(() => COPY[locale.value])
  const selectedPage = ref<PageId>("wallpaper")
  const previousPage = ref<PageId>("wallpaper")
  const activePage = computed(() => selectedPage.value)
  const pages = computed(() => createSetupPages(locale.value, mode))
  const currentPage = computed(() => pages.value.find((page) => page.id === activePage.value)!)
  const evaluation = computed(() => evaluateSteps(draft, scan.ready.value, scan.usablePlaylists.value))
  const allValid = computed(() => Object.values(evaluation.value.validity).every(Boolean))
  const missingSteps = computed(() =>
    STEP_ORDER.filter((id) => id !== "review" && !isStepValid(id)).map((id) => ({
      id,
      ...copy.value.steps[id],
    })),
  )
  const navigationItems = computed(() =>
    pages.value.map((page) => ({
      id: page.id,
      title: page.title,
      icon: page.icon,
      status: page.profileStep === null ? "" : stepStatus(page.profileStep),
      nextRequired: page.profileStep === missingSteps.value[0]?.id,
    })),
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
    currentPage,
    navigationItems,
    evaluation,
    allValid,
    missingSteps,
    isStepValid,
    navigateTo,
  }
}

export type SetupNavigation = ReturnType<typeof useSetupNavigation>
