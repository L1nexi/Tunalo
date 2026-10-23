<script setup lang="ts">
import { computed } from "vue"

import { COPY } from "@/setup/copy"
import {
  useSetupEditor,
  useSetupFlowContext,
  useSetupNativeWindow,
  useSetupWeather,
} from "@/setup/workspace/useSetupWorkspace"
import LocationStep from "./LocationStep.vue"
import WeatherKeyStep from "./WeatherKeyStep.vue"

const { locale, mode, draft, savedDraft } = useSetupEditor()
const { stepError, issuesByStep } = useSetupFlowContext()
const { openExternal } = useSetupNativeWindow()
const {
  validatingWeather,
  weatherKeyState,
  weatherTestedAtText,
  weatherConnectionError,
  weatherValidationError,
  locating,
  locationDetectionStatus,
  locationDetectionError,
  locationDetectionCity,
  updateApiKey,
  updateLocation,
  testWeatherKey,
  detectCity,
} = useSetupWeather()
const copy = computed(() => COPY[locale.value])
const locationEdited = computed(
  () => JSON.stringify(draft.weather.location) !== JSON.stringify(savedDraft.value.weather.location),
)
</script>

<template>
  <div class="flex flex-col gap-8">
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
        <p class="text-sm text-muted-foreground">
          {{ mode === "setup" ? copy.location.setupDescription : copy.location.settingsDescription }}
        </p>
      </div>
      <LocationStep
        :locale="locale"
        :location="draft.weather.location"
        :locating="locating"
        :detection-status="locationDetectionStatus"
        :detection-error="locationDetectionError"
        :detection-city="locationDetectionCity"
        :attempted="Boolean(stepError)"
        :edited="locationEdited"
        :errors="issuesByStep.weather"
        @update:location="updateLocation"
        @detect="detectCity"
        @open-map="openExternal('https://www.openstreetmap.org')"
      />
    </section>
  </div>
</template>
