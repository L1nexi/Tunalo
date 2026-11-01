<script setup lang="ts">
import { onMounted, ref } from "vue"

import type { Locale, Profile } from "@/api/profile"
import { ApiError, getProfile } from "@/api/profile"
import { COPY, SetupWorkspace } from "@/setup"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Toaster } from "@/components/ui/sonner"

type AppState = "loading" | "ready" | "unavailable"

const initialLocale: Locale = new URLSearchParams(window.location.search).get("locale") === "zh" ? "zh" : "en"
const state = ref<AppState>("loading")
const profile = ref<Profile | null>(null)
const detail = ref("")

document.documentElement.lang = initialLocale === "zh" ? "zh-CN" : "en"
document.title = initialLocale === "zh" ? "Tunalo 设置" : "Tunalo Settings"

async function loadProfile(): Promise<void> {
  state.value = "loading"
  detail.value = ""
  try {
    profile.value = await getProfile()
    state.value = "ready"
  } catch (error) {
    state.value = "unavailable"
    detail.value = error instanceof ApiError ? error.message : COPY[initialLocale].errors.generic
  }
}

onMounted(loadProfile)
</script>

<template>
  <SetupWorkspace
    v-if="state === 'ready'"
    :initial-profile="profile"
    :initial-locale="initialLocale"
  />

  <main v-else class="grid min-h-[100dvh] place-items-center bg-background p-6 text-foreground">
    <section v-if="state === 'loading'" class="flex w-full max-w-lg flex-col gap-6" aria-busy="true">
      <h1 class="text-2xl font-semibold">{{ COPY[initialLocale].loading.title }}</h1>
      <div class="flex flex-col gap-4">
        <Skeleton class="h-10 w-full" />
        <Skeleton class="h-24 w-full" />
        <Skeleton class="h-10 w-2/3" />
      </div>
    </section>

    <section v-else class="flex w-full max-w-lg flex-col gap-4">
      <h1 class="text-2xl font-semibold">{{ COPY[initialLocale].unavailable.title }}</h1>
      <p class="text-sm text-muted-foreground">{{ COPY[initialLocale].unavailable.description }}</p>
      <p class="text-sm text-destructive" role="alert">{{ detail }}</p>
      <Button class="self-start" @click="loadProfile">{{ COPY[initialLocale].unavailable.retry }}</Button>
    </section>
  </main>

  <Toaster position="top-center" />
</template>
