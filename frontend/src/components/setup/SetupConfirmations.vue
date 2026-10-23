<script setup lang="ts">
import { computed } from "vue"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { COPY, ZH_WEATHER_SAVE_PROMPT } from "@/setup/copy"
import {
  useSetupEditor,
  useSetupNativeWindow,
  useSetupSubmission,
  useSetupWeather,
} from "@/setup/useSetupWorkspace"

const { locale, mode } = useSetupEditor()
const { closeDialogOpen, closeWindow } = useSetupNativeWindow()
const { submitting, submitProfile } = useSetupSubmission()
const { weatherSaveDialogOpen, weatherSaveFailure } = useSetupWeather()
const copy = computed(() => COPY[locale.value])
</script>

<template>
  <AlertDialog v-model:open="closeDialogOpen">
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>{{ copy.nav.discardTitle }}</AlertDialogTitle>
        <AlertDialogDescription>{{
          mode === "setup" ? copy.nav.discardSetupDescription : copy.nav.discardSettingsDescription
        }}</AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>{{ copy.nav.keepEditing }}</AlertDialogCancel>
        <AlertDialogAction @click="closeWindow">{{ copy.nav.discardChanges }}</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
  <AlertDialog v-model:open="weatherSaveDialogOpen">
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>{{
          locale === "zh" ? ZH_WEATHER_SAVE_PROMPT.title : copy.errors.weatherValidationUnavailable
        }}</AlertDialogTitle>
        <AlertDialogDescription>
          {{ weatherSaveFailure }}
          <template v-if="locale === 'zh'">{{ ZH_WEATHER_SAVE_PROMPT.description }}</template>
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>{{ copy.common.back }}</AlertDialogCancel>
        <AlertDialogAction :disabled="submitting" @click="submitProfile(true)">{{
          mode === "setup" ? copy.review.create : copy.review.save
        }}</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>
