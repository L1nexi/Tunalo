<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue"
import type { Locale, PlaylistScanResult, SceneProfile } from "@/api/profile"
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
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { COPY } from "@/setup/copy"
import { useSetupEditor } from "@/setup/workspace/useSetupWorkspace"
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
const { pendingSceneChanges } = useSetupEditor()
const discardDialogOpen = ref(false)
const discardConfirmed = ref(false)
let editorFocus: HTMLElement | null = null
const returnFocus = document.activeElement as HTMLElement
const copy = computed(() => COPY[props.locale].scenes)
const navCopy = computed(() => COPY[props.locale].nav)
const isPreset = props.state.kind === "presets"
const title = computed(() =>
  isPreset ? copy.value.presets : props.state.kind === "edit" ? copy.value.edit : copy.value.create,
)

function requestClose(): void {
  if (pendingSceneChanges.value) {
    editorFocus = document.activeElement as HTMLElement
    discardConfirmed.value = false
    discardDialogOpen.value = true
  } else emit("close")
}

function finishDiscard(event: Event): void {
  event.preventDefault()
  if (discardConfirmed.value) emit("close")
  else editorFocus?.focus()
}

onBeforeUnmount(() => { pendingSceneChanges.value = false })

function restoreFocus(event: Event): void {
  event.preventDefault()
  returnFocus?.focus()
}
</script>

<template>
  <Dialog :open="true" @update:open="requestClose">
    <DialogContent
      :show-close-button="false"
      class="flex max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] flex-col gap-0 overflow-hidden p-0 sm:max-w-2xl"
      @interact-outside.prevent
      @close-auto-focus="restoreFocus"
    >
      <DialogHeader class="shrink-0 px-5 py-4 sm:px-6">
        <DialogTitle>{{ title }}</DialogTitle>
        <DialogDescription>{{ isPreset ? copy.presetsHelp : copy.associationHelp }}</DialogDescription>
      </DialogHeader>
      <ScenePresetForm
        v-if="isPreset"
        :locale="locale"
        :scenes="scenes"
        :playlists="playlists"
        @dirty="pendingSceneChanges = $event"
        @cancel="emit('close')"
        @save="emit('save', $event)"
      />
      <SceneDetailsForm
        v-else
        :locale="locale"
        :scene="state.kind === 'edit' ? scenes[state.id]! : null"
        :playlists="playlists"
        @dirty="pendingSceneChanges = $event"
        @cancel="emit('close')"
        @save="emit('save', [$event])"
      />
    </DialogContent>
  </Dialog>
  <AlertDialog v-model:open="discardDialogOpen">
    <AlertDialogContent @close-auto-focus="finishDiscard">
      <AlertDialogHeader>
        <AlertDialogTitle>{{ copy.discardTitle }}</AlertDialogTitle>
        <AlertDialogDescription>{{ copy.discardDescription }}</AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>{{ navCopy.keepEditing }}</AlertDialogCancel>
        <AlertDialogAction @click="discardConfirmed = true">{{ navCopy.discardChanges }}</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>
