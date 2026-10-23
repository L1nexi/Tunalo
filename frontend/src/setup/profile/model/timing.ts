import type { ProfileDraft } from "./draft"

export const DISTURBANCE_PRESETS = {
  eager: {
    startup_grace_seconds: 5,
    idle_before_switch_seconds: 10,
    cycle_interval_minutes: 5,
  },
  responsive: {
    startup_grace_seconds: 15,
    idle_before_switch_seconds: 15,
    cycle_interval_minutes: 10,
  },
  balanced: {
    startup_grace_seconds: 15,
    idle_before_switch_seconds: 20,
    cycle_interval_minutes: 15,
  },
  quiet: {
    startup_grace_seconds: 30,
    idle_before_switch_seconds: 60,
    cycle_interval_minutes: 30,
  },
  minimal: {
    startup_grace_seconds: 60,
    idle_before_switch_seconds: 120,
    cycle_interval_minutes: 60,
  },
} as const

export type DisturbancePreset = keyof typeof DISTURBANCE_PRESETS

export function parseNumberInput(value: string | number): number | null {
  if (value === "") return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

/** 防打扰计时值全部为不小于 0 的整数；保存可用性与错误跳转的折叠区展开共用同一规则。 */
export function hasValidTiming(disturbance: ProfileDraft["disturbance"]): boolean {
  return Object.values(disturbance).every(isNonNegativeInteger)
}

export function isNonNegativeInteger(value: number | null): value is number {
  return value !== null && Number.isInteger(value) && value >= 0
}

export function requireNonNegativeInteger(value: number | null): number {
  if (!isNonNegativeInteger(value)) throw new Error("non_negative_integer_required")
  return value
}

export function detectDisturbancePreset(
  draft: Pick<ProfileDraft, "disturbance">,
): DisturbancePreset | "custom" {
  const match = Object.entries(DISTURBANCE_PRESETS).find(([, values]) =>
    Object.entries(values).every(
      ([key, value]) => draft.disturbance[key as keyof ProfileDraft["disturbance"]] === value,
    ),
  )
  return (match?.[0] as DisturbancePreset | undefined) ?? "custom"
}
