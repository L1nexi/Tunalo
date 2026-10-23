import type { Locale } from "@/api/profile"
import { COPY, associationSummary, preferenceSummary } from "../copy"
import type { StepId } from "../flow"
import type { ProfileDraft } from "../model"
import { reviewLocation } from "./summary"

interface ProfileChange {
  id: StepId
  label: string
  before: string
  after: string
}

/** 将已保存基线与当前草稿的差异表达为可回到对应步骤的可读条目。 */
export function describeProfileChanges(
  before: ProfileDraft,
  after: ProfileDraft,
  locale: Locale,
): ProfileChange[] {
  const copy = COPY[locale]
  const list: ProfileChange[] = []
  const empty = copy.common.notSet
  const add = (id: StepId, label: string, oldValue: unknown, newValue: unknown, hide = false) => {
    if (JSON.stringify(oldValue) === JSON.stringify(newValue)) return
    list.push({
      id,
      label,
      before: hide ? copy.review.secretChanged : String(oldValue ?? empty),
      after: hide ? copy.review.secretChanged : String(newValue ?? empty),
    })
  }
  add("wallpaper", copy.review.wallpaper, before.wallpaper_engine_path, after.wallpaper_engine_path)
  add("weather", copy.weather.keyLabel, before.weather.api_key, after.weather.api_key, true)
  add("weather", copy.review.location, reviewLocation(before, locale), reviewLocation(after, locale))
  for (const id of new Set([...Object.keys(before.scenes), ...Object.keys(after.scenes)])) {
    const describe = (scene: ProfileDraft["scenes"][string] | undefined) =>
      scene
        ? `${scene.name} · ${associationSummary(scene.associations, locale)} · ${scene.playlist || copy.review.awaitingPlaylist}`
        : copy.review.disabled
    add(
      "scenes",
      after.scenes[id]?.name ?? before.scenes[id]!.name,
      describe(before.scenes[id]),
      describe(after.scenes[id]),
    )
  }
  add(
    "scheduling",
    copy.review.response,
    preferenceSummary(before.matching.preference_tiers, locale),
    preferenceSummary(after.matching.preference_tiers, locale),
  )
  const timingRows = [
    { field: "startup_grace_seconds", label: copy.preferences.startupGrace, unit: copy.preferences.seconds },
    {
      field: "idle_before_switch_seconds",
      label: copy.preferences.idleBeforeSwitch,
      unit: copy.preferences.seconds,
    },
    {
      field: "cycle_interval_minutes",
      label: copy.preferences.cycleInterval,
      unit: copy.preferences.minutes,
    },
  ] as const
  for (const { field, label, unit } of timingRows) {
    const withUnit = (value: unknown) =>
      value === null || value === undefined ? empty : `${String(value)} ${unit}`
    add("scheduling", label, withUnit(before.disturbance[field]), withUnit(after.disturbance[field]))
  }
  for (const field of [
    "work_processes",
    "leisure_processes",
    "work_title_keywords",
    "leisure_title_keywords",
  ] as const) {
    const group = field.startsWith("work") ? copy.activity.workTitle : copy.activity.leisureTitle
    const kind = field.endsWith("processes") ? copy.activity.processLabel : copy.activity.titleKeywordLabel
    add(
      "activity",
      `${group} · ${kind}`,
      before.activity[field].join("、") || empty,
      after.activity[field].join("、") || empty,
    )
  }
  const languageName = (value: string | null) =>
    value === "zh" ? "中文" : value === "en" ? "English" : empty
  add("review", copy.nav.languageLabel, languageName(before.language), languageName(after.language))
  return list
}
