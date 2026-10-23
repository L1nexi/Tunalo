import type { Locale } from "@/api/profile";
import { WORKSPACE_COPY } from "./workspace";
import { WALLPAPER_COPY } from "./wallpaper";
import { WEATHER_COPY } from "./weather";
import { LOCATION_COPY } from "./location";
import { SCENES_COPY } from "./scenes";
import { PREFERENCES_COPY } from "./preferences";
import { ACTIVITY_COPY } from "./activity";
import { REVIEW_COPY } from "./review";
import { ERRORS_COPY } from "./errors";

const zh = {
  ...WORKSPACE_COPY.zh,
  wallpaper: WALLPAPER_COPY.zh,
  weather: WEATHER_COPY.zh,
  location: LOCATION_COPY.zh,
  scenes: SCENES_COPY.zh,
  preferences: PREFERENCES_COPY.zh,
  activity: ACTIVITY_COPY.zh,
  review: REVIEW_COPY.zh,
  errors: ERRORS_COPY.zh,
};

const en = {
  ...WORKSPACE_COPY.en,
  wallpaper: WALLPAPER_COPY.en,
  weather: WEATHER_COPY.en,
  location: LOCATION_COPY.en,
  scenes: SCENES_COPY.en,
  preferences: PREFERENCES_COPY.en,
  activity: ACTIVITY_COPY.en,
  review: REVIEW_COPY.en,
  errors: ERRORS_COPY.en,
};

export const COPY = { zh, en } satisfies Record<Locale, typeof zh>;

export { CONTEXT_VARIABLE_LABELS } from "./context-labels";
export { associationSummary, preferenceSummary } from "./formatters";
export { DISTURBANCE_LABELS, ZH_TIMING_HINTS } from "./preferences";
export { ZH_WEATHER_SAVE_PROMPT } from "./weather";
