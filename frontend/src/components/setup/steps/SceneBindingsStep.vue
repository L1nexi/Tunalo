<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, ref } from "vue"
import { PencilIcon, PlusIcon, Trash2Icon, LayersIcon, SearchIcon, TriangleAlertIcon } from "@lucide/vue"
import type { Locale, PlaylistScanResult, SceneProfile } from "@/api/profile"
import type { SceneEditorState } from "@/setup/scenes"
import PlaylistPicker from "../PlaylistPicker.vue"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Field, FieldError } from "@/components/ui/field"
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

const SceneEditor = defineAsyncComponent(() => import("../SceneEditor.vue"))

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
const batchPlaylist = ref("")
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
function bindSelected(): void {
  emit(
    "update:scenes",
    Object.fromEntries(
      entries.value.map(([id, scene]) => [
        id,
        selected.value.includes(id) ? { ...scene, playlist: batchPlaylist.value } : scene,
      ]),
    ),
  )
  selected.value = []
  batchPlaylist.value = ""
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
      <div
        v-if="selected.length"
        class="flex flex-wrap items-center gap-3 rounded-lg bg-muted p-3"
        role="group"
        :aria-label="copy.batch"
      >
        <span class="text-sm font-medium">{{ copy.selected(selected.length) }}</span>
        <div class="min-w-0 flex-1 basis-44">
          <PlaylistPicker
            v-model="batchPlaylist"
            :locale="locale"
            :playlists="playlists"
            :label="copy.batch"
          />
        </div>
        <Button :disabled="!batchPlaylist" @click="bindSelected">{{ copy.applyPlaylist }}</Button>
      </div>
      <div v-if="visible.length" class="divide-y rounded-lg border px-4" :aria-label="copy.list">
        <div
          v-for="[id, scene] in visible"
          :key="id"
          class="grid min-w-0 grid-cols-[minmax(0,1fr)_auto] items-start gap-x-3 gap-y-3 py-4 lg:grid-cols-[minmax(0,1fr)_13rem_auto]"
          role="group"
          :aria-label="scene.name"
        >
          <div class="flex min-w-0 items-start gap-3">
            <Checkbox
              class="mt-1"
              :aria-label="`${copy.selectedScenes}: ${scene.name}`"
              :model-value="selected.includes(id)"
              @update:model-value="toggle(id, $event)"
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
            :data-invalid="(attempted && !playlistNames.has(scene.playlist)) || undefined"
          >
            <PlaylistPicker
              :model-value="scene.playlist"
              :locale="locale"
              :playlists="playlists"
              :label="`${scene.name}: ${shared.scenes.playlist}`"
              :invalid="attempted && !playlistNames.has(scene.playlist)"
              :describedby="attempted && !playlistNames.has(scene.playlist) ? `binding-${id}` : undefined"
              @update:model-value="setPlaylist(id, $event)"
            />
            <p v-if="playlistNames.has(scene.playlist)" class="text-xs text-muted-foreground">
              {{
                shared.scenes.playlistCount(
                  playlists.find((playlist) => playlist.name === scene.playlist)!.item_count,
                )
              }}
            </p>
            <FieldError
              v-if="attempted && !playlistNames.has(scene.playlist)"
              :id="`binding-${id}`"
              :errors="[scene.playlist ? shared.scenes.unavailablePlaylist : shared.scenes.bindingRequired]"
            />
          </Field>
          <div class="col-start-2 row-start-1 flex gap-1 lg:col-start-3">
            <Button
              variant="ghost"
              size="icon-sm"
              :id="`edit-scene-${id}`"
              :aria-label="`${copy.edit}: ${scene.name}`"
              :title="copy.edit"
              @click="editing = { kind: 'edit', id }"
              ><PencilIcon
            /></Button>
            <Button
              variant="ghost"
              size="icon-sm"
              :aria-label="`${copy.remove}: ${scene.name}`"
              :title="copy.remove"
              @click="removeScene(id)"
              ><Trash2Icon
            /></Button>
          </div>
        </div>
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
