<script setup lang="ts">
import { CheckCircle2Icon, CircleDashedIcon, CircleXIcon, TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale } from "@/api/profile"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { COPY } from "@/setup/copy"
import type { ReviewWeatherState } from "@/setup/review/summary"

const props = defineProps<{
  locale: Locale
  canTest: boolean
  validating: boolean
  state: ReviewWeatherState
  testedAtText: string
  connectionError: string
  validationError: string
}>()

const emit = defineEmits<{ validate: []; openProvider: [] }>()
const copy = computed(() => COPY[props.locale])
const stateText = computed(() => {
  if (props.state === "valid") return copy.value.weather.connectionValid
  if (props.state === "invalid") return copy.value.errors.issueCodes.weather_location_invalid
  if (props.state === "quota") return copy.value.errors.issueCodes.weather_api_quota_exceeded
  return copy.value.weather.connectionUntested
})
</script>

<template>
  <section class="flex flex-col gap-5" :aria-label="copy.weather.title">
    <h2 class="text-lg font-semibold">{{ copy.weather.title }}</h2>
    <Button variant="outline" class="self-start" :disabled="validating || !canTest" @click="emit('validate')">
      <Spinner v-if="validating" data-icon="inline-start" />
      {{ validating ? copy.weather.validating : copy.weather.validate }}
    </Button>

    <Alert v-if="validationError" variant="destructive">
      <TriangleAlertIcon />
      <AlertDescription>{{ validationError }}</AlertDescription>
    </Alert>

    <div v-if="state !== 'untested' || connectionError" class="flex flex-col gap-1.5" role="status">
      <p v-if="state === 'valid'" class="flex items-center gap-2 text-sm">
        <CheckCircle2Icon class="text-success" />
        <span>{{ stateText }}</span>
        <span v-if="testedAtText" class="text-muted-foreground">{{ testedAtText }}</span>
      </p>
      <p v-else-if="state === 'invalid'" class="flex items-center gap-2 text-sm text-destructive">
        <CircleXIcon />
        <span>{{ stateText }}</span>
      </p>
      <p v-else-if="state === 'quota'" class="flex items-center gap-2 text-sm text-warning">
        <TriangleAlertIcon />
        <span>{{ stateText }}</span>
      </p>
      <p v-else class="flex items-center gap-2 text-sm text-muted-foreground">
        <CircleDashedIcon />
        <span>{{ stateText }}</span>
      </p>
      <p v-if="connectionError" class="flex items-start gap-2 text-sm text-warning">
        <TriangleAlertIcon class="mt-0.5 shrink-0" />
        <span class="min-w-0">{{ connectionError }}</span>
      </p>
    </div>

    <Button variant="link" class="h-auto self-start p-0" @click="emit('openProvider')">
      {{ copy.weather.attribution }}
    </Button>
  </section>
</template>
