<script setup lang="ts">
import { LightbulbIcon, TriangleAlertIcon } from "@lucide/vue"
import { computed, ref } from "vue"

import type { Locale, PlaylistScanResult, SceneCatalogItem, SceneId } from "@/api/profile"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Field, FieldContent, FieldError, FieldGroup, FieldLabel, FieldLegend, FieldSet } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { COPY, SCENE_LABELS } from "@/setup/copy"
import type { ProfileDraft } from "@/setup/model"

type Scenes = ProfileDraft["scenes"]

const props = defineProps<{
  locale: Locale
  mode: "setup" | "settings"
  scenes: Scenes
  rememberedScenes: Scenes
  catalog: SceneCatalogItem[]
  playlists: PlaylistScanResult["playlists"]
  catalogError: string
  valid: boolean
  attempted: boolean
  errors: string[]
}>()

const emit = defineEmits<{
  "update:scenes": [value: Scenes]
  rememberScene: [id: SceneId, playlist: string]
  retryCatalog: []
  openWallpaper: []
}>()

const copy = computed(() => COPY[props.locale])
const supportedScenes = computed(() => new Set(props.catalog.map((scene) => scene.id)))
const availablePlaylists = computed(() => new Set(props.playlists.map((playlist) => playlist.name)))
const showInactive = ref(false)
const playlistSearch = ref("")
const sceneGroups = computed(() => [
  {
    id: "context",
    title: copy.value.scenes.groups.context,
    scenes: ["day_work", "day_leisure", "night_work", "night_leisure"] as SceneId[],
  },
  {
    id: "season",
    title: copy.value.scenes.groups.season,
    scenes: ["spring", "summer", "autumn", "winter"] as SceneId[],
  },
  {
    id: "weather",
    title: copy.value.scenes.groups.weather,
    scenes: ["sunset", "rain"] as SceneId[],
  },
])
const supportedOrder = computed(() => sceneGroups.value.flatMap((group) => group.scenes).filter((id) => supportedScenes.value.has(id)))
const enabledScenes = computed(() => supportedOrder.value
  .filter((id) => id in props.scenes)
  .sort((a, b) => Number(assignmentInvalid(b)) - Number(assignmentInvalid(a))))
const inactiveScenes = computed(() => supportedOrder.value.filter((id) => !(id in props.scenes)))
const inactiveGroups = computed(() => sceneGroups.value
  .map((group) => ({ ...group, scenes: group.scenes.filter((id) => inactiveScenes.value.includes(id)) }))
  .filter((group) => group.scenes.length > 0))
const filteredPlaylists = computed(() => props.playlists.filter((playlist) =>
  playlist.name.toLocaleLowerCase().includes(playlistSearch.value.trim().toLocaleLowerCase())))

function toggleScene(sceneId: SceneId, enabled: boolean | "indeterminate"): void {
  const updated = { ...props.scenes }
  if (enabled === true) {
    updated[sceneId] ??= props.rememberedScenes[sceneId] ?? ""
  } else {
    if (updated[sceneId]) emit("rememberScene", sceneId, updated[sceneId])
    delete updated[sceneId]
  }
  emit("update:scenes", updated)
}

function setPlaylist(sceneId: SceneId, value: unknown): void {
  if (typeof value === "string") {
    emit("update:scenes", { ...props.scenes, [sceneId]: value })
    playlistSearch.value = ""
  }
}

function assignmentInvalid(sceneId: SceneId): boolean {
  return sceneId in props.scenes && !availablePlaylists.value.has(props.scenes[sceneId] ?? "")
}

function selectedPlaylistLabel(sceneId: SceneId): string {
  const name = props.scenes[sceneId]
  const playlist = props.playlists.find((item) => item.name === name)
  return playlist ? copy.value.scenes.playlistOption(playlist.name, playlist.item_count) : name ?? ""
}
</script>

<template>
  <section class="flex flex-col gap-6">
    <Alert v-if="mode === 'setup' && copy.scenes.defaultHint">
      <LightbulbIcon />
      <AlertDescription>{{ copy.scenes.defaultHint }}</AlertDescription>
    </Alert>

    <Alert v-if="catalogError" variant="destructive">
      <TriangleAlertIcon />
      <AlertDescription>{{ catalogError }}</AlertDescription>
      <Button variant="outline" size="sm" @click="emit('retryCatalog')">{{ copy.common.retry }}</Button>
    </Alert>

    <Alert v-if="playlists.length === 0" variant="destructive">
      <TriangleAlertIcon />
      <AlertDescription>{{ copy.scenes.unavailable }}</AlertDescription>
      <Button variant="outline" size="sm" @click="emit('openWallpaper')">{{ copy.wallpaper.title }}</Button>
    </Alert>

    <p class="text-sm text-muted-foreground">{{ copy.scenes.matchExplanation }}</p>

    <FieldSet v-if="enabledScenes.length">
      <FieldLegend>{{ copy.scenes.activeTitle }}</FieldLegend>
      <p v-if="enabledScenes.some(assignmentInvalid)" class="text-sm text-destructive">{{ copy.scenes.pendingBindings }}</p>
      <div v-if="playlists.length > 8" class="max-w-sm">
        <FieldLabel for="playlist-search">{{ copy.scenes.searchPlaylist }}</FieldLabel>
        <Input id="playlist-search" v-model="playlistSearch" type="search" />
      </div>
      <FieldGroup class="gap-2">
        <Field
          v-for="sceneId in enabledScenes"
          :key="sceneId"
          orientation="responsive"
          :data-invalid="attempted && assignmentInvalid(sceneId)"
          class="min-w-0 rounded-lg border p-3"
        >
          <div class="flex min-w-44 items-center gap-3">
            <Checkbox
              :id="`scene-${sceneId}`"
              :model-value="sceneId in scenes"
              :disabled="playlists.length === 0"
              @update:model-value="(value) => toggleScene(sceneId, value)"
            />
            <FieldLabel :for="`scene-${sceneId}`" class="font-normal">
              {{ SCENE_LABELS[locale][sceneId] }}
            </FieldLabel>
          </div>
          <FieldContent class="min-w-0">
            <Select
              :model-value="scenes[sceneId]"
              :disabled="!(sceneId in scenes) || playlists.length === 0"
              @update:model-value="(value) => setPlaylist(sceneId, value)"
            >
              <SelectTrigger
                class="min-w-0 w-full max-w-full"
                :aria-label="`${SCENE_LABELS[locale][sceneId]}: ${copy.scenes.playlist}`"
                :aria-invalid="attempted && assignmentInvalid(sceneId)"
                :aria-describedby="attempted && assignmentInvalid(sceneId) ? `scene-error-${sceneId}` : undefined"
                :title="scenes[sceneId] || undefined"
              >
                <SelectValue :placeholder="copy.scenes.choosePlaylist">{{ scenes[sceneId] ? selectedPlaylistLabel(sceneId) : copy.scenes.choosePlaylist }}</SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem v-for="playlist in filteredPlaylists" :key="playlist.name" :value="playlist.name">
                    {{ copy.scenes.playlistOption(playlist.name, playlist.item_count) }}
                  </SelectItem>
                  <p v-if="filteredPlaylists.length === 0" class="px-2 py-1 text-sm text-muted-foreground">{{ copy.scenes.noPlaylistMatch }}</p>
                </SelectGroup>
              </SelectContent>
            </Select>
            <FieldError
              v-if="attempted && assignmentInvalid(sceneId)"
              :id="`scene-error-${sceneId}`"
              :errors="[scenes[sceneId] ? copy.scenes.unavailablePlaylist : copy.scenes.bindingRequired]"
            />
          </FieldContent>
        </Field>
      </FieldGroup>
    </FieldSet>

    <Collapsible v-if="inactiveScenes.length" v-model:open="showInactive">
      <CollapsibleTrigger as-child>
        <Button type="button" variant="outline">{{ copy.scenes.inactiveTitle(inactiveScenes.length) }}</Button>
      </CollapsibleTrigger>
      <CollapsibleContent class="pt-4">
        <FieldSet v-for="group in inactiveGroups" :key="group.id" class="mb-4">
          <FieldLegend>{{ group.title }}</FieldLegend>
          <FieldGroup class="gap-2">
            <Field v-for="sceneId in group.scenes" :key="sceneId" class="flex items-center gap-3">
              <Checkbox
                :id="`scene-${sceneId}`"
                :model-value="false"
                :disabled="playlists.length === 0"
                @update:model-value="(value) => toggleScene(sceneId, value)"
              />
              <FieldLabel :for="`scene-${sceneId}`">{{ SCENE_LABELS[locale][sceneId] }}</FieldLabel>
            </Field>
          </FieldGroup>
        </FieldSet>
      </CollapsibleContent>
    </Collapsible>

    <FieldError
      v-if="(attempted && !valid) || errors.length"
      :errors="[
        ...(attempted && !valid ? [copy.scenes.required] : []),
        ...errors,
      ]"
    />
  </section>
</template>
