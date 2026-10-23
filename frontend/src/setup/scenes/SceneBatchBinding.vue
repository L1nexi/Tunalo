<script setup lang="ts">
import { computed, ref } from "vue"
import type { Locale, PlaylistScanResult } from "@/api/profile"
import { Button } from "@/components/ui/button"
import { COPY } from "@/setup/copy"
import PlaylistPicker from "./PlaylistPicker.vue"

const props = defineProps<{
  locale: Locale
  selectedCount: number
  playlists: PlaylistScanResult["playlists"]
}>()
const emit = defineEmits<{ apply: [playlist: string] }>()
const playlist = ref("")
const copy = computed(() => COPY[props.locale].scenes)

function apply(): void {
  emit("apply", playlist.value)
  playlist.value = ""
}
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-3 rounded-lg bg-muted p-3"
    role="group"
    :aria-label="copy.batch"
  >
    <span class="text-sm font-medium">{{ copy.selected(selectedCount) }}</span>
    <div class="min-w-0 flex-1 basis-44">
      <PlaylistPicker v-model="playlist" :locale="locale" :playlists="playlists" :label="copy.batch" />
    </div>
    <Button :disabled="!playlist" @click="apply">{{ copy.applyPlaylist }}</Button>
  </div>
</template>
