<script setup lang="ts">
import type { Component } from "vue"
import { computed } from "vue"
import {
  AppWindowIcon, ClipboardCheckIcon, CloudSunIcon, LayersIcon,
  MonitorIcon, MoonIcon, SlidersHorizontalIcon, SunIcon,
} from "@lucide/vue"

import type { Locale } from "@/api/profile"
import TunaloMark from "@/components/TunaloMark.vue"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger } from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { cn } from "@/lib/utils"
import { COPY } from "@/setup/copy"
import type { StepId } from "@/setup/flow"
import type { SetupMode } from "@/setup/useProfileDraft"
import type { SetupNavigationItem } from "@/setup/useSetupFlow"
import { themeMode } from "@/theme"

const props = defineProps<{
  locale: Locale
  mode: SetupMode
  steps: SetupNavigationItem[]
  activeStep: StepId
  dirty: boolean
  submitting: boolean
}>()
const emit = defineEmits<{
  navigate: [id: StepId]
  "update:locale": [locale: Locale]
}>()

const copy = computed(() => COPY[props.locale])
const stepIcons: Record<StepId, Component> = {
  wallpaper: MonitorIcon,
  weather: CloudSunIcon,
  scenes: LayersIcon,
  scheduling: SlidersHorizontalIcon,
  activity: AppWindowIcon,
  review: ClipboardCheckIcon,
}
const themeIcon = computed(() => ({ auto: MonitorIcon, light: SunIcon, dark: MoonIcon })[themeMode.value])
const themeLabel = computed(() => ({
  auto: copy.value.nav.themeSystem,
  light: copy.value.nav.themeLight,
  dark: copy.value.nav.themeDark,
})[themeMode.value])

function setTheme(value: unknown): void {
  if (value === "auto" || value === "light" || value === "dark") themeMode.value = value
}

function setLocale(value: unknown): void {
  if (value === "zh" || value === "en") emit("update:locale", value)
}
</script>

<template>
  <aside class="flex min-w-0 flex-col gap-4 rounded-xl bg-sidebar p-4 text-sidebar-foreground ring-1 ring-sidebar-border md:h-full md:min-h-0 md:overflow-hidden">
    <header class="flex items-center gap-2.5 px-1">
      <TunaloMark class="size-7 shrink-0 text-primary" />
      <div class="flex min-w-0 flex-col">
        <p class="text-lg leading-7 font-semibold tracking-tight">{{ copy.appName }}</p>
        <p class="text-sm leading-5 text-muted-foreground">{{ copy.mode[mode] }}</p>
      </div>
    </header>

    <nav :inert="submitting" class="flex gap-1 overflow-x-auto pb-1 md:min-h-0 md:flex-1 md:flex-col md:overflow-y-auto" :aria-label="mode === 'setup' ? copy.nav.setupNavigation : copy.nav.settingsNavigation">
      <p class="hidden px-3 pb-1 text-xs font-medium text-muted-foreground md:block">{{ mode === 'setup' ? copy.nav.setupNavigation : copy.nav.settingsNavigation }}</p>
      <Button
        v-for="step in steps"
        :key="step.id"
        type="button"
        variant="ghost"
        :aria-current="activeStep === step.id ? 'page' : undefined"
        :class="cn('min-w-44 justify-start border-l-2 px-3 text-left md:min-w-0',
          activeStep === step.id
            ? 'border-l-primary bg-primary/10 font-semibold dark:bg-primary/18'
            : 'border-l-transparent hover:bg-sidebar-accent')"
        @click="emit('navigate', step.id)"
      >
        <component :is="stepIcons[step.id]" data-icon="inline-start" />
        <span class="min-w-0 flex-1 truncate font-medium">{{ step.title }}</span>
        <span v-if="step.status" class="shrink-0 text-xs text-muted-foreground">{{ step.status }}</span>
        <span v-if="step.nextRequired" data-next-required="true" aria-hidden="true" class="size-1.5 shrink-0 rounded-full bg-foreground" />
      </Button>
    </nav>

    <p v-if="mode === 'settings'" class="text-sm text-muted-foreground" role="status">
      {{ dirty ? copy.nav.unsaved : copy.nav.saved }}
    </p>

    <div :inert="submitting" class="mt-auto flex items-center justify-between border-t border-sidebar-border pt-3">
      <ToggleGroup type="single" size="sm" :spacing="1" class="shrink-0 rounded-md border border-sidebar-border bg-muted/40 p-0.5" :model-value="locale" :aria-label="copy.nav.languageLabel" @update:model-value="setLocale">
        <ToggleGroupItem value="zh" class="rounded-sm data-[state=on]:bg-background" aria-label="中文">中</ToggleGroupItem>
        <ToggleGroupItem value="en" class="rounded-sm data-[state=on]:bg-background" aria-label="English">EN</ToggleGroupItem>
      </ToggleGroup>
      <Select :model-value="themeMode" @update:model-value="setTheme">
        <SelectTrigger class="size-9 justify-center gap-0 rounded-md border border-sidebar-border bg-transparent p-0 hover:bg-sidebar-accent [&_svg:last-child]:hidden" :aria-label="`${copy.nav.themeLabel}: ${themeLabel}`" :title="`${copy.nav.themeLabel}: ${themeLabel}`">
          <component :is="themeIcon" />
        </SelectTrigger>
        <SelectContent position="popper" align="end">
          <SelectGroup>
            <SelectItem value="auto">{{ copy.nav.themeSystem }}</SelectItem>
            <SelectItem value="light">{{ copy.nav.themeLight }}</SelectItem>
            <SelectItem value="dark">{{ copy.nav.themeDark }}</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>
  </aside>
</template>
