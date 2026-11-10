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
import WeatherConnectionStep from "./WeatherConnectionStep.vue"

const { locale, draft, savedDraft } = useSetupEditor()
const { stepError, issuesByStep } = useSetupFlowContext()
const { openExternal } = useSetupNativeWindow()
const {
  validatingWeather,
  weatherConnectionState,
  canTestWeather,
  weatherTestedAtText,
  weatherConnectionError,
  weatherValidationError,
  locating,
  locationDetectionStatus,
  locationDetectionError,
  locationDetectionCity,
  updateLocation,
  testWeatherConnection,
  detectCity,
} = useSetupWeather()
const copy = computed(() => COPY[locale.value])
const locationEdited = computed(
  () => JSON.stringify(draft.weather.location) !== JSON.stringify(savedDraft.value.weather.location),
)
</script>

<template>
  <div class="flex flex-col gap-10">
    <section class="flex flex-col gap-5" :aria-label="copy.location.title">
      <h2 class="text-lg font-semibold">{{ copy.location.title }}</h2>
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
    <WeatherConnectionStep
      :locale="locale"
      :can-test="canTestWeather"
      :validating="validatingWeather"
      :state="weatherConnectionState"
      :tested-at-text="weatherTestedAtText"
      :connection-error="weatherConnectionError"
      :validation-error="weatherValidationError"
      @validate="testWeatherConnection"
      @open-provider="openExternal('https://open-meteo.com/')"
    />
  </div>
</template>
