<script setup lang="ts">
import { CheckCircle2Icon, CircleDashedIcon, CircleXIcon, CloudSunIcon, ExternalLinkIcon, EyeIcon, EyeOffIcon, GaugeIcon, TriangleAlertIcon } from "@lucide/vue"
import { computed, ref } from "vue"

import type { Locale } from "@/api/profile"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput } from "@/components/ui/input-group"
import { Spinner } from "@/components/ui/spinner"
import { COPY } from "@/setup/copy"

const props = defineProps<{
  locale: Locale
  apiKey: string
  invalid: boolean
  errors: string[]
  validating: boolean
  keyState: "untested" | "valid" | "invalid" | "quota"
  testedAtText: string
  connectionError: string
  validationError: string
}>()

const emit = defineEmits<{
  "update:apiKey": [value: string]
  openKeyPage: []
  validate: []
}>()

const copy = computed(() => COPY[props.locale])
const showApiKey = ref(false)
const keyStateText = computed(() => {
  if (props.keyState === "valid") return copy.value.weather.keyValid
  if (props.keyState === "invalid") return copy.value.errors.issueCodes.weather_api_key_invalid
  if (props.keyState === "quota") return copy.value.errors.issueCodes.weather_api_quota_exceeded
  return copy.value.weather.keyUntested
})
</script>

<template>
  <section class="flex flex-col gap-6">
    <FieldGroup>
      <Field :data-invalid="invalid || errors.length > 0">
        <FieldLabel for="weather-api-key">{{ copy.weather.keyLabel }}</FieldLabel>
        <InputGroup>
          <InputGroupInput
            id="weather-api-key"
            :model-value="apiKey"
            :type="showApiKey ? 'text' : 'password'"
            :placeholder="copy.weather.keyPlaceholder"
            autocomplete="off"
            :aria-invalid="invalid || errors.length > 0"
            :aria-describedby="invalid || errors.length ? 'weather-api-key-error' : undefined"
            @update:model-value="(value: string | number) => emit('update:apiKey', String(value))"
          />
          <InputGroupAddon align="inline-end">
            <InputGroupButton :aria-label="showApiKey ? copy.common.hide : copy.common.show" @click="showApiKey = !showApiKey">
              <EyeOffIcon v-if="showApiKey" />
              <EyeIcon v-else />
            </InputGroupButton>
          </InputGroupAddon>
        </InputGroup>
        <FieldDescription>{{ copy.weather.keyDescription }}</FieldDescription>
        <FieldError v-if="invalid || errors.length" id="weather-api-key-error" :errors="[...(invalid ? [copy.weather.keyRequired] : []), ...errors]" />
      </Field>
    </FieldGroup>

    <div class="flex flex-wrap gap-2">
      <Button :disabled="validating || !apiKey.trim()" @click="emit('validate')">
        <Spinner v-if="validating" data-icon="inline-start" />
        <GaugeIcon v-else data-icon="inline-start" />
        {{ validating ? copy.weather.validating : copy.weather.validate }}
      </Button>
      <Button variant="outline" @click="emit('openKeyPage')">
        <ExternalLinkIcon data-icon="inline-start" />
        {{ copy.weather.getKey }}
      </Button>
    </div>

    <Alert v-if="validationError" variant="destructive">
      <TriangleAlertIcon />
      <AlertDescription>{{ validationError }}</AlertDescription>
    </Alert>

    <div
      v-if="keyState !== 'untested' || connectionError"
      class="flex flex-col gap-1.5 rounded-lg border bg-card p-3"
      role="status"
    >
      <p v-if="keyState === 'valid'" class="flex items-center gap-2 text-sm">
        <CheckCircle2Icon class="text-success" />
        <span>{{ keyStateText }}</span>
        <span v-if="testedAtText" class="text-muted-foreground">{{ testedAtText }}</span>
      </p>
      <p v-else-if="keyState === 'invalid'" class="flex items-center gap-2 text-sm text-destructive">
        <CircleXIcon />
        <span>{{ keyStateText }}</span>
      </p>
      <p v-else-if="keyState === 'quota'" class="flex items-center gap-2 text-sm text-warning">
        <TriangleAlertIcon />
        <span>{{ keyStateText }}</span>
      </p>
      <p v-else class="flex items-center gap-2 text-sm text-muted-foreground">
        <CircleDashedIcon />
        <span>{{ keyStateText }}</span>
      </p>
      <p v-if="connectionError" class="flex items-start gap-2 text-sm text-warning">
        <TriangleAlertIcon class="mt-0.5 shrink-0" />
        <span class="min-w-0">{{ connectionError }}</span>
      </p>
    </div>

    <details class="rounded-lg border bg-muted/30 p-4">
      <summary class="cursor-pointer font-medium">{{ copy.weather.guideTitle }}</summary>
      <ol class="mt-3 flex flex-col gap-4 text-sm leading-relaxed">
        <li v-for="(step, index) in copy.weather.guideSteps" :key="step.title" class="flex gap-3">
          <span class="flex size-6 shrink-0 items-center justify-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">{{ index + 1 }}</span>
          <div class="flex min-w-0 flex-col gap-1">
            <p class="font-medium">{{ step.title }}</p>
            <p class="text-muted-foreground">{{ step.action }}</p>
            <p class="text-muted-foreground">{{ step.expected }}</p>
            <p v-if="step.fallback" class="text-muted-foreground">{{ step.fallback }}</p>
          </div>
        </li>
      </ol>
    </details>

    <Alert v-if="copy.weather.validationOnSubmit">
      <CloudSunIcon />
      <AlertDescription>{{ copy.weather.validationOnSubmit }}</AlertDescription>
    </Alert>
  </section>
</template>
