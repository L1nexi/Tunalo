<script setup lang="ts">
import { CheckCircle2Icon, CircleDashedIcon, CircleXIcon, GaugeIcon, TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale } from "@/api/profile"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { COPY } from "@/setup/copy"
import { reviewWeather } from "./summary"
import type { ReviewWeatherState } from "./summary"

const props = defineProps<{
  locale: Locale
  state: ReviewWeatherState
  testedAtText: string
  connectionError: string
  validating: boolean
  hasApiKey: boolean
}>()
const emit = defineEmits<{ validate: [] }>()
const copy = computed(() => COPY[props.locale])
const status = computed(
  () =>
    ({
      valid: { icon: CheckCircle2Icon, class: "text-success" },
      invalid: { icon: CircleXIcon, class: "text-destructive" },
      quota: { icon: TriangleAlertIcon, class: "text-warning" },
      untested: { icon: CircleDashedIcon, class: "text-muted-foreground" },
    })[props.state],
)
</script>

<template>
  <div class="flex min-w-0 flex-wrap items-start justify-between gap-3">
    <div class="min-w-0">
      <p class="flex items-center gap-2 text-sm font-medium" role="status">
        <component :is="status.icon" :class="status.class" />
        <span>{{ reviewWeather(state, locale) }}</span>
      </p>
      <p v-if="connectionError" class="mt-1 flex items-start gap-2 text-sm text-warning">
        <TriangleAlertIcon class="mt-0.5 shrink-0" />
        <span class="min-w-0">{{ connectionError }}</span>
      </p>
      <p v-if="copy.review.weatherNote" class="mt-1 text-xs text-muted-foreground">
        {{ copy.review.weatherNote }}
      </p>
      <p v-if="testedAtText" class="mt-1 text-xs text-muted-foreground">{{ testedAtText }}</p>
    </div>
    <Button size="sm" variant="outline" :disabled="validating || !hasApiKey" @click="emit('validate')">
      <Spinner v-if="validating" data-icon="inline-start" />
      <GaugeIcon v-else data-icon="inline-start" />
      {{ validating ? copy.weather.validating : copy.weather.validate }}
    </Button>
  </div>
</template>
