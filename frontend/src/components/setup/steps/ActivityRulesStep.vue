<script setup lang="ts">
import { ChevronDownIcon, TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"
import { toast } from "vue-sonner"

import type { Locale } from "@/api/profile"
import ActivityListInput from "@/components/setup/ActivityListInput.vue"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Field, FieldError, FieldGroup, FieldLabel, FieldLegend, FieldSet } from "@/components/ui/field"
import { COPY, ZH_ACTIVITY_NOTE } from "@/setup/copy"
import { ACTIVITY_RULE_PACKS, importActivityRulePack } from "@/setup/activityRulePacks"
import type { ActivityRulePack } from "@/setup/activityRulePacks"
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

function importPack(pack: ActivityRulePack, target: "work" | "leisure"): void {
  const result = importActivityRulePack(props.activity, pack, target)
  if (result.added > 0) emit("update:activity", result.activity)
  toast(copy.value.activity.imported(result.added, result.skipped))
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
    <Collapsible>
      <CollapsibleTrigger as-child>
        <Button type="button" variant="ghost"><ChevronDownIcon data-icon="inline-start" />{{ copy.activity.importGroups }}</Button>
      </CollapsibleTrigger>
      <CollapsibleContent class="pt-3">
        <div class="flex flex-col divide-y">
          <section v-for="pack in ACTIVITY_RULE_PACKS" :key="pack.id" :aria-label="copy.activity.packLabels[pack.id]" class="flex flex-wrap items-center justify-between gap-3 py-4">
            <div class="min-w-0 flex-1 basis-60">
              <h3 class="text-sm font-medium">{{ copy.activity.packLabels[pack.id] }}</h3>
              <p class="mt-1 text-sm text-muted-foreground">{{ pack.apps.map((app) => locale === 'en' ? app.nameEn ?? app.name : app.name).join(locale === 'zh' ? '、' : ', ') }}</p>
            </div>
            <div class="flex gap-2">
              <Button type="button" size="sm" variant="outline" @click="importPack(pack, 'work')">{{ copy.activity.importWork }}</Button>
              <Button type="button" size="sm" variant="outline" @click="importPack(pack, 'leisure')">{{ copy.activity.importLeisure }}</Button>
            </div>
          </section>
        </div>
      </CollapsibleContent>
    </Collapsible>
  </section>
</template>
