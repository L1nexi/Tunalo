<script setup lang="ts">
import { computed, ref } from "vue"
import type { Locale, PlaylistScanResult, SceneProfile } from "@/api/profile"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { DialogFooter } from "@/components/ui/dialog"
import {
  Field,
  FieldContent,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
  FieldTitle,
} from "@/components/ui/field"
import { Separator } from "@/components/ui/separator"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { COPY, associationSummary } from "@/setup/copy"
import { copyScene } from "@/setup/profile/model"
import { PRESET_SECTIONS, SCENE_PRESETS } from "./presets"
import type { ScenePreset, ScenePresetGroup, ScenePresetId } from "./presets"
import { associationKey } from "./associations"
import ScenePlaylistField from "./ScenePlaylistField.vue"

const props = defineProps<{
  locale: Locale
  scenes: Record<string, SceneProfile>
  playlists: PlaylistScanResult["playlists"]
}>()
const emit = defineEmits<{ cancel: []; save: [scenes: SceneProfile[]] }>()
const copy = computed(() => COPY[props.locale].scenes)
const group = ref<ScenePresetGroup>("season")
const selected = ref<ScenePresetId[]>([])
const playlist = ref("")
const presets = computed(() => SCENE_PRESETS[group.value])
const existing = computed(
  () => new Set(Object.values(props.scenes).map((scene) => associationKey(scene.associations))),
)
const selectable = computed(() => presets.value.filter((preset) => !isAdded(preset)))
const allSelected = computed(
  () => selectable.value.length > 0 && selectable.value.every((preset) => selected.value.includes(preset.id)),
)

function isAdded(preset: ScenePreset): boolean {
  return existing.value.has(associationKey(preset.associations))
}

function selectPreset(id: ScenePresetId, checked: boolean | "indeterminate"): void {
  selected.value = checked === true ? [...selected.value, id] : selected.value.filter((value) => value !== id)
}

function selectGroup(): void {
  const ids = selectable.value.map((preset) => preset.id)
  selected.value = allSelected.value
    ? selected.value.filter((id) => !ids.includes(id))
    : [...new Set([...selected.value, ...ids])]
}

function setGroup(value: unknown): void {
  if (value) group.value = value as ScenePresetGroup
}

function save(): void {
  emit(
    "save",
    Object.values(SCENE_PRESETS)
      .flat()
      .filter((preset) => selected.value.includes(preset.id))
      .map((preset) =>
        copyScene({
          name: copy.value.presetNames[preset.id],
          associations: preset.associations,
          playlist: playlist.value,
        }),
      ),
  )
}
</script>

<template>
  <form
    id="scene-editor-form"
    class="min-h-0 overflow-y-auto overscroll-contain px-5 py-5 sm:px-6"
    @submit.prevent="save"
  >
    <FieldGroup>
      <div class="grid gap-5 sm:grid-cols-2">
        <FieldSet v-for="section in PRESET_SECTIONS" :key="section.id" class="gap-2">
          <FieldLegend :id="`preset-section-${section.id}`" variant="label">{{
            copy.sections[section.id]
          }}</FieldLegend>
          <ToggleGroup
            type="single"
            variant="outline"
            :spacing="2"
            class="flex-wrap"
            :model-value="group"
            :aria-labelledby="`preset-section-${section.id}`"
            @update:model-value="setGroup"
          >
            <ToggleGroupItem v-for="id in section.groups" :key="id" :value="id">{{
              copy.groups[id]
            }}</ToggleGroupItem>
          </ToggleGroup>
        </FieldSet>
      </div>
      <FieldSet class="gap-3">
        <FieldLegend class="sr-only">{{ copy.groups[group] }}</FieldLegend>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <FieldDescription>{{ copy.groupHelp[group] }}</FieldDescription>
          <Button type="button" variant="ghost" size="sm" :disabled="!selectable.length" @click="selectGroup">
            {{ allSelected ? copy.deselectGroup : copy.selectGroup }}
          </Button>
        </div>
        <FieldGroup class="grid gap-3 sm:grid-cols-2">
          <FieldLabel v-for="preset in presets" :key="preset.id" :for="`preset-${preset.id}`">
            <Field orientation="horizontal" :data-disabled="isAdded(preset) || undefined">
              <Checkbox
                :id="`preset-${preset.id}`"
                :aria-label="copy.presetNames[preset.id]"
                :model-value="selected.includes(preset.id) || isAdded(preset)"
                :disabled="isAdded(preset)"
                @update:model-value="selectPreset(preset.id, $event)"
              />
              <FieldContent>
                <FieldTitle>{{ copy.presetNames[preset.id] }}</FieldTitle>
                <FieldDescription
                  v-if="associationSummary(preset.associations, locale) !== copy.presetNames[preset.id]"
                >
                  {{ associationSummary(preset.associations, locale) }}
                </FieldDescription>
                <Badge v-if="isAdded(preset)" variant="secondary">{{ copy.alreadyAdded }}</Badge>
              </FieldContent>
            </Field>
          </FieldLabel>
        </FieldGroup>
      </FieldSet>
      <Separator />
      <ScenePlaylistField
        v-model="playlist"
        :locale="locale"
        :playlists="playlists"
        :label="copy.batchPlaylist"
      />
    </FieldGroup>
  </form>
  <Separator />
  <DialogFooter class="shrink-0 flex-row flex-wrap items-center gap-2 px-5 py-4 sm:px-6">
    <span class="mr-auto text-sm text-muted-foreground" aria-live="polite">{{
      copy.selected(selected.length)
    }}</span>
    <Button type="button" variant="outline" @click="emit('cancel')">{{ copy.cancel }}</Button>
    <Button type="submit" form="scene-editor-form" :disabled="!selected.length">{{
      copy.addSelected(selected.length)
    }}</Button>
  </DialogFooter>
</template>
