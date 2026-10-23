<script setup lang="ts">
import { TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale } from "@/api/profile"
import ReviewWeatherStatus from "@/components/setup/review/ReviewWeatherStatus.vue"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { COPY, associationSummary } from "@/setup/copy"
import type { StepId } from "@/setup/flow"
import type { ProfileDraft } from "@/setup/model"
import { describeProfileChanges } from "@/setup/review/changes"
import { reviewGroups } from "@/setup/review/summary"
import type { ReviewWeatherState } from "@/setup/review/summary"

const props = defineProps<{
  locale: Locale
  draft: ProfileDraft
  savedDraft: ProfileDraft
  mode: "setup" | "settings"
  valid: boolean
  missingSteps: Array<{ id: StepId; title: string }>
  weatherKeyState: ReviewWeatherState
  weatherTestedAtText: string
  weatherConnectionError: string
  validatingWeather: boolean
  hasPendingActivity: boolean
}>()
const emit = defineEmits<{ validateWeather: []; openStep: [id: StepId] }>()
const copy = computed(() => COPY[props.locale])
const sceneIds = computed(() => Object.keys(props.draft.scenes))
const changes = computed(() => describeProfileChanges(props.savedDraft, props.draft, props.locale))
const groups = computed(() => reviewGroups(props.draft, props.locale, props.weatherKeyState))
</script>

<template>
  <section class="flex flex-col gap-6">
    <section v-if="mode === 'settings'" aria-labelledby="changes-heading">
      <h2 id="changes-heading" class="mb-3 text-base font-semibold">{{ copy.review.changesTitle }}</h2>
      <p
        v-if="changes.length === 0 && !hasPendingActivity"
        role="status"
        class="text-sm text-muted-foreground"
      >
        {{ copy.review.noChanges }}
      </p>
      <ul v-else-if="changes.length > 0" class="divide-y rounded-lg border">
        <li
          v-for="(change, index) in changes"
          :key="`${change.id}-${index}`"
          class="flex flex-wrap items-start justify-between gap-3 px-4 py-3"
        >
          <div class="min-w-0">
            <p class="text-sm font-medium">{{ change.label }}</p>
            <p
              v-if="change.before !== copy.review.secretChanged"
              class="text-sm text-muted-foreground [overflow-wrap:anywhere]"
            >
              {{ change.before }} → {{ change.after }}
            </p>
            <p v-else class="text-sm text-muted-foreground">{{ change.after }}</p>
          </div>
          <Button type="button" variant="ghost" size="sm" @click="emit('openStep', change.id)">{{
            copy.review.edit
          }}</Button>
        </li>
      </ul>
      <p v-if="hasPendingActivity" role="status" class="text-sm text-warning">
        {{ copy.review.pendingInputNotice }}
      </p>
    </section>

    <details :open="mode === 'setup' || undefined">
      <summary v-if="mode === 'settings'" class="cursor-pointer text-sm font-medium">
        {{ copy.review.currentDetails }}
      </summary>
      <div class="mt-3 flex flex-col gap-6">
        <section v-for="group in groups" :key="group.id" class="flex flex-col gap-3">
          <h3 class="text-base font-semibold">{{ copy.steps[group.id].title }}</h3>
          <dl class="rounded-lg border">
            <div
              v-for="row in group.rows"
              :key="row.id"
              class="grid min-w-0 gap-1 border-b px-4 py-3 last:border-b-0 sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-4"
            >
              <dt class="text-sm text-muted-foreground">{{ row.label }}</dt>
              <dd class="min-w-0">
                <ReviewWeatherStatus
                  v-if="row.id === 'weather'"
                  :locale="locale"
                  :state="weatherKeyState"
                  :tested-at-text="weatherTestedAtText"
                  :connection-error="weatherConnectionError"
                  :validating="validatingWeather"
                  :has-api-key="Boolean(draft.weather.api_key.trim())"
                  @validate="emit('validateWeather')"
                />
                <div
                  v-else
                  class="text-sm [overflow-wrap:anywhere]"
                  :class="group.deEmphasized ? 'font-normal text-muted-foreground' : 'font-medium'"
                >
                  {{ row.value }}
                  <ul v-if="row.id === 'scenes'" class="mt-1 text-sm font-normal text-muted-foreground">
                    <li v-for="id in sceneIds" :key="id">
                      {{ draft.scenes[id]!.name }}（{{
                        associationSummary(draft.scenes[id]!.associations, locale)
                      }}）：{{ draft.scenes[id]!.playlist || copy.common.notSet }}
                    </li>
                  </ul>
                </div>
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </details>

    <Alert v-if="!valid" variant="destructive">
      <TriangleAlertIcon />
      <AlertTitle>{{ copy.review.missingTitle }}</AlertTitle>
      <AlertDescription class="flex flex-col gap-3">
        <span>{{ copy.review.missingDescription }}</span>
        <span class="flex flex-wrap gap-2">
          <Button
            v-for="step in missingSteps"
            :key="step.id"
            size="sm"
            variant="outline"
            @click="emit('openStep', step.id)"
            >{{ step.title }}</Button
          >
        </span>
      </AlertDescription>
    </Alert>
  </section>
</template>
