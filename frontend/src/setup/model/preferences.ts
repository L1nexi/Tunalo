import { CONTEXT_VARIABLES, type ContextVariable } from "@/api/profile"
import type { ProfileDraft } from "./draft"

export interface PreferenceLayer {
  id: number
  variables: ContextVariable[]
}

export function normalizePreferenceTiers(tiers: ContextVariable[][]): ContextVariable[][] {
  return tiers
    .filter((tier) => tier.length > 0)
    .map((tier) => [...tier].sort((a, b) => CONTEXT_VARIABLES.indexOf(a) - CONTEXT_VARIABLES.indexOf(b)))
}

export function hasValidPreferences(matching: ProfileDraft["matching"]): boolean {
  const variables = matching.preference_tiers.flat()
  return (
    matching.preference_tiers.every((tier) => tier.length > 0) &&
    variables.every((variable) => CONTEXT_VARIABLES.includes(variable)) &&
    new Set(variables).size === variables.length
  )
}

export function preferenceFingerprint(matching: ProfileDraft["matching"]): string {
  return JSON.stringify(normalizePreferenceTiers(matching.preference_tiers))
}
