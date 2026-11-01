<script setup lang="ts">
import { FolderOpenIcon, RefreshCwIcon, TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale, PlaylistScanResult } from "@/api/profile"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput } from "@/components/ui/input-group"
import { Spinner } from "@/components/ui/spinner"
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { COPY } from "@/setup/copy"
import type { ScanStatus } from "./usePlaylistScan"

const props = defineProps<{
  locale: Locale
  path: string
  status: ScanStatus
  detail: string
  playlists: PlaylistScanResult["playlists"]
  usableCount: number
  nativeBridge: boolean
  invalid: boolean
  errors: string[]
}>()

const emit = defineEmits<{
  "update:path": [value: string]
  scan: []
  choose: []
}>()

const copy = computed(() => COPY[props.locale])
</script>

<template>
  <section class="flex flex-col gap-6">
    <FieldGroup>
      <Field :data-invalid="invalid || errors.length > 0">
        <FieldLabel for="wallpaper-engine-path">{{ copy.wallpaper.pathLabel }}</FieldLabel>
        <div class="flex flex-wrap items-start gap-2">
          <InputGroup class="min-w-0 flex-1 basis-80">
            <InputGroupInput
              id="wallpaper-engine-path"
              :model-value="path"
              :placeholder="copy.wallpaper.pathPlaceholder"
              :aria-invalid="invalid || errors.length > 0"
              :aria-describedby="invalid || errors.length ? 'wallpaper-path-error' : !path.trim() ? 'wallpaper-path-help' : undefined"
              @update:model-value="(value: string | number) => emit('update:path', String(value))"
            />
            <InputGroupAddon v-if="nativeBridge" align="inline-end">
              <InputGroupButton :aria-label="copy.wallpaper.choose" @click="emit('choose')">
                <FolderOpenIcon />
                <span>{{ copy.wallpaper.choose }}</span>
              </InputGroupButton>
            </InputGroupAddon>
          </InputGroup>
          <Button variant="outline" class="shrink-0" :disabled="status === 'loading'" @click="emit('scan')">
            <Spinner v-if="status === 'loading'" data-icon="inline-start" />
            <RefreshCwIcon v-else data-icon="inline-start" />
            {{ status === "loading" ? copy.wallpaper.scanning : status === "empty" ? copy.wallpaper.scanAgain : path ? copy.wallpaper.scan : copy.wallpaper.detect }}
          </Button>
        </div>
        <FieldDescription v-if="!path.trim()" id="wallpaper-path-help">{{ copy.wallpaper.pathDescription }}</FieldDescription>
        <FieldError v-if="invalid || errors.length" id="wallpaper-path-error" :errors="[...(invalid ? [copy.wallpaper.scanRequired] : []), ...errors]" />
      </Field>
    </FieldGroup>

    <Alert v-if="status === 'error'" variant="destructive">
      <TriangleAlertIcon />
      <AlertTitle>{{ copy.wallpaper.emptyTitle }}</AlertTitle>
      <AlertDescription>{{ detail }}</AlertDescription>
    </Alert>

    <Empty v-else-if="status === 'empty'">
      <EmptyHeader>
        <EmptyTitle>{{ copy.wallpaper.emptyTitle }}</EmptyTitle>
        <EmptyDescription>{{ copy.wallpaper.emptyDescription }}</EmptyDescription>
      </EmptyHeader>
    </Empty>

    <div v-else-if="status === 'success'" class="flex flex-col gap-4">
      <p class="text-sm text-muted-foreground" role="status">{{ copy.wallpaper.foundDescription(usableCount) }}</p>
      <div>
        <Table class="table-fixed">
          <TableCaption class="sr-only">{{ copy.wallpaper.scanResultsLabel }}</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>{{ copy.wallpaper.playlistName }}</TableHead>
              <TableHead class="w-28 text-right">{{ copy.wallpaper.wallpaperCount }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="playlist in playlists" :key="playlist.name">
              <TableCell class="min-w-0">
                <span class="block truncate font-medium" :title="playlist.name">{{ playlist.name }}</span>
              </TableCell>
              <TableCell class="text-right tabular-nums" :class="playlist.item_count > 0 ? 'text-foreground' : 'text-muted-foreground'">
                {{ playlist.item_count > 0 ? copy.wallpaper.itemCount(playlist.item_count) : copy.wallpaper.zeroItem }}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
      <p class="text-sm text-muted-foreground">{{ copy.wallpaper.englishNames }}</p>
    </div>
  </section>
</template>
