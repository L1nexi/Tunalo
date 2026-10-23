<script setup lang="ts">
import { PencilIcon, Trash2Icon } from "@lucide/vue"
import { computed } from "vue"
import type { Locale, PlaylistScanResult, SceneProfile } from "@/api/profile"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Field, FieldError } from "@/components/ui/field"
import { COPY, associationSummary } from "@/setup/copy"
import PlaylistPicker from "../PlaylistPicker.vue"

const props = defineProps<{
  id: string
  locale: Locale
  scene: SceneProfile
  playlists: PlaylistScanResult["playlists"]
  selected: boolean
  attempted: boolean
}>()
const emit = defineEmits<{
  select: [checked: boolean | "indeterminate"]
  playlist: [name: string]
  edit: []
  remove: []
}>()
const copy = computed(() => COPY[props.locale].scenes)
const playlist = computed(() => props.playlists.find((entry) => entry.name === props.scene.playlist))
const invalid = computed(() => props.attempted && !playlist.value)
</script>

<template>
  <div
    class="grid min-w-0 grid-cols-[minmax(0,1fr)_auto] items-start gap-x-3 gap-y-3 py-4 lg:grid-cols-[minmax(0,1fr)_13rem_auto]"
    role="group"
    :aria-label="scene.name"
  >
    <div class="flex min-w-0 items-start gap-3">
      <Checkbox
        class="mt-1"
        :aria-label="`${copy.selectedScenes}: ${scene.name}`"
        :model-value="selected"
        @update:model-value="emit('select', $event)"
      />
      <div class="flex min-w-0 flex-col gap-1.5">
        <p class="break-words text-sm font-medium">{{ scene.name }}</p>
        <p class="text-xs leading-relaxed text-muted-foreground">
          {{ associationSummary(scene.associations, locale) }}
        </p>
      </div>
    </div>
    <Field
      class="col-span-2 row-start-2 gap-1.5 lg:col-span-1 lg:row-start-auto"
      :data-invalid="invalid || undefined"
    >
      <PlaylistPicker
        :model-value="scene.playlist"
        :locale="locale"
        :playlists="playlists"
        :label="`${scene.name}: ${copy.playlist}`"
        :invalid="invalid"
        :describedby="invalid ? `binding-${id}` : undefined"
        @update:model-value="emit('playlist', $event)"
      />
      <p v-if="playlist" class="text-xs text-muted-foreground">
        {{ copy.playlistCount(playlist.item_count) }}
      </p>
      <FieldError
        v-if="invalid"
        :id="`binding-${id}`"
        :errors="[scene.playlist ? copy.unavailablePlaylist : copy.bindingRequired]"
      />
    </Field>
    <div class="col-start-2 row-start-1 flex gap-1 lg:col-start-3">
      <Button
        :id="`edit-scene-${id}`"
        variant="ghost"
        size="icon-sm"
        :aria-label="`${copy.edit}: ${scene.name}`"
        :title="copy.edit"
        @click="emit('edit')"
        ><PencilIcon
      /></Button>
      <Button
        variant="ghost"
        size="icon-sm"
        :aria-label="`${copy.remove}: ${scene.name}`"
        :title="copy.remove"
        @click="emit('remove')"
        ><Trash2Icon
      /></Button>
    </div>
  </div>
</template>
