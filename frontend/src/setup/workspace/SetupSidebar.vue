<script setup lang="ts">
import type { Component } from "vue"
import { computed } from "vue"
import {
  AppWindowIcon, ClipboardCheckIcon, CloudSunIcon, LayersIcon,
  MonitorIcon, MoonIcon, SettingsIcon, SlidersHorizontalIcon, SunIcon,
} from "@lucide/vue"

import TunaloMark from "@/components/TunaloMark.vue"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger } from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { cn } from "@/lib/utils"
import { COPY } from "@/setup/copy"
import type { PageId } from "@/setup/workflow/useSetupNavigation"
import { themeMode } from "@/theme"
import { useSetupEditor, useSetupFlowContext, useSetupSubmission } from "./useSetupWorkspace"

const { locale, mode, isDirty: dirty, setLocale } = useSetupEditor()
const { navigationItems, activePage, navigateTo } = useSetupFlowContext()
const { submitting } = useSetupSubmission()
const copy = computed(() => COPY[locale.value])
const pageIcons: Record<PageId, Component> = {
  application: SettingsIcon,
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
</script>

<template>
  <aside class="flex min-w-0 flex-col gap-7 bg-sidebar px-4 py-6 text-sidebar-foreground md:h-full md:min-h-0 md:overflow-hidden">
    <header class="flex items-center gap-2.5 px-1">
      <TunaloMark class="size-7 shrink-0 text-primary" />
      <div class="flex min-w-0 flex-col">
        <p class="text-lg leading-7 font-semibold tracking-tight">{{ copy.appName }}</p>
        <p v-if="mode === 'setup'" class="text-sm leading-5 text-muted-foreground">{{ copy.mode.setup }}</p>
      </div>
    </header>

    <nav :inert="submitting" class="flex gap-1 overflow-x-auto pb-1 md:min-h-0 md:flex-1 md:flex-col md:overflow-y-auto" :aria-label="mode === 'setup' ? copy.nav.setupNavigation : copy.nav.settingsNavigation">
      <Button
        v-for="page in navigationItems"
        :key="page.id"
        type="button"
        variant="ghost"
        :aria-label="page.title"
        :aria-current="activePage === page.id ? 'page' : undefined"
        :aria-describedby="page.nextRequired || page.status === copy.nav.changed ? `setup-nav-status-${page.id}` : undefined"
        :class="cn('min-w-44 justify-start px-3 text-left md:min-w-0',
          activePage === page.id
            ? 'bg-sidebar-accent'
            : 'hover:bg-sidebar-accent')"
        @click="navigateTo(page.id)"
      >
        <component :is="pageIcons[page.id]" data-icon="inline-start" :class="cn(activePage === page.id && 'text-primary')" />
        <span class="min-w-0 flex-1 truncate font-medium">{{ page.title }}</span>
        <span v-if="page.nextRequired" :id="`setup-nav-status-${page.id}`" class="shrink-0 text-xs text-muted-foreground">{{ copy.nav.pending }}</span>
        <span v-else-if="page.status === copy.nav.changed" :id="`setup-nav-status-${page.id}`" class="relative size-1.5 shrink-0 rounded-full bg-foreground">
          <span class="sr-only">{{ copy.nav.changed }}</span>
        </span>
      </Button>
    </nav>

    <p v-if="mode === 'settings'" class="text-sm text-muted-foreground" :class="{ 'sr-only': !dirty }" role="status">
      {{ dirty ? copy.nav.unsaved : copy.nav.saved }}
    </p>

    <div :inert="submitting" class="mt-auto flex items-center justify-between">
      <ToggleGroup type="single" size="sm" :spacing="1" class="shrink-0" :model-value="locale" :aria-label="copy.nav.languageLabel" @update:model-value="setLocale">
        <ToggleGroupItem value="zh" class="rounded-sm" aria-label="中文">中</ToggleGroupItem>
        <ToggleGroupItem value="en" class="rounded-sm" aria-label="English">EN</ToggleGroupItem>
      </ToggleGroup>
      <Select :model-value="themeMode" @update:model-value="setTheme">
        <SelectTrigger class="size-9 justify-center gap-0 border-0 bg-transparent p-0 hover:bg-sidebar-accent [&_svg:last-child]:hidden" :aria-label="`${copy.nav.themeLabel}: ${themeLabel}`" :title="`${copy.nav.themeLabel}: ${themeLabel}`">
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
