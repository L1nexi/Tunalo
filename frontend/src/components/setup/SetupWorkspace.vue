<script setup lang="ts">
import { CheckIcon, ChevronRightIcon, TriangleAlertIcon } from "@lucide/vue"
import { computed, onMounted, ref, shallowRef, toRef } from "vue"

import type { Locale, Profile, SceneCatalogItem } from "@/api/profile"
import { getSceneCatalog } from "@/api/profile"
import SetupSidebar from "@/components/setup/SetupSidebar.vue"
import ActivityRulesStep from "@/components/setup/steps/ActivityRulesStep.vue"
import LocationStep from "@/components/setup/steps/LocationStep.vue"
import ReviewStep from "@/components/setup/steps/ReviewStep.vue"
import SceneBindingsStep from "@/components/setup/steps/SceneBindingsStep.vue"
import SchedulingStep from "@/components/setup/steps/SchedulingStep.vue"
import WallpaperStep from "@/components/setup/steps/WallpaperStep.vue"
import WeatherKeyStep from "@/components/setup/steps/WeatherKeyStep.vue"
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Spinner } from "@/components/ui/spinner"
import { COPY, ZH_WEATHER_SAVE_PROMPT } from "@/setup/copy"
import { describeError, describeScanError } from "@/setup/errorMessages"
import { usePlaylistScan } from "@/setup/usePlaylistScan"
import { useProfileDraft } from "@/setup/useProfileDraft"
import { useProfileSubmission } from "@/setup/useProfileSubmission"
import { useSetupFlow } from "@/setup/useSetupFlow"
import { useSetupWindow } from "@/setup/useSetupWindow"
import { useWeatherServices } from "@/setup/useWeatherServices"

const props = defineProps<{
  initialProfile: Profile | null
  initialLocale: Locale
}>()

const editor = useProfileDraft(props.initialProfile, props.initialLocale)
const { mode, locale, draft, savedDraft, isDirty, pendingActivity, pendingActivityFields, rememberedScenes, rememberScene, setLocale } = editor
const copy = computed(() => COPY[locale.value])
const scan = usePlaylistScan(toRef(draft, "wallpaper_engine_path"))
const flow = useSetupFlow(editor, scan)
const {
  activeStep, previousSection, steps, activeHeading, stepContentClass,
  allValid, missingSteps, evaluation, stepError, stepErrorText, submissionError, issuesByStep, timingOpen,
  isStepValid, navigateTo, navigateToStep,
  updatePath, updateScenes, updateMatching, updateDisturbance, updateActivity, updatePendingActivity,
} = flow
const weather = useWeatherServices(toRef(draft, "weather"), locale, flow.clearWeatherFieldFeedback)
const {
  validatingWeather, weatherKeyState, weatherTestedAtText, weatherConnectionError, weatherValidationError,
  locating, locationDetectionStatus, locationDetectionError, locationDetectionCity,
  weatherSaveDialogOpen, weatherSaveFailure, updateApiKey, updateLocation, testWeatherKey, detectCity,
} = weather
const nativeWindow = useSetupWindow(isDirty)
const { hasNativeBridge, closeDialogOpen, requestClose, closeWindow, openExternal } = nativeWindow
const { submitting, submitProfile } = useProfileSubmission(editor, flow, weather, closeWindow)

const sceneCatalog = ref<SceneCatalogItem[]>([])
const catalogFailure = shallowRef<unknown>(null)
const catalogError = computed(() => catalogFailure.value ? describeError(catalogFailure.value, locale.value) : "")
const scanDetail = computed(() => scan.error.value ? describeScanError(scan.error.value, locale.value) : "")

async function loadSceneCatalog(): Promise<void> {
  catalogFailure.value = null
  try {
    sceneCatalog.value = await getSceneCatalog()
  } catch (error) {
    catalogFailure.value = error
  }
}

async function scanWallpaper(): Promise<void> {
  flow.clearStepFeedback("wallpaper")
  await scan.scan()
}

async function chooseWallpaperEngine(): Promise<void> {
  const path = await nativeWindow.chooseWallpaperEngine()
  if (!path) return
  updatePath(path)
  await scan.scan()
}

onMounted(() => {
  void loadSceneCatalog()
  void scan.scan().then(editor.acceptDetectedPath)
})
</script>

<template>
  <main class="min-h-[100dvh] bg-muted/40 p-4 text-foreground md:h-[100dvh] md:overflow-hidden">
    <div class="mx-auto grid w-full max-w-[100rem] gap-4 md:h-full md:min-h-0 md:grid-cols-[14rem_minmax(0,1fr)]">
      <SetupSidebar
        :locale="locale"
        :mode="mode"
        :steps="steps"
        :active-step="activeStep"
        :dirty="isDirty"
        :submitting="submitting"
        @navigate="navigateTo"
        @update:locale="setLocale"
      />

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
            :has-pending-activity="pendingActivityFields.length > 0"
            @validate-weather="testWeatherKey"
            @open-step="navigateToStep"
          />
          </div>
        </CardContent>

        <Separator />
        <CardFooter class="shrink-0 justify-between gap-3">
          <Button v-if="activeStep === 'review'" variant="outline" :disabled="submitting" @click="navigateTo(previousSection)">{{ copy.nav.backToSettings }}</Button>
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
