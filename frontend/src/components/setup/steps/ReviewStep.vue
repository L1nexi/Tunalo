<script setup lang="ts">
import { CheckCircle2Icon, CircleDashedIcon, CircleXIcon, GaugeIcon, TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale, SceneId } from "@/api/profile"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { COPY, DISTURBANCE_LABELS, RESPONSE_STYLE_LABELS, SCENE_LABELS } from "@/setup/copy"
import type { StepId } from "@/setup/flow"
import { detectDisturbancePreset } from "@/setup/model"
import type { ProfileDraft } from "@/setup/model"

const props = defineProps<{
  locale: Locale
  draft: ProfileDraft
  savedDraft: ProfileDraft
  mode: "setup" | "settings"
  valid: boolean
  missingSteps: Array<{ id: StepId, title: string }>
  weatherKeyState: "untested" | "valid" | "invalid" | "quota"
  weatherTestedAtText: string
  weatherConnectionError: string
  validatingWeather: boolean
}>()

const emit = defineEmits<{
  validateWeather: []
  openStep: [id: StepId]
}>()

const copy = computed(() => COPY[props.locale])
const preset = computed(() => detectDisturbancePreset(props.draft))
const locationSummary = computed(() => {
  const location = props.draft.weather.location
  if (location.latitude === null || location.longitude === null) return copy.value.common.notSet
  return copy.value.review.coordinates(location.latitude, location.longitude)
})
const weatherSummary = computed(() => {
  if (props.weatherKeyState === "valid") return copy.value.weather.keyValid
  if (props.weatherKeyState === "invalid") return copy.value.errors.issueCodes.weather_api_key_invalid
  if (props.weatherKeyState === "quota") return copy.value.errors.issueCodes.weather_api_quota_exceeded
  return copy.value.review.weatherUntested
})
const weatherStatusIcon = computed(() => {
  if (props.weatherKeyState === "valid") return CheckCircle2Icon
  if (props.weatherKeyState === "invalid") return CircleXIcon
  if (props.weatherKeyState === "quota") return TriangleAlertIcon
  return CircleDashedIcon
})
const weatherStatusClass = computed(() => {
  if (props.weatherKeyState === "valid") return "text-success"
  if (props.weatherKeyState === "invalid") return "text-destructive"
  if (props.weatherKeyState === "quota") return "text-warning"
  return "text-muted-foreground"
})
const sceneSummary = computed(() => {
  const assignments = Object.values(props.draft.scenes)
  return copy.value.review.sceneCount(assignments.filter(Boolean).length, assignments.filter((value) => !value).length)
})
const sceneIds = computed(() => Object.keys(props.draft.scenes) as SceneId[])
const changes = computed(() => {
  const before = props.savedDraft
  const after = props.draft
  const list: Array<{ id: StepId, label: string, before: string, after: string }> = []
  const empty = copy.value.common.notSet
  const add = (id: StepId, label: string, oldValue: unknown, newValue: unknown, hide = false) => {
    if (JSON.stringify(oldValue) === JSON.stringify(newValue)) return
    list.push({
      id,
      label,
      before: hide ? copy.value.review.secretChanged : String(oldValue ?? empty),
      after: hide ? copy.value.review.secretChanged : String(newValue ?? empty),
    })
  }
  add("wallpaper", copy.value.review.wallpaper, before.wallpaper_engine_path, after.wallpaper_engine_path)
  add("weather", copy.value.weather.keyLabel, before.weather.api_key, after.weather.api_key, true)
  add("weather", copy.value.review.location,
    before.weather.location.latitude === null || before.weather.location.longitude === null ? empty : copy.value.review.coordinates(before.weather.location.latitude, before.weather.location.longitude),
    locationSummary.value)
  for (const id of Object.keys(SCENE_LABELS[props.locale]) as SceneId[]) {
    add("scenes", SCENE_LABELS[props.locale][id], before.scenes[id] || copy.value.review.disabled, after.scenes[id] || (id in after.scenes ? copy.value.review.awaitingPlaylist : copy.value.review.disabled))
  }
  add("scheduling", copy.value.review.response,
    RESPONSE_STYLE_LABELS[props.locale][before.matching.response_style],
    RESPONSE_STYLE_LABELS[props.locale][after.matching.response_style])
  const timingLabels = {
    startup_grace_seconds: copy.value.preferences.startupGrace,
    idle_before_switch_seconds: copy.value.preferences.idleBeforeSwitch,
    maximum_deferral_minutes: copy.value.preferences.maximumDeferral,
    cycle_interval_minutes: copy.value.preferences.cycleInterval,
  }
  for (const field of Object.keys(timingLabels) as Array<keyof typeof timingLabels>) {
    add("scheduling", timingLabels[field], before.disturbance[field], after.disturbance[field])
  }
  for (const field of ["work_processes", "leisure_processes", "work_title_keywords", "leisure_title_keywords"] as const) {
    const group = field.startsWith("work") ? copy.value.activity.workTitle : copy.value.activity.leisureTitle
    const kind = field.endsWith("processes") ? copy.value.activity.processLabel : copy.value.activity.titleKeywordLabel
    add("activity", `${group} · ${kind}`, before.activity[field].join("、") || empty, after.activity[field].join("、") || empty)
  }
  const languageName = (value: string | null) => value === "zh" ? "中文" : value === "en" ? "English" : empty
  add("review", copy.value.nav.languageLabel, languageName(before.language), languageName(after.language))
  return list
})
// 检查页按分类分组展示；deEmphasized 组内的取值为技术细节（路径），降权为普通文本，关键选择保持强调。
const reviewGroups = computed(() => [
  {
    id: "wallpaper" as const,
    deEmphasized: true,
    rows: [{ id: "wallpaper", label: copy.value.review.wallpaper, value: props.draft.wallpaper_engine_path || copy.value.common.notSet }],
  },
  {
    id: "weather" as const,
    rows: [
      { id: "weather", label: copy.value.review.weather, value: weatherSummary.value },
      { id: "location", label: copy.value.review.location, value: locationSummary.value },
    ],
  },
  {
    id: "scenes" as const,
    rows: [{ id: "scenes", label: copy.value.review.scenes, value: sceneSummary.value }],
  },
  {
    id: "scheduling" as const,
    rows: [
      { id: "response", label: copy.value.review.response, value: RESPONSE_STYLE_LABELS[props.locale][props.draft.matching.response_style] },
      { id: "disturbance", label: copy.value.review.disturbance, value: preset.value === "custom" ? copy.value.common.custom : DISTURBANCE_LABELS[props.locale][preset.value] },
    ],
  },
  {
    id: "activity" as const,
    rows: [{ id: "activity", label: copy.value.review.activity, value: copy.value.review.activityCount(
      props.draft.activity.work_title_keywords.length + props.draft.activity.leisure_title_keywords.length,
      props.draft.activity.work_processes.length + props.draft.activity.leisure_processes.length,
    ) }],
  },
])
</script>

<template>
  <section class="flex flex-col gap-6">
    <section v-if="mode === 'settings'" aria-labelledby="changes-heading">
      <h2 id="changes-heading" class="mb-3 text-base font-semibold">{{ copy.review.changesTitle }}</h2>
      <p v-if="changes.length === 0" role="status" class="text-sm text-muted-foreground">{{ copy.review.noChanges }}</p>
      <ul v-else class="divide-y rounded-lg border">
        <li v-for="(change, index) in changes" :key="`${change.id}-${index}`" class="flex flex-wrap items-start justify-between gap-3 px-4 py-3">
          <div class="min-w-0">
            <p class="text-sm font-medium">{{ change.label }}</p>
            <p v-if="change.before !== copy.review.secretChanged" class="text-sm text-muted-foreground [overflow-wrap:anywhere]">{{ change.before }} → {{ change.after }}</p>
            <p v-else class="text-sm text-muted-foreground">{{ change.after }}</p>
          </div>
          <Button type="button" variant="ghost" size="sm" @click="emit('openStep', change.id)">{{ copy.review.edit }}</Button>
        </li>
      </ul>
    </section>

    <details :open="mode === 'setup' || undefined">
      <summary v-if="mode === 'settings'" class="cursor-pointer text-sm font-medium">{{ copy.review.currentDetails }}</summary>
      <div class="mt-3 flex flex-col gap-6">
        <section v-for="group in reviewGroups" :key="group.id" class="flex flex-col gap-3">
          <h3 class="text-base font-semibold">{{ copy.steps[group.id].title }}</h3>
          <dl class="rounded-lg border">
            <div
              v-for="row in group.rows"
              :key="row.id"
              class="grid min-w-0 gap-1 border-b px-4 py-3 last:border-b-0 sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-4"
            >
              <dt class="text-sm text-muted-foreground">{{ row.label }}</dt>
              <dd class="min-w-0">
                <div v-if="row.id === 'weather'" class="flex min-w-0 flex-wrap items-start justify-between gap-3">
                  <div class="min-w-0">
                    <p class="flex items-center gap-2 text-sm font-medium" role="status">
                      <component :is="weatherStatusIcon" :class="weatherStatusClass" />
                      <span>{{ row.value }}</span>
                    </p>
                    <p v-if="weatherConnectionError" class="mt-1 flex items-start gap-2 text-sm text-warning">
                      <TriangleAlertIcon class="mt-0.5 shrink-0" />
                      <span class="min-w-0">{{ weatherConnectionError }}</span>
                    </p>
                    <p v-if="copy.review.weatherNote" class="mt-1 text-xs text-muted-foreground">{{ copy.review.weatherNote }}</p>
                    <p v-if="weatherTestedAtText" class="mt-1 text-xs text-muted-foreground">{{ weatherTestedAtText }}</p>
                  </div>
                  <Button size="sm" variant="outline" :disabled="validatingWeather || !draft.weather.api_key.trim()" @click="emit('validateWeather')">
                    <Spinner v-if="validatingWeather" data-icon="inline-start" />
                    <GaugeIcon v-else data-icon="inline-start" />
                    {{ validatingWeather ? copy.weather.validating : copy.weather.validate }}
                  </Button>
                </div>
                <div v-else class="text-sm [overflow-wrap:anywhere]" :class="group.deEmphasized ? 'font-normal text-muted-foreground' : 'font-medium'">
                  {{ row.value }}
                  <ul v-if="row.id === 'scenes'" class="mt-1 text-sm font-normal text-muted-foreground">
                    <li v-for="id in sceneIds" :key="id">{{ SCENE_LABELS[locale][id] }}：{{ draft.scenes[id] || copy.common.notSet }}</li>
                  </ul>
                </div>
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </details>

    <Alert v-if="!valid" variant="destructive">
      <TriangleAlertIcon />
      <AlertTitle>{{ copy.review.missingTitle }}</AlertTitle>
      <AlertDescription class="flex flex-col gap-3">
        <span>{{ copy.review.missingDescription }}</span>
        <span class="flex flex-wrap gap-2">
          <Button v-for="step in missingSteps" :key="step.id" size="sm" variant="outline" @click="emit('openStep', step.id)">{{ step.title }}</Button>
        </span>
      </AlertDescription>
    </Alert>
  </section>
</template>
