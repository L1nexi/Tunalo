<script setup lang="ts">
import { ExternalLinkIcon, MapPinIcon, MapPinSearchIcon, TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale } from "@/api/profile"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { COPY } from "@/setup/copy"
import type { ProfileDraft } from "@/setup/model"

type Location = ProfileDraft["weather"]["location"]
type Coordinate = "latitude" | "longitude"

const props = defineProps<{
  locale: Locale
  location: Location
  locating: boolean
  detectionStatus: "idle" | "success" | "error"
  detectionError: string
  detectionCity: string | null
  attempted: boolean
  errors: Record<string, string[]>
}>()

const emit = defineEmits<{
  "update:location": [value: Location]
  detect: []
  openMap: []
}>()

const copy = computed(() => COPY[props.locale])
const latitudeInvalid = computed(() =>
  props.location.latitude === null || !Number.isFinite(props.location.latitude) ||
  props.location.latitude < -90 || props.location.latitude > 90,
)
const longitudeInvalid = computed(() =>
  props.location.longitude === null || !Number.isFinite(props.location.longitude) ||
  props.location.longitude < -180 || props.location.longitude > 180,
)

function messages(...fields: string[]): string[] {
  return fields.flatMap((field) => props.errors[field] ?? [])
}

function coordinateErrors(field: Coordinate): string[] {
  const invalid = field === "latitude" ? latitudeInvalid.value : longitudeInvalid.value
  return [
    ...(props.attempted && invalid ? [field === "latitude" ? copy.value.location.invalidLatitude : copy.value.location.invalidLongitude] : []),
    ...messages("weather.location", `weather.location.${field}`),
  ]
}

function setCoordinate(field: Coordinate, value: string | number): void {
  const parsed = value === "" ? null : Number(value)
  emit("update:location", {
    ...props.location,
    [field]: parsed !== null && Number.isFinite(parsed) ? parsed : null,
  })
}
</script>

<template>
  <section class="flex flex-col gap-6">
    <div class="flex flex-col items-start gap-2">
      <Button variant="outline" :disabled="locating" @click="emit('detect')">
        <Spinner v-if="locating" data-icon="inline-start" />
        <MapPinSearchIcon v-else data-icon="inline-start" />
        {{ locating ? copy.location.detecting : copy.location.detect }}
      </Button>
      <p class="text-sm text-muted-foreground">{{ copy.location.detectHint }}</p>
      <p class="text-sm text-muted-foreground">{{ copy.location.manualHelp }}</p>
      <Button type="button" variant="link" class="h-auto px-0" @click="emit('openMap')">
        <ExternalLinkIcon data-icon="inline-start" />
        {{ copy.location.openMap }}
      </Button>
    </div>

    <Alert v-if="detectionStatus === 'success'">
      <MapPinIcon />
      <AlertDescription>{{ copy.location.detected(detectionCity) }}</AlertDescription>
    </Alert>
    <Alert v-else-if="detectionStatus === 'error'" variant="destructive">
      <TriangleAlertIcon />
      <AlertDescription>{{ detectionError }} {{ copy.location.detectionUnavailable }}</AlertDescription>
    </Alert>

    <FieldGroup>
      <div class="grid gap-5 sm:max-w-md sm:grid-cols-2">
        <Field :data-invalid="coordinateErrors('latitude').length > 0">
          <FieldLabel for="latitude">{{ copy.location.latitudeLabel }}</FieldLabel>
          <Input
            id="latitude"
            :model-value="location.latitude ?? ''"
            type="number"
            min="-90"
            max="90"
            step="0.0001"
            :placeholder="copy.location.latitudePlaceholder"
            :aria-invalid="coordinateErrors('latitude').length > 0"
            :aria-describedby="coordinateErrors('latitude').length ? 'latitude-error' : undefined"
            @update:model-value="(value: string | number) => setCoordinate('latitude', value)"
          />
          <FieldError v-if="coordinateErrors('latitude').length" id="latitude-error" :errors="coordinateErrors('latitude')" />
        </Field>
        <Field :data-invalid="coordinateErrors('longitude').length > 0">
          <FieldLabel for="longitude">{{ copy.location.longitudeLabel }}</FieldLabel>
          <Input
            id="longitude"
            :model-value="location.longitude ?? ''"
            type="number"
            min="-180"
            max="180"
            step="0.0001"
            :placeholder="copy.location.longitudePlaceholder"
            :aria-invalid="coordinateErrors('longitude').length > 0"
            :aria-describedby="coordinateErrors('longitude').length ? 'longitude-error' : undefined"
            @update:model-value="(value: string | number) => setCoordinate('longitude', value)"
          />
          <FieldError v-if="coordinateErrors('longitude').length" id="longitude-error" :errors="coordinateErrors('longitude')" />
        </Field>
      </div>
      <FieldError v-if="messages('weather.location').length" :errors="messages('weather.location')" />
    </FieldGroup>
  </section>
</template>
