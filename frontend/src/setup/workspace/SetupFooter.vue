<script setup lang="ts">
import { computed } from "vue"

import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"
import { COPY } from "@/setup/copy"
import {
  useSetupEditor,
  useSetupFlowContext,
  useSetupNativeWindow,
  useSetupSubmission,
  useSetupWeather,
} from "./useSetupWorkspace"

defineProps<{ scrollable: boolean }>()

const { locale, mode, isDirty } = useSetupEditor()
const { activePage, previousPage, allValid, navigateTo, navigateToStep } = useSetupFlowContext()
const { requestClose } = useSetupNativeWindow()
const { submitting, submitProfile } = useSetupSubmission()
const { locating } = useSetupWeather()
const copy = computed(() => COPY[locale.value])
const application = computed(() => activePage.value === "application")
</script>

<template>
  <footer :class="cn('flex shrink-0 items-end justify-between gap-3 border-t px-5 py-5 sm:px-8', scrollable ? 'border-border' : 'border-transparent')">
    <Button
      v-if="activePage === 'review'"
      variant="outline"
      class="shrink-0"
      :disabled="submitting"
      @click="navigateTo(previousPage)"
      >{{ copy.nav.backToSettings }}</Button
    >
    <Button v-else variant="outline" class="shrink-0" :disabled="submitting" @click="requestClose">{{
      mode === "setup" ? copy.common.cancel : copy.common.close
    }}</Button>
    <div v-if="!application" class="flex min-w-0 flex-wrap justify-end gap-2">
      <Button
        v-if="activePage !== 'review'"
        :variant="mode === 'settings' ? 'outline' : 'default'"
        :disabled="submitting"
        @click="navigateToStep('review')"
      >
        {{ mode === "setup" ? copy.nav.reviewSetup : copy.nav.reviewSettings }}
      </Button>
      <Button
        v-if="mode === 'settings' || activePage === 'review'"
        :disabled="submitting || locating || !allValid || (mode === 'settings' && !isDirty)"
        @click="submitProfile()"
      >
        <Spinner v-if="submitting" data-icon="inline-start" />
        {{
          submitting
            ? mode === "setup"
              ? copy.review.creating
              : copy.review.saving
            : mode === "setup"
              ? copy.review.create
              : copy.review.save
        }}
      </Button>
    </div>
  </footer>
</template>
