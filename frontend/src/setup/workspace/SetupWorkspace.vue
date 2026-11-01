<script setup lang="ts">
import type { Locale, Profile } from "@/api/profile"
import { useSetupWorkspace } from "./useSetupWorkspace"
import SetupConfirmations from "./SetupConfirmations.vue"
import SetupFooter from "./SetupFooter.vue"
import SetupSidebar from "./SetupSidebar.vue"
import SetupStepContent from "./SetupStepContent.vue"

const props = defineProps<{ initialProfile: Profile | null; initialLocale: Locale }>()
const { editor, flow, submission } = useSetupWorkspace(props.initialProfile, props.initialLocale)
const { mode, locale, isDirty, setLocale } = editor
const { activeStep, steps, activeHeading, navigateTo } = flow
const { submitting } = submission
</script>

<template>
  <main class="min-h-[100dvh] bg-background text-foreground md:h-[100dvh] md:overflow-hidden">
    <div
      class="mx-auto grid w-full max-w-[100rem] md:h-full md:min-h-0 md:grid-cols-[14rem_minmax(0,1fr)]"
    >
      <SetupSidebar
        :locale="locale"
        :mode="mode"
        :steps="steps"
        :active-step="activeStep"
        :dirty="isDirty"
        :submitting="submitting"
        @navigate="navigateTo"
        @update:locale="setLocale"
      />
      <section class="flex min-h-[32rem] min-w-0 flex-col md:h-full md:min-h-0" aria-labelledby="setup-step-heading">
        <header class="flex shrink-0 flex-col gap-2 px-5 pt-8 pb-7 sm:px-8">
          <h1
            id="setup-step-heading"
            tabindex="-1"
            class="text-2xl leading-8 font-semibold tracking-tight focus:outline-none"
          >
            {{ activeHeading.title }}
          </h1>
          <p v-if="activeHeading.description" class="max-w-[72ch] text-sm leading-relaxed text-muted-foreground">{{ activeHeading.description }}</p>
        </header>
        <div
          id="setup-step-content"
          :inert="submitting"
          :aria-busy="submitting"
          class="min-h-0 flex-1 overflow-y-auto px-5 pb-8 sm:px-8"
        >
          <SetupStepContent />
        </div>
        <SetupFooter />
      </section>
    </div>
    <SetupConfirmations />
  </main>
</template>
