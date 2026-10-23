import type { ActivityProfile } from "@/api/profile"
import type { ProfileDraft } from "./draft"

export function copyActivity(activity: ActivityProfile | null): ActivityProfile {
  if (activity === null)
    return { work_processes: [], leisure_processes: [], work_title_keywords: [], leisure_title_keywords: [] }
  return {
    work_processes: [...activity.work_processes],
    leisure_processes: [...activity.leisure_processes],
    work_title_keywords: [...activity.work_title_keywords],
    leisure_title_keywords: [...activity.leisure_title_keywords],
  }
}

export type ActivityField = keyof ProfileDraft["activity"]
export type PendingActivity = Record<ActivityField, string>

export function emptyPendingActivity(): PendingActivity {
  return {
    work_processes: "",
    leisure_processes: "",
    work_title_keywords: "",
    leisure_title_keywords: "",
  }
}

export function normalizeProcess(value: string): string {
  return value
    .trim()
    .toLocaleLowerCase()
    .replace(/\.exe$/i, "")
}

export function normalizeTitle(value: string): string {
  return value.trim().toLocaleLowerCase()
}

export function activityConflicts(draft: ProfileDraft): string[] {
  const workProcesses = new Set(draft.activity.work_processes.map(normalizeProcess))
  const leisureProcesses = new Set(draft.activity.leisure_processes.map(normalizeProcess))
  const workTitles = new Set(draft.activity.work_title_keywords.map(normalizeTitle))
  const leisureTitles = new Set(draft.activity.leisure_title_keywords.map(normalizeTitle))

  return [
    ...[...workProcesses].filter((value) => leisureProcesses.has(value)),
    ...[...workTitles].filter((value) => leisureTitles.has(value)),
  ].filter(Boolean)
}
