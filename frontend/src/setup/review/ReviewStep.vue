<script setup lang="ts">
import { TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale, PlaylistScanResult } from "@/api/profile"
import ReviewWeatherStatus from "./ReviewWeatherStatus.vue"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { COPY, associationSummary } from "@/setup/copy"
import type { StepId } from "@/setup/workflow/steps"
import type { ProfileDraft } from "@/setup/profile/model"
import { playlistBindingStatus } from "@/setup/profile/model"
import { describeProfileChanges } from "./changes"
import { reviewGroups } from "./summary"
import type { ReviewWeatherState } from "./summary"

const props = defineProps<{
  locale: Locale
  draft: ProfileDraft
  savedDraft: ProfileDraft
  playlists: PlaylistScanResult["playlists"]
  mode: "setup" | "settings"
  valid: boolean
  missingSteps: Array<{ id: StepId; title: string }>
  weatherKeyState: ReviewWeatherState
  weatherTestedAtText: string
  weatherConnectionError: string
  validatingWeather: boolean
  hasPendingActivity: boolean
}>()
const emit = defineEmits<{ validateWeather: []; openStep: [id: StepId]; openScene: [id: string] }>()
const copy = computed(() => COPY[props.locale])
const sceneIds = computed(() => Object.keys(props.draft.scenes))
const changes = computed(() => describeProfileChanges(props.savedDraft, props.draft, props.locale))
const groups = computed(() => reviewGroups(props.draft, props.locale, props.weatherKeyState, props.playlists))
const sceneStatuses = computed(() => {
  const available = new Set(props.playlists.map((playlist) => playlist.name))
  return Object.fromEntries(Object.entries(props.draft.scenes).map(([id, scene]) => [id, playlistBindingStatus(scene.playlist, available)]))
})
</script>

<template>
  <section class="flex flex-col gap-6">
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
    <section v-if="mode === 'settings'" aria-labelledby="changes-heading">
      <h2 id="changes-heading" class="mb-4 text-lg font-semibold">{{ copy.review.changesTitle }}</h2>
      <p
        v-if="changes.length === 0 && !hasPendingActivity"
        role="status"
        class="text-sm text-muted-foreground"
      >
        {{ copy.review.noChanges }}
      </p>
      <ul v-else-if="changes.length > 0" class="flex flex-col gap-4">
        <li
          v-for="(change, index) in changes"
          :key="`${change.id}-${index}`"
          class="flex flex-wrap items-start justify-between gap-3"
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

    <component :is="mode === 'settings' ? 'details' : 'div'">
      <summary v-if="mode === 'settings'" class="cursor-pointer text-sm font-medium">
        {{ copy.review.currentDetails }}
      </summary>
      <div class="mt-4 flex flex-col gap-8">
        <section v-for="group in groups" :key="group.id" class="flex flex-col gap-3">
          <h2 class="text-lg font-semibold">{{ copy.steps[group.id].title }}</h2>
          <dl class="flex flex-col gap-4">
            <div
              v-for="row in group.rows"
              :key="row.id"
              class="relative grid min-w-0 gap-1"
              :class="{ 'sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-4': group.rows.length > 1 }"
            >
              <dt class="text-sm text-muted-foreground" :class="{ 'sr-only': group.rows.length === 1 }">{{ row.label }}</dt>
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
                  <ul v-if="row.id === 'scenes'" class="mt-1 flex flex-col gap-1 text-sm font-normal text-muted-foreground">
                    <li v-for="id in sceneIds" :key="id" class="flex flex-wrap items-baseline gap-x-2">
                      <span>{{ draft.scenes[id]!.name }}（{{
                        associationSummary(draft.scenes[id]!.associations, locale)
                      }}）：{{ draft.scenes[id]!.playlist || copy.common.notSet }}</span>
                      <Button
                        v-if="sceneStatuses[id] !== 'bound'"
                        type="button"
                        variant="link"
                        size="sm"
                        class="h-auto p-0"
                        :aria-label="`${draft.scenes[id]!.name}: ${sceneStatuses[id] === 'unavailable' ? copy.review.unavailableBinding : copy.review.awaitingPlaylist}`"
                        @click="emit('openScene', id)"
                      >{{ sceneStatuses[id] === 'unavailable' ? copy.review.unavailableBinding : copy.review.awaitingPlaylist }}</Button>
                    </li>
                  </ul>
                </div>
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </component>
  </section>
</template>
