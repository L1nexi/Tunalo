<script setup lang="ts">
import type { Component } from "vue"
import {
  AppWindowIcon,
  CheckIcon,
  ChevronRightIcon,
  ClipboardCheckIcon,
  CloudSunIcon,
  LayersIcon,
  MonitorIcon,
  MoonIcon,
  SlidersHorizontalIcon,
  SunIcon,
  TriangleAlertIcon,
} from "@lucide/vue"
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, shallowRef, toRef, watch } from "vue"
import { toast } from "vue-sonner"

import type { Locale, Profile, SceneCatalogItem, ValidationIssue } from "@/api/profile"
import { ApiError, applyProfile, createInitialProfile, detectLocation, getSceneCatalog, validateWeatherKey } from "@/api/profile"
import ActivityRulesStep from "@/components/setup/steps/ActivityRulesStep.vue"
import LocationStep from "@/components/setup/steps/LocationStep.vue"
import ReviewStep from "@/components/setup/steps/ReviewStep.vue"
import SceneBindingsStep from "@/components/setup/steps/SceneBindingsStep.vue"
import SchedulingStep from "@/components/setup/steps/SchedulingStep.vue"
import WallpaperStep from "@/components/setup/steps/WallpaperStep.vue"
import WeatherKeyStep from "@/components/setup/steps/WeatherKeyStep.vue"
import TunaloMark from "@/components/TunaloMark.vue"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Spinner } from "@/components/ui/spinner"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { COPY, ZH_WEATHER_SAVE_PROMPT } from "@/setup/copy"
import { evaluateSteps, stepFingerprint, STEP_ORDER, stepForIssue, WIDE_STEPS } from "@/setup/flow"
import type { EditableStepId, StepId } from "@/setup/flow"
import { buildProfile, createProfileDraft, emptyPendingActivity, profileFingerprint, validationIssueField } from "@/setup/model"
import type { ActivityField, ProfileDraft } from "@/setup/model"
import { usePlaylistScan } from "@/setup/usePlaylistScan"
import { themeMode } from "@/theme"
import { cn } from "@/lib/utils"

const props = defineProps<{
  initialProfile: Profile | null
  initialLocale: Locale
}>()

const mode = computed<"setup" | "settings">(() => props.initialProfile === null ? "setup" : "settings")
const locale = ref<Locale>(props.initialProfile?.language ?? props.initialLocale)
const copy = computed(() => COPY[locale.value])
const draft = reactive<ProfileDraft>(createProfileDraft(props.initialProfile, locale.value))
const savedDraft = ref<ProfileDraft>(createProfileDraft(props.initialProfile, locale.value))
const baseline = ref(profileFingerprint(savedDraft.value))
const pendingActivity = reactive(emptyPendingActivity())
const rememberedScenes = reactive<ProfileDraft["scenes"]>({})
const scan = usePlaylistScan(toRef(draft, "wallpaper_engine_path"))

const currentIndex = ref(0)
const previousSectionIndex = ref(0)
const activeStep = computed<StepId>(() => STEP_ORDER[currentIndex.value] ?? "wallpaper")
const stepError = ref<"validation" | "fieldValidation" | "pendingActivity" | null>(null)
const validationIssues = ref<ValidationIssue[]>([])
const submissionFailure = shallowRef<unknown>(null)
const catalogFailure = shallowRef<unknown>(null)
const submitting = ref(false)
const locating = ref(false)
const locationDetectionStatus = ref<"idle" | "success" | "error">("idle")
const locationDetectionError = ref("")
const locationDetectionCity = ref<string | null>(null)
const validatingWeather = ref(false)
const weatherFailureKind = ref<null | "invalid" | "quota" | "connection">(null)
const weatherTestedAt = ref<number | null>(null)
const weatherValidationError = ref("")
const weatherValidationFailure = shallowRef<unknown>(null)
const verifiedWeatherKey = ref<string | null>(null)
const weatherSaveDialogOpen = ref(false)
const weatherSaveFailure = ref("")
const timingOpen = ref(false)
const closeDialogOpen = ref(false)
const hasNativeBridge = ref(Boolean(window.pywebview?.api))
const sceneCatalog = ref<SceneCatalogItem[]>([])

const stepIcons: Record<StepId, Component> = {
  wallpaper: MonitorIcon,
  weather: CloudSunIcon,
  scenes: LayersIcon,
  scheduling: SlidersHorizontalIcon,
  activity: AppWindowIcon,
  review: ClipboardCheckIcon,
}
const steps = computed(() => STEP_ORDER.map((id) => ({ id, ...copy.value.steps[id], icon: stepIcons[id] })))
const themeIcon = computed(() => ({ auto: MonitorIcon, light: SunIcon, dark: MoonIcon })[themeMode.value])
const themeLabel = computed(() => ({
  auto: copy.value.nav.themeSystem,
  light: copy.value.nav.themeLight,
  dark: copy.value.nav.themeDark,
})[themeMode.value])
const missingSteps = computed(() => steps.value.filter((step) => step.id !== "review" && !isStepValid(step.id)))
const pendingActivityFields = computed(() => (Object.keys(pendingActivity) as ActivityField[])
  .filter((field) => pendingActivity[field].trim().length > 0))
const changedSteps = computed(() => new Set(STEP_ORDER.filter((id): id is EditableStepId => id !== "review")
  .filter((id) => stepFingerprint(draft, id) !== stepFingerprint(savedDraft.value, id)
    || (id === "activity" && pendingActivityFields.value.length > 0))))
const nextMissingStep = computed(() => missingSteps.value[0] ?? null)
const activeHeading = computed(() => {
  const content = copy.value
  switch (activeStep.value) {
    case "wallpaper": return { title: content.wallpaper.title, description: content.wallpaper.description }
    case "weather": return { title: content.weather.title, description: content.weather.description }
    case "scenes": return { title: content.scenes.title, description: content.scenes.description }
    case "scheduling": return { title: content.preferences.title, description: content.preferences.description }
    case "activity": return { title: content.activity.title, description: content.activity.description }
    case "review": return {
      title: mode.value === "setup" ? content.nav.reviewSetup : content.nav.reviewSettings,
      description: content.review.description,
    }
  }
})
const evaluation = computed(() => evaluateSteps(draft, scan.ready.value, scan.usablePlaylists.value))
const allValid = computed(() => Object.values(evaluation.value.validity).every(Boolean))
const isDirty = computed(() => profileFingerprint(draft) !== baseline.value || pendingActivityFields.value.length > 0)
const stepErrorText = computed(() => stepError.value ? copy.value.errors[stepError.value] : "")
const submissionError = computed(() => submissionFailure.value ? describeError(submissionFailure.value) : "")
const catalogError = computed(() => catalogFailure.value ? describeError(catalogFailure.value) : "")
const scanDetail = computed(() => scan.error.value ? describeScanError(scan.error.value) : "")
// 表单页限宽到 760px，宽步骤（WIDE_STEPS）允许更宽；左对齐基线，右边界随内容收束。
const stepContentClass = computed(() => WIDE_STEPS.has(activeStep.value) ? "max-w-4xl" : "max-w-[47.5rem]")

const issuesByStep = computed<Record<StepId, Record<string, string[]>>>(() => {
  const grouped = Object.fromEntries(STEP_ORDER.map((id) => [id, {}])) as Record<StepId, Record<string, string[]>>
  for (const issue of validationIssues.value) {
    const fields = grouped[stepForIssue(issue.path)]
    const field = validationIssueField(issue.path)
    fields[field] ??= []
    fields[field].push(copy.value.errors.issueCodes[issue.code as keyof typeof copy.value.errors.issueCodes] ?? issue.message)
  }
  return grouped
})

function isStepValid(id: StepId): boolean {
  return id === "review" ? allValid.value : evaluation.value.validity[id]
}

function stepStatus(id: StepId): string {
  if (id === "review") return ""
  if (mode.value === "settings") return changedSteps.value.has(id) ? copy.value.nav.changed : ""
  if (!isStepValid(id)) return copy.value.nav.pending
  if ((id === "scheduling" || id === "activity") && !changedSteps.value.has(id)) return copy.value.nav.defaultReady
  return copy.value.nav.complete
}

function clearStepFeedback(id: StepId): void {
  validationIssues.value = validationIssues.value.filter((issue) => stepForIssue(issue.path) !== id)
  if (activeStep.value === id) stepError.value = null
  submissionFailure.value = null
}

function clearWeatherFieldFeedback(field: "api_key" | "location"): void {
  validationIssues.value = validationIssues.value.filter((issue) =>
    !(issue.path[0] === "weather" && issue.path[1] === field))
  if (activeStep.value === "weather" && isStepValid("weather") &&
    !validationIssues.value.some((issue) => stepForIssue(issue.path) === "weather")) {
    stepError.value = null
  }
  submissionFailure.value = null
}

function setTheme(value: unknown): void {
  if (value === "auto" || value === "light" || value === "dark") themeMode.value = value
}

function updatePath(value: string): void {
  draft.wallpaper_engine_path = value
  clearStepFeedback("wallpaper")
}

function updateApiKey(value: string): void {
  draft.weather.api_key = value
  weatherFailureKind.value = null
  weatherValidationError.value = ""
  weatherValidationFailure.value = null
  if (value.trim() !== verifiedWeatherKey.value) weatherTestedAt.value = null
  clearWeatherFieldFeedback("api_key")
}

function updateLocation(value: ProfileDraft["weather"]["location"]): void {
  draft.weather.location = value
  locationDetectionStatus.value = "idle"
  locationDetectionError.value = ""
  locationDetectionCity.value = null
  clearWeatherFieldFeedback("location")
}

function updateScenes(value: ProfileDraft["scenes"]): void {
  draft.scenes = value
  clearStepFeedback("scenes")
}

function updateMatching(value: ProfileDraft["matching"]): void {
  draft.matching = value
  clearStepFeedback("scheduling")
}

function updateDisturbance(value: ProfileDraft["disturbance"]): void {
  draft.disturbance = value
  clearStepFeedback("scheduling")
}

function updateActivity(value: ProfileDraft["activity"]): void {
  draft.activity = value
  const keepPendingWarning = stepError.value === "pendingActivity" && pendingActivityFields.value.length > 0
  clearStepFeedback("activity")
  if (keepPendingWarning) stepError.value = "pendingActivity"
}

function updatePendingActivity(field: ActivityField, value: string): void {
  pendingActivity[field] = value
  if (stepError.value === "pendingActivity" && pendingActivityFields.value.length === 0) stepError.value = null
}

function rememberScene(id: keyof ProfileDraft["scenes"], playlist: string): void {
  rememberedScenes[id] = playlist
}

watch(locale, (value, previous) => {
  if (previous !== undefined) draft.language = value
  document.documentElement.lang = value === "zh" ? "zh-CN" : "en"
  document.title = value === "zh" ? "Tunalo 设置" : "Tunalo Settings"
}, { immediate: true })

function handleBeforeUnload(event: BeforeUnloadEvent): void {
  if (!isDirty.value) return
  event.preventDefault()
}

function updateNativeBridgeAvailability(): void {
  hasNativeBridge.value = Boolean(window.pywebview?.api)
  if (window.pywebview?.api) void window.pywebview.api.page_ready()
}

onMounted(() => {
  window.addEventListener("beforeunload", handleBeforeUnload)
  window.addEventListener("pywebviewready", updateNativeBridgeAvailability)
  // ui/webview.py 用同名事件把被守卫拦截的原生 × / Alt+F4 转发给页面。
  window.addEventListener("tunalo:native-close-request", requestClose)
  updateNativeBridgeAvailability()
  void loadSceneCatalog()
  void scan.scan()
})

onBeforeUnmount(() => {
  window.removeEventListener("beforeunload", handleBeforeUnload)
  window.removeEventListener("pywebviewready", updateNativeBridgeAvailability)
  window.removeEventListener("tunalo:native-close-request", requestClose)
})

async function loadSceneCatalog(): Promise<void> {
  catalogFailure.value = null
  try {
    sceneCatalog.value = await getSceneCatalog()
  } catch (error) {
    catalogFailure.value = error
  }
}

async function scanWallpaper(): Promise<void> {
  clearStepFeedback("wallpaper")
  await scan.scan()
}

async function chooseWallpaperEngine(): Promise<void> {
  if (!window.pywebview?.api) return
  const path = await window.pywebview.api.choose_wallpaper_engine()
  if (!path) return
  updatePath(path)
  await scan.scan()
}

async function openExternal(url: string): Promise<void> {
  if (window.pywebview?.api) {
    await window.pywebview.api.open_external(url)
    return
  }
  window.open(url, "_blank", "noopener,noreferrer")
}

function describeScanError(error: unknown): string {
  if (!(error instanceof ApiError)) return copy.value.errors.generic
  const messages = copy.value.errors.scanCodes as Record<string, string>
  return messages[error.payload.error] ?? error.message
}

function describeError(error: unknown): string {
  if (!(error instanceof ApiError)) return copy.value.errors.generic
  if (error.payload.error === "profile_already_exists") return copy.value.errors.profileAlreadyExists
  if (error.payload.error === "profile_apply_timeout") return copy.value.errors.applyTimeout
  if (error.payload.error === "profile_apply_unavailable") return copy.value.errors.applyUnavailable
  if (error.payload.error === "weather_validation_unavailable") {
    return `${copy.value.errors.weatherValidationUnavailable} ${describeNetworkFailure(error)}`.trim()
  }
  if (error.payload.stage) {
    const stage = copy.value.errors.stages[error.payload.stage]
    return `${stage}: ${error.payload.detail || error.payload.error}`
  }
  return error.message || copy.value.errors.generic
}

function describeNetworkFailure(error: ApiError): string {
  const { reason, http_status: status } = error.payload
  if (reason === "http_status" && status !== undefined) {
    if (status === 429) return copy.value.errors.httpRateLimited
    if (status === 403) return copy.value.errors.httpForbidden
    if (status >= 500) return copy.value.errors.httpServerError
    return copy.value.errors.httpOther(status)
  }
  const messages = copy.value.errors.networkReasons as Record<string, string>
  return reason ? (messages[reason] ?? "") : ""
}

function describeWeatherTestError(error: unknown): string {
  if (!(error instanceof ApiError)) return copy.value.errors.generic
  const issue = error.payload.issues?.[0]
  if (issue) {
    const messages = copy.value.errors.issueCodes as Record<string, string>
    return messages[issue.code] ?? copy.value.errors.generic
  }
  if (error.payload.error === "weather_validation_unavailable") {
    return `${copy.value.errors.weatherValidationUnavailable} ${describeNetworkFailure(error)}`.trim()
  }
  return copy.value.errors.generic
}

function isSoftWeatherFailure(error: unknown): boolean {
  return error instanceof ApiError && (
    error.payload.error === "weather_validation_unavailable"
    || error.payload.issues?.some((issue) => issue.code === "weather_api_quota_exceeded") === true
  )
}

async function testWeatherKey(): Promise<void> {
  const apiKey = draft.weather.api_key.trim()
  if (!apiKey) {
    weatherValidationError.value = copy.value.weather.validationMissing
    return
  }
  validatingWeather.value = true
  weatherValidationError.value = ""
  weatherValidationFailure.value = null
  weatherFailureKind.value = null
  try {
    await validateWeatherKey(apiKey)
    if (draft.weather.api_key.trim() === apiKey) {
      verifiedWeatherKey.value = apiKey
      weatherTestedAt.value = Date.now()
    }
  } catch (error) {
    if (draft.weather.api_key.trim() === apiKey) {
      const issueCodes = error instanceof ApiError
        ? (error.payload.issues ?? []).map((issue) => issue.code)
        : []
      if (issueCodes.includes("weather_api_key_invalid")) {
        weatherFailureKind.value = "invalid"
        verifiedWeatherKey.value = null
      } else if (issueCodes.includes("weather_api_quota_exceeded")) {
        weatherFailureKind.value = "quota"
      } else {
        weatherFailureKind.value = "connection"
      }
      weatherValidationFailure.value = error
      if (verifiedWeatherKey.value !== apiKey) weatherTestedAt.value = Date.now()
    }
  } finally {
    validatingWeather.value = false
  }
}

const weatherKeyState = computed<"untested" | "valid" | "invalid" | "quota">(() => {
  if (weatherFailureKind.value === "invalid") return "invalid"
  if (weatherFailureKind.value === "quota") return "quota"
  if (verifiedWeatherKey.value !== null && draft.weather.api_key.trim() === verifiedWeatherKey.value) return "valid"
  return "untested"
})

const weatherConnectionError = computed(() => {
  if (weatherFailureKind.value !== "connection") return ""
  const error = weatherValidationFailure.value
  const reason = error instanceof ApiError && error.payload.error === "weather_validation_unavailable"
    ? describeNetworkFailure(error)
    : ""
  return copy.value.weather.connectionFailed(reason || copy.value.errors.generic)
})

const weatherTestedAtText = computed(() => weatherTestedAt.value === null ? "" :
  copy.value.weather.testedAt(new Date(weatherTestedAt.value).toLocaleString(locale.value === "zh" ? "zh-CN" : "en-US")))

function applyValidationIssues(error: unknown): boolean {
  if (!(error instanceof ApiError) || !error.payload.issues?.length) return false
  validationIssues.value = error.payload.issues
  const target = Math.min(...error.payload.issues.map((issue) => STEP_ORDER.indexOf(stepForIssue(issue.path))))
  currentIndex.value = target
  if (error.payload.issues.some((issue) => issue.path[0] === "disturbance")) timingOpen.value = true
  stepError.value = "fieldValidation"
  submissionFailure.value = null
  void focusStep(true)
  return true
}

async function detectCity(): Promise<void> {
  locating.value = true
  locationDetectionStatus.value = "idle"
  locationDetectionError.value = ""
  locationDetectionCity.value = null
  try {
    const detected = await detectLocation()
    updateLocation({ latitude: detected.latitude, longitude: detected.longitude })
    locationDetectionCity.value = detected.city ?? null
    locationDetectionStatus.value = "success"
  } catch (error) {
    locationDetectionStatus.value = "error"
    const detail = error instanceof ApiError ? describeNetworkFailure(error) : ""
    locationDetectionError.value = `${copy.value.errors.locationValidationUnavailable} ${detail}`.trim()
  } finally {
    locating.value = false
  }
}

function navigateTo(index: number): void {
  if (activeStep.value !== "review" && index === STEP_ORDER.length - 1) previousSectionIndex.value = currentIndex.value
  currentIndex.value = index
  stepError.value = null
  submissionFailure.value = null
  void focusStep(false)
}

function navigateToStep(id: StepId): void {
  const needsAttention = activeStep.value === "review" && !isStepValid(id)
  navigateTo(STEP_ORDER.indexOf(id))
  if (needsAttention) stepError.value = "validation"
  if (needsAttention) void focusStep(true)
}

async function focusStep(errorFirst: boolean): Promise<void> {
  await nextTick()
  const target = errorFirst
    ? [...document.querySelectorAll<HTMLElement>("#setup-step-content [aria-invalid='true']")]
      .find((element) => element.getClientRects().length > 0)
    : null
  ;(target ?? document.getElementById("setup-step-heading"))?.focus()
}

function setLocale(value: unknown): void {
  if (value === "zh" || value === "en") locale.value = value
}

function requestClose(): void {
  if (isDirty.value) {
    closeDialogOpen.value = true
    return
  }
  void closeWindow()
}

async function closeWindow(): Promise<void> {
  if (window.pywebview?.api) await window.pywebview.api.close()
}

async function submitProfile(allowUnverifiedWeather = false): Promise<void> {
  if (submitting.value || locating.value) return
  if (pendingActivityFields.value.length > 0) {
    navigateToStep("activity")
    stepError.value = "pendingActivity"
    void focusStep(true)
    return
  }
  if (!allValid.value) {
    const invalidIndex = STEP_ORDER.findIndex((id) => !isStepValid(id))
    currentIndex.value = Math.max(0, invalidIndex)
    stepError.value = "validation"
    void focusStep(true)
    return
  }
  if (mode.value === "settings" && !isDirty.value) return

  const hasVerifiedKey = verifiedWeatherKey.value === draft.weather.api_key.trim()
  if (!allowUnverifiedWeather && !hasVerifiedKey && isSoftWeatherFailure(weatherValidationFailure.value)) {
    weatherSaveFailure.value = describeWeatherTestError(weatherValidationFailure.value)
    weatherSaveDialogOpen.value = true
    return
  }

  submitting.value = true
  submissionFailure.value = null
  try {
    const profile = buildProfile(draft)
    const skipWeatherValidation = allowUnverifiedWeather || hasVerifiedKey
    const committed = mode.value === "setup"
      ? await createInitialProfile(profile, skipWeatherValidation)
      : await applyProfile(profile, skipWeatherValidation)
    Object.assign(draft, createProfileDraft(committed, locale.value))
    savedDraft.value = createProfileDraft(committed, locale.value)
    baseline.value = profileFingerprint(draft)
    for (const id of Object.keys(rememberedScenes) as Array<keyof ProfileDraft["scenes"]>) delete rememberedScenes[id]
    validationIssues.value = []
    stepError.value = null
    weatherValidationFailure.value = null
    weatherSaveFailure.value = ""
    if (mode.value === "setup") {
      toast.success(copy.value.review.setupSuccess)
      await closeWindow()
    } else {
      toast.success(copy.value.review.success)
    }
  } catch (error) {
    if (isSoftWeatherFailure(error) && !allowUnverifiedWeather) {
      weatherSaveFailure.value = describeWeatherTestError(error)
      weatherSaveDialogOpen.value = true
    } else if (!applyValidationIssues(error)) submissionFailure.value = error
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="min-h-[100dvh] bg-muted/40 p-4 text-foreground md:h-[100dvh] md:overflow-hidden">
    <div class="mx-auto grid w-full max-w-[100rem] gap-4 md:h-full md:min-h-0 md:grid-cols-[14rem_minmax(0,1fr)]">
      <aside class="flex min-w-0 flex-col gap-4 rounded-xl bg-sidebar p-4 text-sidebar-foreground ring-1 ring-sidebar-border md:h-full md:min-h-0 md:overflow-hidden">
        <header class="flex items-center gap-2.5 px-1">
          <TunaloMark class="size-7 shrink-0 text-foreground" />
          <div class="flex min-w-0 flex-col">
            <p class="text-lg leading-7 font-semibold tracking-tight">{{ copy.appName }}</p>
            <p class="text-sm leading-5 text-muted-foreground">{{ copy.mode[mode] }}</p>
          </div>
        </header>

        <nav :inert="submitting" class="flex gap-1 overflow-x-auto pb-1 md:min-h-0 md:flex-1 md:flex-col md:overflow-y-auto" :aria-label="mode === 'setup' ? copy.nav.setupNavigation : copy.nav.settingsNavigation">
          <p class="hidden px-3 pb-1 text-xs font-medium text-muted-foreground md:block">{{ mode === 'setup' ? copy.nav.setupNavigation : copy.nav.settingsNavigation }}</p>
          <Button
            v-for="(step, index) in steps"
            :key="step.id"
            type="button"
            variant="ghost"
            :aria-current="currentIndex === index ? 'page' : undefined"
            :class="[cn('min-w-44 justify-start border-l-2 px-3 text-left md:min-w-0',
              currentIndex === index
                ? 'border-l-foreground bg-background font-semibold shadow-xs ring-1 ring-sidebar-border'
                : 'border-l-transparent hover:bg-sidebar-accent')]"
            @click="navigateTo(index)"
          >
            <component :is="step.icon" data-icon="inline-start" />
            <span class="min-w-0 flex-1 truncate font-medium">{{ step.id === 'review' ? (mode === 'setup' ? copy.nav.reviewSetup : copy.nav.reviewSettings) : step.title }}</span>
            <span v-if="stepStatus(step.id)" class="shrink-0 text-xs text-muted-foreground">{{ stepStatus(step.id) }}</span>
            <span
              v-if="step.id === nextMissingStep?.id"
              data-next-required="true"
              aria-hidden="true"
              class="size-1.5 shrink-0 rounded-full bg-foreground"
            />
          </Button>
        </nav>

        <p v-if="mode === 'settings'" class="text-sm text-muted-foreground" role="status">
          {{ isDirty ? copy.nav.unsaved : copy.nav.saved }}
        </p>

        <div :inert="submitting" class="mt-auto flex items-center justify-between border-t border-sidebar-border pt-3">
          <ToggleGroup type="single" size="sm" :spacing="1" class="shrink-0 rounded-md border border-sidebar-border bg-muted/40 p-0.5" :model-value="locale" :aria-label="copy.nav.languageLabel" @update:model-value="setLocale">
            <ToggleGroupItem value="zh" class="rounded-sm data-[state=on]:bg-background" aria-label="中文">中</ToggleGroupItem>
            <ToggleGroupItem value="en" class="rounded-sm data-[state=on]:bg-background" aria-label="English">EN</ToggleGroupItem>
          </ToggleGroup>
          <Select :model-value="themeMode" @update:model-value="setTheme">
            <SelectTrigger class="size-9 justify-center gap-0 rounded-md border border-sidebar-border bg-transparent p-0 hover:bg-sidebar-accent [&_svg:last-child]:hidden" :aria-label="`${copy.nav.themeLabel}: ${themeLabel}`" :title="`${copy.nav.themeLabel}: ${themeLabel}`">
              <component :is="themeIcon" class="size-4" />
            </SelectTrigger>
            <SelectContent position="popper" align="end">
              <SelectGroup>
                <SelectItem value="auto">{{ copy.nav.themeSystem }}</SelectItem>
                <SelectItem value="light">{{ copy.nav.themeLight }}</SelectItem>
                <SelectItem value="dark">{{ copy.nav.themeDark }}</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      </aside>

      <Card class="min-w-0 min-h-[32rem] md:h-full md:min-h-0 [--card-spacing:--spacing(7)]">
        <CardHeader class="shrink-0">
          <CardTitle><h1 id="setup-step-heading" tabindex="-1" class="text-2xl leading-8 font-semibold tracking-tight focus:outline-none">{{ activeHeading.title }}</h1></CardTitle>
          <CardDescription v-if="activeHeading.description">{{ activeHeading.description }}</CardDescription>
        </CardHeader>
        <CardContent id="setup-step-content" :inert="submitting" :aria-busy="submitting" class="min-h-0 flex-1 overflow-y-auto pt-0 pb-6">
          <div class="flex w-full flex-col" :class="stepContentClass">
          <Alert v-if="stepErrorText" variant="destructive" class="mb-6">
            <TriangleAlertIcon />
            <AlertTitle>{{ copy.common.needsAttention }}</AlertTitle>
            <AlertDescription>{{ stepErrorText }}</AlertDescription>
          </Alert>
          <Alert v-if="submissionError" variant="destructive" class="mb-6">
            <TriangleAlertIcon />
            <AlertTitle>{{ copy.errors.generic }}</AlertTitle>
            <AlertDescription>{{ submissionError }}</AlertDescription>
          </Alert>

          <WallpaperStep
            v-if="activeStep === 'wallpaper'"
            :locale="locale"
            :path="draft.wallpaper_engine_path"
            :status="scan.status.value"
            :detail="scanDetail"
            :playlists="scan.playlists.value"
            :usable-count="scan.usablePlaylists.value.length"
            :native-bridge="hasNativeBridge"
            :invalid="Boolean(stepError) && !isStepValid('wallpaper')"
            :errors="issuesByStep.wallpaper.wallpaper_engine_path ?? []"
            @update:path="updatePath"
            @scan="scanWallpaper"
            @choose="chooseWallpaperEngine"
          />
          <div v-else-if="activeStep === 'weather'" class="flex flex-col gap-8">
            <WeatherKeyStep
              :locale="locale"
              :api-key="draft.weather.api_key"
              :invalid="Boolean(stepError) && !draft.weather.api_key.trim()"
              :errors="issuesByStep.weather['weather.api_key'] ?? []"
              :validating="validatingWeather"
              :key-state="weatherKeyState"
              :tested-at-text="weatherTestedAtText"
              :connection-error="weatherConnectionError"
              :validation-error="weatherValidationError"
              @update:api-key="updateApiKey"
              @validate="testWeatherKey"
              @open-key-page="openExternal('https://home.openweathermap.org/api_keys')"
            />
            <section class="flex flex-col gap-4 border-t pt-6" :aria-label="copy.location.title">
              <div>
                <h2 class="text-base font-semibold">{{ copy.location.title }}</h2>
                <p class="text-sm text-muted-foreground">{{ mode === 'setup' ? copy.location.setupDescription : copy.location.settingsDescription }}</p>
              </div>
              <LocationStep
                :locale="locale"
                :location="draft.weather.location"
                :locating="locating"
                :detection-status="locationDetectionStatus"
                :detection-error="locationDetectionError"
                :detection-city="locationDetectionCity"
                :attempted="Boolean(stepError)"
                :errors="issuesByStep.weather"
                @update:location="updateLocation"
                @detect="detectCity"
                @open-map="openExternal('https://www.openstreetmap.org')"
              />
            </section>
          </div>
          <SceneBindingsStep
            v-else-if="activeStep === 'scenes'"
            :locale="locale"
            :mode="mode"
            :scenes="draft.scenes"
            :remembered-scenes="rememberedScenes"
            :catalog="sceneCatalog"
            :playlists="scan.usablePlaylists.value"
            :catalog-error="catalogError"
            :valid="isStepValid('scenes')"
            :attempted="Boolean(stepError)"
            :errors="issuesByStep.scenes.scenes ?? []"
            @update:scenes="updateScenes"
            @remember-scene="rememberScene"
            @retry-catalog="loadSceneCatalog"
            @open-wallpaper="navigateToStep('wallpaper')"
          />
          <SchedulingStep
            v-else-if="activeStep === 'scheduling'"
            :locale="locale"
            :matching="draft.matching"
            :disturbance="draft.disturbance"
            :timing-open="timingOpen"
            :errors="issuesByStep.scheduling"
            @update:matching="updateMatching"
            @update:disturbance="updateDisturbance"
            @update:timing-open="timingOpen = $event"
          />
          <ActivityRulesStep
            v-else-if="activeStep === 'activity'"
            :locale="locale"
            :activity="draft.activity"
            :pending="pendingActivity"
            :show-pending="stepError === 'pendingActivity'"
            :conflicts="evaluation.conflicts"
            :errors="issuesByStep.activity.activity ?? []"
            @update:activity="updateActivity"
            @update:pending="updatePendingActivity"
          />
          <ReviewStep
            v-else
            :locale="locale"
            :draft="draft"
            :saved-draft="savedDraft"
            :mode="mode"
            :valid="allValid"
            :missing-steps="missingSteps"
            :weather-key-state="weatherKeyState"
            :weather-tested-at-text="weatherTestedAtText"
            :weather-connection-error="weatherConnectionError"
            :validating-weather="validatingWeather"
            @validate-weather="testWeatherKey"
            @open-step="navigateToStep"
          />
          </div>
        </CardContent>

        <Separator />
        <CardFooter class="shrink-0 justify-between gap-3">
          <Button v-if="activeStep === 'review'" variant="outline" :disabled="submitting" @click="navigateTo(previousSectionIndex)">{{ copy.nav.backToSettings }}</Button>
          <Button v-else variant="ghost" :disabled="submitting" @click="requestClose">{{ mode === 'setup' ? copy.common.cancel : copy.common.close }}</Button>

          <Button v-if="activeStep !== 'review'" :variant="mode === 'settings' ? 'outline' : 'default'" :disabled="submitting" @click="navigateToStep('review')">
            {{ mode === 'setup' ? copy.nav.reviewSetup : copy.nav.reviewSettings }}
            <ChevronRightIcon data-icon="inline-end" />
          </Button>
          <Button v-if="mode === 'settings' || activeStep === 'review'" :disabled="submitting || locating || !allValid || (mode === 'settings' && !isDirty)" @click="submitProfile()">
            <Spinner v-if="submitting" data-icon="inline-start" />
            <CheckIcon v-else data-icon="inline-start" />
            {{ submitting
              ? (mode === "setup" ? copy.review.creating : copy.review.saving)
              : (mode === "setup" ? copy.review.create : copy.review.save) }}
          </Button>
        </CardFooter>
      </Card>
    </div>

    <AlertDialog v-model:open="closeDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{{ copy.nav.discardTitle }}</AlertDialogTitle>
          <AlertDialogDescription>{{ mode === "setup" ? copy.nav.discardSetupDescription : copy.nav.discardSettingsDescription }}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{{ copy.nav.keepEditing }}</AlertDialogCancel>
          <AlertDialogAction @click="closeWindow">{{ copy.nav.discardChanges }}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <AlertDialog v-model:open="weatherSaveDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{{ locale === "zh" ? ZH_WEATHER_SAVE_PROMPT.title : copy.errors.weatherValidationUnavailable }}</AlertDialogTitle>
          <AlertDialogDescription>
            {{ weatherSaveFailure }}
            <template v-if="locale === 'zh'">{{ ZH_WEATHER_SAVE_PROMPT.description }}</template>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{{ copy.common.back }}</AlertDialogCancel>
          <AlertDialogAction :disabled="submitting" @click="submitProfile(true)">{{ mode === "setup" ? copy.review.create : copy.review.save }}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </main>
</template>
