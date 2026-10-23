<script setup lang="ts">
import { TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { COPY } from "@/setup/copy"
import {
  useSetupEditor,
  useSetupFlowContext,
  useSetupNativeWindow,
  useSetupScan,
  useSetupWeather,
} from "@/setup/useSetupWorkspace"
import SetupWeatherContent from "./SetupWeatherContent.vue"
import ActivityRulesStep from "./steps/ActivityRulesStep.vue"
import SceneBindingsStep from "./steps/SceneBindingsStep.vue"
import SchedulingStep from "./steps/SchedulingStep.vue"
import WallpaperStep from "./steps/WallpaperStep.vue"
import ReviewStep from "./steps/ReviewStep.vue"

const { locale, draft, savedDraft, mode, pendingActivity, pendingActivityFields, preferenceLayers } =
  useSetupEditor()
const {
  activeStep,
  stepContentClass,
  evaluation,
  allValid,
  missingSteps,
  stepError,
  stepErrorText,
  submissionError,
  issuesByStep,
  timingOpen,
  isStepValid,
  navigateToStep,
  updatePath,
  updateScenes,
  removeScene,
  updatePreferenceLayers,
  addPreferenceLayer,
  updateDisturbance,
  updateActivity,
  updatePendingActivity,
} = useSetupFlowContext()
const scan = useSetupScan()
const { hasNativeBridge } = useSetupNativeWindow()
const { weatherKeyState, weatherTestedAtText, weatherConnectionError, validatingWeather, testWeatherKey } =
  useSetupWeather()
const copy = computed(() => COPY[locale.value])
</script>

<template>
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
      :detail="scan.detail.value"
      :playlists="scan.playlists.value"
      :usable-count="scan.usablePlaylists.value.length"
      :native-bridge="hasNativeBridge"
      :invalid="Boolean(stepError) && !isStepValid('wallpaper')"
      :errors="issuesByStep.wallpaper.wallpaper_engine_path ?? []"
      @update:path="updatePath"
      @scan="scan.rescan"
      @choose="scan.chooseWallpaperEngine"
    />
    <SetupWeatherContent v-else-if="activeStep === 'weather'" />
    <SceneBindingsStep
      v-else-if="activeStep === 'scenes'"
      :locale="locale"
      :scenes="draft.scenes"
      :playlists="scan.usablePlaylists.value"
      :valid="isStepValid('scenes')"
      :attempted="Boolean(stepError)"
      :errors="issuesByStep.scenes.scenes ?? []"
      @update:scenes="updateScenes"
      @remove-scene="removeScene"
      @open-wallpaper="navigateToStep('wallpaper')"
    />
    <SchedulingStep
      v-else-if="activeStep === 'scheduling'"
      :locale="locale"
      :layers="preferenceLayers"
      :disturbance="draft.disturbance"
      :timing-open="timingOpen"
      :errors="issuesByStep.scheduling"
      @update:layers="updatePreferenceLayers"
      @add-layer="addPreferenceLayer"
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
</template>
