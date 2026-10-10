<script setup lang="ts">
import { TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale } from "@/api/profile"
import ActivityListInput from "@/components/setup/ActivityListInput.vue"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Field, FieldError, FieldGroup, FieldLabel, FieldLegend, FieldSet } from "@/components/ui/field"
import { COPY, ZH_ACTIVITY_NOTE } from "@/setup/copy"
import type { ActivityField, PendingActivity, ProfileDraft } from "@/setup/model"

type Activity = ProfileDraft["activity"]

const props = defineProps<{
  locale: Locale
  activity: Activity
  pending: PendingActivity
  showPending: boolean
  conflicts: string[]
  errors: string[]
}>()

const emit = defineEmits<{
  "update:activity": [value: Activity]
  "update:pending": [field: ActivityField, value: string]
}>()

const copy = computed(() => COPY[props.locale])
const groups = computed(() => [
  {
    id: "work",
    title: copy.value.activity.workTitle,
    processKey: "work_processes" as const,
    titleKey: "work_title_keywords" as const,
  },
  {
    id: "leisure",
    title: copy.value.activity.leisureTitle,
    processKey: "leisure_processes" as const,
    titleKey: "leisure_title_keywords" as const,
  },
])

function setList(field: keyof Activity, values: string[]): void {
  emit("update:activity", { ...props.activity, [field]: values })
}
</script>

<template>
  <section class="flex flex-col gap-6">
    <p v-if="locale === 'zh'" class="text-sm leading-relaxed text-muted-foreground">{{ ZH_ACTIVITY_NOTE }}</p>
    <p class="text-sm leading-relaxed text-muted-foreground">{{ copy.activity.matchingHelp }}</p>
    <Alert v-if="conflicts.length" variant="destructive">
      <TriangleAlertIcon />
      <AlertTitle>{{ copy.activity.conflictTitle }}</AlertTitle>
      <AlertDescription>{{ copy.activity.conflictDescription(conflicts.join(", ")) }}</AlertDescription>
    </Alert>

    <Alert v-if="errors.length" variant="destructive">
      <TriangleAlertIcon />
      <AlertTitle>{{ copy.common.needsAttention }}</AlertTitle>
      <AlertDescription>{{ errors.join('; ') }}</AlertDescription>
    </Alert>

    <div class="grid gap-6 lg:grid-cols-2">
      <FieldSet v-for="group in groups" :key="group.id" class="gap-5">
        <FieldLegend>{{ group.title }}</FieldLegend>
        <FieldGroup>
          <Field>
            <FieldLabel :for="`${group.id}-processes`">{{ copy.activity.processLabel }}</FieldLabel>
            <p class="text-xs text-muted-foreground">{{ copy.activity.processHelp }}</p>
            <ActivityListInput
              :id="`${group.id}-processes`"
              :model-value="activity[group.processKey]"
              :pending="pending[group.processKey]"
              :invalid="showPending && Boolean(pending[group.processKey].trim())"
              :error-id="`${group.id}-process-pending-error`"
              :placeholder="copy.activity.processPlaceholder"
              :add-label="copy.activity.add"
              :remove-label="copy.common.remove"
              :empty-label="copy.activity.empty"
              @update:model-value="(values: string[]) => setList(group.processKey, values)"
              @update:pending="(value: string) => emit('update:pending', group.processKey, value)"
            />
            <FieldError v-if="showPending && pending[group.processKey].trim()" :id="`${group.id}-process-pending-error`" :errors="[copy.activity.pendingWarning]" />
          </Field>
          <Field>
            <FieldLabel :for="`${group.id}-title-keywords`">{{ copy.activity.titleKeywordLabel }}</FieldLabel>
            <p class="text-xs text-muted-foreground">{{ copy.activity.titleHelp }}</p>
            <ActivityListInput
              :id="`${group.id}-title-keywords`"
              :model-value="activity[group.titleKey]"
              :pending="pending[group.titleKey]"
              :invalid="showPending && Boolean(pending[group.titleKey].trim())"
              :error-id="`${group.id}-title-pending-error`"
              :placeholder="copy.activity.keywordPlaceholder"
              :add-label="copy.activity.add"
              :remove-label="copy.common.remove"
              :empty-label="copy.activity.empty"
              @update:model-value="(values: string[]) => setList(group.titleKey, values)"
              @update:pending="(value: string) => emit('update:pending', group.titleKey, value)"
            />
            <FieldError v-if="showPending && pending[group.titleKey].trim()" :id="`${group.id}-title-pending-error`" :errors="[copy.activity.pendingWarning]" />
          </Field>
        </FieldGroup>
      </FieldSet>
    </div>
  </section>
</template>
