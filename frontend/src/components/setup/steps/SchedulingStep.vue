<script setup lang="ts">
import { CheckIcon, CircleHelpIcon, SlidersHorizontalIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale, ResponseStyle } from "@/api/profile"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel, FieldLegend, FieldSet } from "@/components/ui/field"
import { InputGroup, InputGroupAddon, InputGroupInput } from "@/components/ui/input-group"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { COPY, DISTURBANCE_LABELS, RESPONSE_STYLE_LABELS, ZH_TIMING_HINTS } from "@/setup/copy"
import { detectDisturbancePreset, DISTURBANCE_PRESETS, isNonNegativeInteger, parseNumberInput } from "@/setup/model"
import type { DisturbancePreset, ProfileDraft } from "@/setup/model"

type Matching = ProfileDraft["matching"]
type Disturbance = ProfileDraft["disturbance"]
type DisturbanceKey = keyof Disturbance

const props = defineProps<{
  locale: Locale
  matching: Matching
  disturbance: Disturbance
  timingOpen: boolean
  errors: Record<string, string[]>
}>()

const emit = defineEmits<{
  "update:matching": [value: Matching]
  "update:disturbance": [value: Disturbance]
  "update:timingOpen": [value: boolean]
}>()

const copy = computed(() => COPY[props.locale])
const preset = computed(() => detectDisturbancePreset({ disturbance: props.disturbance }))
const timingFields = computed(() => [
  ["startup_grace_seconds", copy.value.preferences.startupGrace, copy.value.preferences.seconds, props.locale === "zh" ? ZH_TIMING_HINTS.startupGrace : ""],
  ["idle_before_switch_seconds", copy.value.preferences.idleBeforeSwitch, copy.value.preferences.seconds, props.locale === "zh" ? ZH_TIMING_HINTS.idleBeforeSwitch : ""],
  ["maximum_deferral_minutes", copy.value.preferences.maximumDeferral, copy.value.preferences.minutes, props.locale === "zh" ? ZH_TIMING_HINTS.maximumDeferral : ""],
  ["cycle_interval_minutes", copy.value.preferences.cycleInterval, copy.value.preferences.minutes, props.locale === "zh" ? ZH_TIMING_HINTS.cycleInterval : ""],
] as const)

function messages(...fields: string[]): string[] {
  return fields.flatMap((field) => props.errors[field] ?? [])
}

function timingErrors(field: DisturbanceKey): string[] {
  return [
    ...(!isNonNegativeInteger(props.disturbance[field]) ? [copy.value.preferences.nonNegative] : []),
    ...messages("disturbance", `disturbance.${field}`),
  ]
}

function setResponseStyle(value: unknown): void {
  if (typeof value === "string" && value) {
    emit("update:matching", { response_style: value as ResponseStyle })
  }
}

function setPreset(value: unknown): void {
  if (typeof value !== "string" || !(value in DISTURBANCE_PRESETS)) return
  emit("update:disturbance", { ...DISTURBANCE_PRESETS[value as DisturbancePreset] })
}

function setTiming(field: DisturbanceKey, value: string | number): void {
  emit("update:disturbance", { ...props.disturbance, [field]: parseNumberInput(value) })
}
</script>

<template>
  <section class="flex flex-col gap-8">
    <FieldSet :data-invalid="messages('matching.response_style').length > 0">
      <FieldLegend>{{ copy.preferences.responseTitle }}</FieldLegend>
      <FieldDescription>{{ copy.preferences.responseDescription }}</FieldDescription>
      <Select :model-value="matching.response_style" @update:model-value="setResponseStyle">
        <SelectTrigger class="w-full lg:hidden" :aria-label="copy.preferences.responseTitle" :aria-invalid="messages('matching.response_style').length > 0" :aria-describedby="messages('matching.response_style').length ? 'response-style-error' : undefined">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem v-for="style in (Object.keys(RESPONSE_STYLE_LABELS[locale]) as ResponseStyle[])" :key="style" :value="style">{{ RESPONSE_STYLE_LABELS[locale][style] }}</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <ToggleGroup
        type="single"
        variant="outline"
        :spacing="2"
        class="hidden w-full lg:flex"
        :model-value="matching.response_style"
        :aria-describedby="messages('matching.response_style').length ? 'response-style-error' : undefined"
        @update:model-value="setResponseStyle"
      >
        <ToggleGroupItem
          v-for="style in (Object.keys(RESPONSE_STYLE_LABELS[locale]) as ResponseStyle[])"
          :key="style"
          :value="style"
          class="min-w-28 flex-1 data-[state=on]:border-foreground/60 data-[state=on]:font-semibold"
        >
          <CheckIcon v-if="matching.response_style === style" data-icon="inline-start" />
          {{ RESPONSE_STYLE_LABELS[locale][style] }}
        </ToggleGroupItem>
      </ToggleGroup>
      <p class="text-sm text-muted-foreground" role="status">{{ copy.preferences.responseExplanations[matching.response_style] }}</p>
      <FieldError v-if="messages('matching.response_style').length" id="response-style-error" :errors="messages('matching.response_style')" />
    </FieldSet>

    <FieldSet>
      <FieldLegend>{{ copy.preferences.disturbanceTitle }}</FieldLegend>
      <FieldDescription>{{ copy.preferences.disturbanceDescription }}</FieldDescription>
      <Select :model-value="preset === 'custom' ? undefined : preset" @update:model-value="setPreset">
        <SelectTrigger class="w-full lg:hidden" :aria-label="copy.preferences.disturbanceTitle">
          <SelectValue :placeholder="copy.common.custom" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem v-for="choice in (Object.keys(DISTURBANCE_PRESETS) as DisturbancePreset[])" :key="choice" :value="choice">{{ DISTURBANCE_LABELS[locale][choice] }}</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <ToggleGroup
        type="single"
        variant="outline"
        :spacing="2"
        class="hidden w-full lg:flex"
        :model-value="preset === 'custom' ? undefined : preset"
        @update:model-value="setPreset"
      >
        <ToggleGroupItem
          v-for="choice in (Object.keys(DISTURBANCE_PRESETS) as DisturbancePreset[])"
          :key="choice"
          :value="choice"
          class="min-w-24 flex-1 data-[state=on]:border-foreground/60 data-[state=on]:font-semibold"
        >
          <CheckIcon v-if="preset === choice" data-icon="inline-start" />
          {{ DISTURBANCE_LABELS[locale][choice] }}
        </ToggleGroupItem>
      </ToggleGroup>
      <p class="text-sm text-muted-foreground" role="status">{{ copy.preferences.timingSummary(disturbance.startup_grace_seconds, disturbance.idle_before_switch_seconds, disturbance.maximum_deferral_minutes, disturbance.cycle_interval_minutes) }}</p>
      <Badge v-if="preset === 'custom'" variant="outline">{{ copy.common.custom }}</Badge>
    </FieldSet>

    <Collapsible :open="timingOpen" @update:open="(value: boolean) => emit('update:timingOpen', value)">
      <CollapsibleTrigger as-child>
        <Button variant="ghost">
          <SlidersHorizontalIcon data-icon="inline-start" />
          {{ copy.preferences.fineTune }}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent class="pt-4">
        <FieldGroup>
          <TooltipProvider>
            <div class="grid gap-5 sm:grid-cols-2">
            <Field
              v-for="field in timingFields"
              :key="field[0]"
              :data-invalid="timingErrors(field[0]).length > 0"
            >
              <div class="flex items-center gap-1">
                <FieldLabel :for="field[0]">{{ field[1] }}</FieldLabel>
                <Tooltip v-if="field[3]">
                  <TooltipTrigger as-child>
                    <Button type="button" variant="ghost" size="icon-xs" :aria-label="`${field[1]}说明`">
                      <CircleHelpIcon />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top" class="max-w-72 leading-relaxed">{{ field[3] }}</TooltipContent>
                </Tooltip>
              </div>
              <InputGroup>
                <InputGroupInput
                  :id="field[0]"
                  :model-value="disturbance[field[0]] ?? ''"
                  type="number"
                  min="0"
                  step="1"
                  :aria-invalid="timingErrors(field[0]).length > 0"
                  :aria-describedby="timingErrors(field[0]).length ? `timing-error-${field[0]}` : undefined"
                  @update:model-value="(value: string | number) => setTiming(field[0], value)"
                />
                <InputGroupAddon align="inline-end">{{ field[2] }}</InputGroupAddon>
              </InputGroup>
              <FieldError v-if="timingErrors(field[0]).length" :id="`timing-error-${field[0]}`" :errors="timingErrors(field[0])" />
            </Field>
            </div>
          </TooltipProvider>
        </FieldGroup>
      </CollapsibleContent>
    </Collapsible>
  </section>
</template>
