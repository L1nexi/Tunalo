import type { ContextVariable, Locale, SceneAssociations } from "@/api/profile";
import { SCENE_ITEMS, SCENE_VARIABLES } from "../scenes";
import { CONTEXT_VARIABLE_LABELS } from "./context-labels";
import { PREFERENCES_COPY } from "./preferences";
import { SCENE_LABELS } from "./scene-labels";

export function preferenceSummary(tiers: ContextVariable[][], locale: Locale): string {
  const labels = CONTEXT_VARIABLE_LABELS[locale];
  return (
    tiers
      .map((tier) => tier.map((variable) => labels[variable]).join(locale === "zh" ? "、" : ", "))
      .join(" > ") || PREFERENCES_COPY[locale].unassigned
  );
}

export function associationSummary(associations: SceneAssociations, locale: Locale): string {
  return SCENE_VARIABLES.filter((variable) => associations[variable]?.length)
    .map((variable) =>
      SCENE_ITEMS[variable]
        .filter((item) => associations[variable]!.includes(item))
        .map((item) => SCENE_LABELS[locale].semanticLabels[item])
        .join(locale === "zh" ? "或" : " or "),
    )
    .join(" · ");
}
