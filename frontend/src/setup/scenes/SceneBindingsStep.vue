<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, ref } from "vue"
import { PlusIcon, LayersIcon, SearchIcon, TriangleAlertIcon } from "@lucide/vue"
import type { Locale, PlaylistScanResult, SceneProfile } from "@/api/profile"
import type { SceneEditorState } from "./editorState"
import SceneBatchBinding from "./SceneBatchBinding.vue"
import SceneBindingRow from "./SceneBindingRow.vue"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { FieldError } from "@/components/ui/field"
import { InputGroup, InputGroupInput, InputGroupAddon } from "@/components/ui/input-group"
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
  EmptyMedia,
  EmptyContent,
} from "@/components/ui/empty"
import { COPY, associationSummary } from "@/setup/copy"

const SceneEditor = defineAsyncComponent(() => import("./SceneEditor.vue"))

const props = defineProps<{
  locale: Locale
  scenes: Record<string, SceneProfile>
  playlists: PlaylistScanResult["playlists"]
  valid: boolean
  attempted: boolean
  errors: string[]
}>()
const emit = defineEmits<{
  "update:scenes": [scenes: Record<string, SceneProfile>]
  removeScene: [id: string]
  openWallpaper: []
}>()
const copy = computed(() => COPY[props.locale].scenes)
const shared = computed(() => COPY[props.locale])
const editing = ref<SceneEditorState | null>(null)
const search = ref("")
const selected = ref<string[]>([])
const entries = computed(() => Object.entries(props.scenes))
const playlistNames = computed(() => new Set(props.playlists.map((playlist) => playlist.name)))
const pending = computed(
  () => entries.value.filter(([, scene]) => !playlistNames.value.has(scene.playlist)).length,
)
const visible = computed(() => {
  const query = search.value.trim().toLocaleLowerCase()
  return entries.value.filter(([, scene]) =>
    `${scene.name} ${scene.playlist} ${associationSummary(scene.associations, props.locale)}`
      .toLocaleLowerCase()
      .includes(query),
  )
})
const allSelected = computed(
  () => visible.value.length > 0 && visible.value.every(([id]) => selected.value.includes(id)),
)
const someSelected = computed(() => visible.value.some(([id]) => selected.value.includes(id)))

function setPlaylist(id: string, playlist: string): void {
  emit("update:scenes", { ...props.scenes, [id]: { ...props.scenes[id]!, playlist } })
}
function toggle(id: string, checked: boolean | "indeterminate"): void {
  selected.value = checked === true ? [...selected.value, id] : selected.value.filter((value) => value !== id)
}
function toggleAll(checked: boolean | "indeterminate"): void {
  const ids = new Set(visible.value.map(([id]) => id))
  selected.value =
    checked === true ? [...new Set([...selected.value, ...ids])] : selected.value.filter((id) => !ids.has(id))
}
function bindSelected(playlist: string): void {
  emit(
    "update:scenes",
    Object.fromEntries(
      entries.value.map(([id, scene]) => [id, selected.value.includes(id) ? { ...scene, playlist } : scene]),
    ),
  )
  selected.value = []
}
function saveScenes(scenes: SceneProfile[]): void {
  const state = editing.value!
  const changes = Object.fromEntries(
    scenes.map((scene) => [state.kind === "edit" ? state.id : crypto.randomUUID(), scene]),
  )
  emit("update:scenes", { ...props.scenes, ...changes })
  search.value = ""
  editing.value = null
}
async function removeScene(id: string): Promise<void> {
  const index = visible.value.findIndex(([sceneId]) => sceneId === id)
  const next = visible.value[index + 1] ?? visible.value[index - 1]
  emit("removeScene", id)
  selected.value = selected.value.filter((value) => value !== id)
  await nextTick()
  document.getElementById(next ? `edit-scene-${next[0]}` : "add-scene-presets")?.focus()
}
</script>

<template>
  <section class="flex flex-col gap-5">
    <Alert v-if="!playlists.length" variant="destructive">
      <TriangleAlertIcon /><AlertDescription>{{ shared.scenes.unavailable }}</AlertDescription>
      <Button variant="outline" size="sm" @click="emit('openWallpaper')">{{ shared.wallpaper.title }}</Button>
    </Alert>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2" aria-live="polite">
        <h2 class="text-base font-semibold">{{ copy.count(entries.length) }}</h2>
        <Badge v-if="pending" variant="outline">{{ copy.pending(pending) }}</Badge>
        <span v-else-if="entries.length" class="text-xs text-muted-foreground">{{ copy.allBound }}</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button id="add-scene-presets" @click="editing = { kind: 'presets' }"
          ><LayersIcon data-icon="inline-start" />{{ copy.addPresets }}</Button
        >
        <Button variant="outline" @click="editing = { kind: 'create' }"
          ><PlusIcon data-icon="inline-start" />{{ copy.create }}</Button
        >
      </div>
    </div>
    <Empty v-if="!entries.length" class="border py-12">
      <EmptyHeader
        ><EmptyMedia variant="icon"><LayersIcon /></EmptyMedia><EmptyTitle>{{ copy.emptyTitle }}</EmptyTitle
        ><EmptyDescription>{{ copy.emptyHelp }}</EmptyDescription></EmptyHeader
      >
    </Empty>
    <template v-else>
      <div class="flex items-center gap-3">
        <Checkbox
          :aria-label="copy.selectAll"
          :model-value="allSelected ? true : someSelected ? 'indeterminate' : false"
          @update:model-value="toggleAll"
        />
        <InputGroup class="max-w-sm"
          ><InputGroupAddon><SearchIcon /></InputGroupAddon
          ><InputGroupInput v-model="search" :aria-label="copy.search" :placeholder="copy.search"
        /></InputGroup>
        <Button v-if="selected.length" variant="ghost" size="sm" @click="selected = []">{{
          copy.clearSelection
        }}</Button>
      </div>
      <SceneBatchBinding
        v-show="selected.length"
        :locale="locale"
        :selected-count="selected.length"
        :playlists="playlists"
        @apply="bindSelected"
      />
      <div v-if="visible.length" class="divide-y rounded-lg border px-4" :aria-label="copy.list">
        <SceneBindingRow
          v-for="[id, scene] in visible"
          :key="id"
          :id="id"
          :locale="locale"
          :scene="scene"
          :playlists="playlists"
          :selected="selected.includes(id)"
          :attempted="attempted"
          @select="toggle(id, $event)"
          @playlist="setPlaylist(id, $event)"
          @edit="editing = { kind: 'edit', id }"
          @remove="removeScene(id)"
        />
      </div>
      <Empty v-else
        ><EmptyHeader
          ><EmptyTitle>{{ copy.noMatch }}</EmptyTitle></EmptyHeader
        ><EmptyContent
          ><Button variant="outline" @click="search = ''">{{ copy.clearSearch }}</Button></EmptyContent
        ></Empty
      >
    </template>
    <p v-if="entries.length" class="text-xs leading-relaxed text-muted-foreground">
      {{ shared.scenes.matchExplanation }}
    </p>
    <FieldError
      v-if="(attempted && !valid) || errors.length"
      :errors="[...(attempted && !valid ? [shared.scenes.required] : []), ...errors]"
    />
    <SceneEditor
      v-if="editing !== null"
      :locale="locale"
      :state="editing"
      :scenes="scenes"
      :playlists="playlists"
      @close="editing = null"
      @save="saveScenes"
    />
  </section>
</template>
