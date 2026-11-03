<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue"
import type { ContextVariable, Locale, PlaylistScanResult, SceneProfile, SemanticItem } from "@/api/profile"
import { Button } from "@/components/ui/button"
import { DialogFooter } from "@/components/ui/dialog"
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { COPY, associationSummary } from "@/setup/copy"
import { copyScene, sceneFingerprint } from "@/setup/profile/model"
import { SCENE_ITEMS, SCENE_VARIABLES } from "./associations"
import ScenePlaylistField from "./ScenePlaylistField.vue"

const props = defineProps<{
  locale: Locale
  scene: SceneProfile | null
  playlists: PlaylistScanResult["playlists"]
}>()
const emit = defineEmits<{ cancel: []; save: [scene: SceneProfile]; dirty: [changed: boolean] }>()
const copy = computed(() => COPY[props.locale].scenes)
const draft = ref<SceneProfile>(
  props.scene === null ? { name: "", associations: {}, playlist: "" } : copyScene(props.scene),
)
const nameEdited = ref(props.scene !== null)
const attempted = ref(false)
const summary = computed(() => associationSummary(draft.value.associations, props.locale))
const baseline = sceneFingerprint({ scene: draft.value })

watch(
  () => sceneFingerprint({ scene: draft.value }) !== baseline,
  (changed) => emit("dirty", changed),
  { immediate: true },
)

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
  attempted.value = true
  if (!draft.value.name.trim() || !summary.value) {
    await nextTick()
    document.getElementById(!draft.value.name.trim() ? "scene-name" : "scene-associations-error")?.focus()
    return
  }
  emit("save", { ...draft.value, name: draft.value.name.trim() })
}
</script>

<template>
  <form
    id="scene-editor-form"
    class="min-h-0 overflow-y-auto overscroll-contain px-5 py-5 sm:px-6"
    @submit.prevent="save"
  >
    <FieldGroup>
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
      <FieldSet class="relative block" :data-invalid="(attempted && !summary) || undefined">
        <FieldLegend class="sr-only">{{ copy.association }}</FieldLegend>
        <FieldGroup>
          <FieldGroup class="grid gap-5 sm:grid-cols-2">
            <Field v-for="variable in SCENE_VARIABLES" :key="variable">
              <div class="flex items-center justify-between gap-3">
                <FieldLabel :id="`scene-${variable}-label`">{{ copy.groups[variable] }}</FieldLabel>
              </div>
              <ToggleGroup
                type="multiple"
                :spacing="2"
                class="flex-wrap"
                :aria-labelledby="`scene-${variable}-label`"
                :aria-invalid="attempted && !summary"
                :model-value="draft.associations[variable] ?? []"
                @update:model-value="setItems(variable, $event)"
              >
                <ToggleGroupItem v-for="item in SCENE_ITEMS[variable]" :key="item" :value="item">
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
        </FieldGroup>
      </FieldSet>
      <ScenePlaylistField
        v-model="draft.playlist"
        :locale="locale"
        :playlists="playlists"
        :label="copy.playlist"
      />
    </FieldGroup>
  </form>
  <DialogFooter class="shrink-0 flex-row flex-wrap items-center gap-2 px-5 py-4 sm:px-6">
    <Button type="button" variant="outline" @click="emit('cancel')">{{ copy.cancel }}</Button>
    <Button type="submit" form="scene-editor-form">{{ scene !== null ? copy.done : copy.add }}</Button>
  </DialogFooter>
</template>
