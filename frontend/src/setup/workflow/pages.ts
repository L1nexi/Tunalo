import type { Component } from "vue"
import {
  AppWindowIcon, ClipboardCheckIcon, CloudSunIcon, LayersIcon,
  MonitorIcon, SettingsIcon, SlidersHorizontalIcon,
} from "@lucide/vue"

import type { Locale } from "@/api/profile"
import { COPY } from "@/setup/copy"
import type { SetupMode } from "@/setup/profile/useProfileDraft"
import { STEP_ORDER } from "./steps"
import type { StepId } from "./steps"

export type PageId = StepId | "application"

export interface PageDefinition {
  readonly id: PageId
  readonly title: string
  readonly heading: { readonly title: string; readonly description: string }
  readonly icon: Component
  readonly contentClass: string
  readonly profileStep: StepId | null
  readonly feedback: "local" | "profile"
  readonly footer: {
    readonly leading: "close" | "back"
    readonly review: boolean
    readonly submit: boolean
  }
}

const FORM_CONTENT_CLASS = "max-w-[47.5rem]"
const WIDE_CONTENT_CLASS = "max-w-4xl"

export function createSetupPages(locale: Locale, mode: SetupMode): readonly PageDefinition[] {
  const copy = COPY[locale]
  const reviewTitle = mode === "setup" ? copy.nav.reviewSetup : copy.nav.reviewSettings
  const profilePages = {
    wallpaper: { heading: copy.wallpaper, icon: MonitorIcon, contentClass: FORM_CONTENT_CLASS },
    weather: { heading: copy.weather, icon: CloudSunIcon, contentClass: FORM_CONTENT_CLASS },
    scenes: { heading: copy.scenes, icon: LayersIcon, contentClass: WIDE_CONTENT_CLASS },
    scheduling: { heading: copy.preferences, icon: SlidersHorizontalIcon, contentClass: FORM_CONTENT_CLASS },
    activity: { heading: copy.activity, icon: AppWindowIcon, contentClass: WIDE_CONTENT_CLASS },
    review: {
      heading: { title: reviewTitle, description: copy.review.description },
      icon: ClipboardCheckIcon,
      contentClass: FORM_CONTENT_CLASS,
    },
  } satisfies Record<StepId, Pick<PageDefinition, "heading" | "icon" | "contentClass">>

  return [
    {
      id: "application",
      title: copy.application.title,
      heading: { title: copy.application.title, description: copy.application.description },
      icon: SettingsIcon,
      contentClass: FORM_CONTENT_CLASS,
      profileStep: null,
      feedback: "local",
      footer: { leading: "close", review: mode === "setup", submit: false },
    },
    ...STEP_ORDER.map((id): PageDefinition => {
      const review = id === "review"
      const { title, description } = profilePages[id].heading
      return {
        id,
        title: review ? reviewTitle : copy.steps[id].title,
        heading: { title, description },
        icon: profilePages[id].icon,
        contentClass: profilePages[id].contentClass,
        profileStep: id,
        feedback: "profile",
        footer: {
          leading: review ? "back" : "close",
          review: !review,
          submit: review || mode === "settings",
        },
      }
    }),
  ]
}
