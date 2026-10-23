import type { ContextVariable, Locale } from "@/api/profile";

export const CONTEXT_VARIABLE_LABELS: Record<Locale, Record<ContextVariable, string>> = {
  zh: { weather: "天气", activity: "活动", time: "时段", season: "季节" },
  en: { weather: "Weather", activity: "Activity", time: "Time", season: "Season" },
};
