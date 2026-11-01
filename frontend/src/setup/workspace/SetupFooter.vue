<script setup lang="ts">
import { computed } from "vue"

import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { COPY } from "@/setup/copy"
import {
  useSetupEditor,
  useSetupFlowContext,
  useSetupNativeWindow,
  useSetupSubmission,
  useSetupWeather,
} from "./useSetupWorkspace"

const { locale, mode, isDirty } = useSetupEditor()
const { activeStep, previousSection, allValid, navigateTo, navigateToStep } = useSetupFlowContext()
const { requestClose } = useSetupNativeWindow()
const { submitting, submitProfile } = useSetupSubmission()
const { locating } = useSetupWeather()
const copy = computed(() => COPY[locale.value])
</script>

<template>
  <footer class="flex shrink-0 items-end justify-between gap-3 px-5 py-5 sm:px-8">
    <Button
      v-if="activeStep === 'review'"
      variant="outline"
      class="shrink-0"
      :disabled="submitting"
      @click="navigateTo(previousSection)"
      >{{ copy.nav.backToSettings }}</Button
    >
    <Button v-else variant="ghost" class="shrink-0" :disabled="submitting" @click="requestClose">{{
      mode === "setup" ? copy.common.cancel : copy.common.close
    }}</Button>
    <div class="flex min-w-0 flex-wrap justify-end gap-2">
      <Button
        v-if="activeStep !== 'review'"
        :variant="mode === 'settings' ? 'outline' : 'default'"
        :disabled="submitting"
        @click="navigateToStep('review')"
      >
        {{ mode === "setup" ? copy.nav.reviewSetup : copy.nav.reviewSettings }}
      </Button>
      <Button
        v-if="mode === 'settings' || activeStep === 'review'"
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
