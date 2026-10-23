<script setup lang="ts">
import { CheckIcon } from "@lucide/vue"
import { computed, nextTick, ref } from "vue"

import type { ContextVariable, Locale, PlaylistScanResult, SceneProfile, SemanticItem } from "@/api/profile"
import PlaylistPicker from "./PlaylistPicker.vue"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Field,
  FieldContent,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
  FieldTitle,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { COPY, associationSummary } from "@/setup/copy"
import { copyScene } from "@/setup/model"
import { PRESET_SECTIONS, SCENE_PRESETS } from "@/setup/scenePresets"
import type { ScenePreset, ScenePresetGroup, ScenePresetId } from "@/setup/scenePresets"
import { SCENE_ITEMS, SCENE_VARIABLES, associationKey } from "@/setup/scenes"
import type { SceneEditorState } from "@/setup/scenes"

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
const isEdit = props.state.kind === "edit"
const title = computed(() => (isPreset ? copy.value.presets : isEdit ? copy.value.edit : copy.value.create))
const group = ref<ScenePresetGroup>("season")
const selected = ref<ScenePresetId[]>([])
const presetPlaylist = ref("")
const presets = computed(() => SCENE_PRESETS[group.value])
const existing = computed(
  () => new Set(Object.values(props.scenes).map((scene) => associationKey(scene.associations))),
)
const selectable = computed(() => presets.value.filter((preset) => !isAdded(preset)))
const allSelected = computed(
  () => selectable.value.length > 0 && selectable.value.every((preset) => selected.value.includes(preset.id)),
)

const draft = ref<SceneProfile>(
  props.state.kind === "edit"
    ? copyScene(props.scenes[props.state.id]!)
    : { name: "", associations: {}, playlist: "" },
)
const nameEdited = ref(isEdit)
const attempted = ref(false)
const summary = computed(() => associationSummary(draft.value.associations, props.locale))

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

function updateName(value: string | number): void {
  draft.value.name = String(value)
  nameEdited.value = true
}

function setItems(variable: ContextVariable, value: unknown): void {
  const items = value as SemanticItem[]
  if (items.length) draft.value.associations[variable] = items
  else delete draft.value.associations[variable]
  if (!nameEdited.value) draft.value.name = summary.value
}

async function save(): Promise<void> {
  if (isPreset) {
    emit(
      "save",
      Object.values(SCENE_PRESETS)
        .flat()
        .filter((preset) => selected.value.includes(preset.id))
        .map((preset) =>
          copyScene({
            name: copy.value.presetNames[preset.id],
            associations: preset.associations,
            playlist: presetPlaylist.value,
          }),
        ),
    )
    return
  }
  attempted.value = true
  if (!draft.value.name.trim() || !summary.value) {
    await nextTick()
    document.getElementById(!draft.value.name.trim() ? "scene-name" : "scene-associations-error")?.focus()
    return
  }
  emit("save", [{ ...draft.value, name: draft.value.name.trim() }])
}

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
      <form
        id="scene-editor-form"
        class="min-h-0 overflow-y-auto overscroll-contain px-5 py-5 sm:px-6"
        @submit.prevent="save"
      >
        <FieldGroup v-if="isPreset">
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
              <Button
                type="button"
                variant="ghost"
                size="sm"
                :disabled="!selectable.length"
                @click="selectGroup"
              >
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
          <Field>
            <FieldLabel
              >{{ copy.batchPlaylist }}
              <span class="text-muted-foreground">{{ copy.optional }}</span></FieldLabel
            >
            <PlaylistPicker
              v-model="presetPlaylist"
              :locale="locale"
              :playlists="playlists"
              :label="copy.batchPlaylist"
              :placeholder="copy.later"
            />
            <Button
              v-if="presetPlaylist"
              type="button"
              variant="ghost"
              size="sm"
              class="self-start"
              @click="presetPlaylist = ''"
              >{{ copy.chooseLater }}</Button
            >
          </Field>
        </FieldGroup>

        <FieldGroup v-else>
          <Field :data-invalid="(attempted && !draft.name.trim()) || undefined">
            <FieldLabel for="scene-name">{{ copy.name }}</FieldLabel>
            <Input
              id="scene-name"
              :model-value="draft.name"
              :placeholder="copy.namePlaceholder"
              :aria-invalid="attempted && !draft.name.trim()"
              :aria-describedby="attempted && !draft.name.trim() ? 'scene-name-error' : undefined"
              @update:model-value="updateName"
            />
            <FieldError
              v-if="attempted && !draft.name.trim()"
              id="scene-name-error"
              :errors="[copy.requiredName]"
            />
          </Field>
          <FieldSet class="block" :data-invalid="(attempted && !summary) || undefined">
            <FieldLegend>{{ copy.association }}</FieldLegend>
            <FieldGroup>
              <FieldDescription>{{ copy.associationHelp }}</FieldDescription>
              <FieldGroup class="grid gap-5 sm:grid-cols-2">
                <Field v-for="variable in SCENE_VARIABLES" :key="variable">
                  <div class="flex items-center justify-between gap-3">
                    <FieldLabel :id="`scene-${variable}-label`">{{ copy.groups[variable] }}</FieldLabel>
                    <span
                      v-if="!draft.associations[variable]?.length"
                      class="text-xs text-muted-foreground"
                      >{{ copy.unassociated }}</span
                    >
                  </div>
                  <ToggleGroup
                    type="multiple"
                    variant="outline"
                    :spacing="2"
                    class="flex-wrap"
                    :aria-labelledby="`scene-${variable}-label`"
                    :aria-invalid="attempted && !summary"
                    :model-value="draft.associations[variable] ?? []"
                    @update:model-value="setItems(variable, $event)"
                  >
                    <ToggleGroupItem v-for="item in SCENE_ITEMS[variable]" :key="item" :value="item">
                      <CheckIcon
                        v-if="draft.associations[variable]?.includes(item)"
                        data-icon="inline-start"
                      />
                      {{ copy.semanticLabels[item] }}
                    </ToggleGroupItem>
                  </ToggleGroup>
                </Field>
              </FieldGroup>
              <FieldError
                v-if="attempted && !summary"
                id="scene-associations-error"
                tabindex="-1"
                :errors="[copy.requiredAssociation]"
              />
              <FieldDescription v-if="summary" aria-live="polite">{{ summary }}</FieldDescription>
            </FieldGroup>
          </FieldSet>
          <Separator />
          <Field>
            <FieldLabel
              >{{ copy.playlist }} <span class="text-muted-foreground">{{ copy.optional }}</span></FieldLabel
            >
            <PlaylistPicker
              v-model="draft.playlist"
              :locale="locale"
              :playlists="playlists"
              :label="copy.playlist"
              :placeholder="copy.later"
            />
            <Button
              v-if="draft.playlist"
              type="button"
              variant="ghost"
              size="sm"
              class="self-start"
              @click="draft.playlist = ''"
              >{{ copy.chooseLater }}</Button
            >
          </Field>
        </FieldGroup>
      </form>
      <Separator />
      <DialogFooter class="shrink-0 flex-row flex-wrap items-center gap-2 px-5 py-4 sm:px-6">
        <span v-if="isPreset" class="mr-auto text-sm text-muted-foreground" aria-live="polite">{{
          copy.selected(selected.length)
        }}</span>
        <Button type="button" variant="outline" @click="emit('close')">{{ copy.cancel }}</Button>
        <Button type="submit" form="scene-editor-form" :disabled="isPreset && !selected.length">
          {{ isPreset ? copy.addSelected(selected.length) : isEdit ? copy.done : copy.add }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
