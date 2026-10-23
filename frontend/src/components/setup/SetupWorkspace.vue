<script setup lang="ts">
import type { Locale, Profile } from "@/api/profile"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { useSetupWorkspace } from "@/setup/useSetupWorkspace"
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
  <main class="min-h-[100dvh] bg-muted/40 p-2 text-foreground sm:p-4 md:h-[100dvh] md:overflow-hidden">
    <div
      class="mx-auto grid w-full max-w-[100rem] gap-4 md:h-full md:min-h-0 md:grid-cols-[14rem_minmax(0,1fr)]"
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
      <Card
        class="min-w-0 min-h-[32rem] md:h-full md:min-h-0 [--card-spacing:--spacing(4)] sm:[--card-spacing:--spacing(7)]"
      >
        <CardHeader class="shrink-0">
          <CardTitle
            ><h1
              id="setup-step-heading"
              tabindex="-1"
              class="text-2xl leading-8 font-semibold tracking-tight focus:outline-none"
            >
              {{ activeHeading.title }}
            </h1></CardTitle
          >
          <CardDescription v-if="activeHeading.description">{{ activeHeading.description }}</CardDescription>
        </CardHeader>
        <CardContent
          id="setup-step-content"
          :inert="submitting"
          :aria-busy="submitting"
          class="min-h-0 flex-1 overflow-y-auto pt-0 pb-6"
        >
          <SetupStepContent />
        </CardContent>
        <Separator />
        <SetupFooter />
      </Card>
    </div>
    <SetupConfirmations />
  </main>
</template>
