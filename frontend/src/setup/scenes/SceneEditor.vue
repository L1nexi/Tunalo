<script setup lang="ts">
import { computed } from "vue"
import type { Locale, PlaylistScanResult, SceneProfile } from "@/api/profile"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Separator } from "@/components/ui/separator"
import { COPY } from "@/setup/copy"
import type { SceneEditorState } from "./editorState"
import SceneDetailsForm from "./SceneDetailsForm.vue"
import ScenePresetForm from "./ScenePresetForm.vue"

const props = defineProps<{
  locale: Locale
  state: SceneEditorState
  scenes: Record<string, SceneProfile>
  playlists: PlaylistScanResult["playlists"]
}>()
const emit = defineEmits<{ close: []; save: [scenes: SceneProfile[]] }>()
const returnFocus = document.activeElement as HTMLElement
const copy = computed(() => COPY[props.locale].scenes)
const isPreset = props.state.kind === "presets"
const title = computed(() =>
  isPreset ? copy.value.presets : props.state.kind === "edit" ? copy.value.edit : copy.value.create,
)

function restoreFocus(event: Event): void {
  event.preventDefault()
  returnFocus?.focus()
}
</script>

<template>
  <Dialog :open="true" @update:open="emit('close')">
    <DialogContent
      :show-close-button="false"
      class="flex max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] flex-col gap-0 overflow-hidden p-0 sm:max-w-2xl"
      @interact-outside.prevent
      @close-auto-focus="restoreFocus"
    >
      <DialogHeader class="shrink-0 px-5 py-4 sm:px-6">
        <DialogTitle>{{ title }}</DialogTitle>
        <DialogDescription>{{ isPreset ? copy.presetsHelp : copy.editHint }}</DialogDescription>
      </DialogHeader>
      <Separator />
      <ScenePresetForm
        v-if="isPreset"
        :locale="locale"
        :scenes="scenes"
        :playlists="playlists"
        @cancel="emit('close')"
        @save="emit('save', $event)"
      />
      <SceneDetailsForm
        v-else
        :locale="locale"
        :scene="state.kind === 'edit' ? scenes[state.id]! : null"
        :playlists="playlists"
        @cancel="emit('close')"
        @save="emit('save', [$event])"
      />
    </DialogContent>
  </Dialog>
</template>
