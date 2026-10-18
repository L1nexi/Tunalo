<script setup lang="ts">
import { ArrowDownIcon, ArrowUpIcon, GripVerticalIcon, PlusIcon, XIcon } from "@lucide/vue"
import { computed, nextTick, ref } from "vue"

import { CONTEXT_VARIABLES } from "@/api/profile"
import type { ContextVariable, Locale } from "@/api/profile"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FieldDescription, FieldError, FieldLegend, FieldSet } from "@/components/ui/field"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { CONTEXT_VARIABLE_LABELS, COPY } from "@/setup/copy"
import type { PreferenceLayer } from "@/setup/model"

const props = defineProps<{
  locale: Locale
  layers: PreferenceLayer[]
  errors: string[]
}>()
const emit = defineEmits<{
  "update:layers": [layers: PreferenceLayer[]]
  addLayer: []
}>()
const copy = computed(() => COPY[props.locale].preferences)
const labels = computed(() => CONTEXT_VARIABLE_LABELS[props.locale])
const draggedVariable = ref<ContextVariable | null>(null)
const dragOverZone = ref<string | null>(null)
const dragPosition = ref({ x: 0, y: 0 })
let pointerStart: { x: number; y: number; variable: ContextVariable } | null = null
const announcement = ref("")
const zones = computed(() => [
  {
    id: "unassigned", label: copy.value.unassigned,
    variables: CONTEXT_VARIABLES.filter((variable) => !props.layers.some((layer) => layer.variables.includes(variable))),
  },
  ...props.layers.map((layer, index) => ({
    id: String(layer.id), label: copy.value.layer(index + 1),
    variables: CONTEXT_VARIABLES.filter((variable) => layer.variables.includes(variable)),
  })),
])

async function moveVariable(variable: ContextVariable, destination: string): Promise<void> {
  const layers = props.layers.map((layer) => ({
    ...layer, variables: layer.variables.filter((item) => item !== variable),
  }))
  if (destination !== "unassigned") layers.find((layer) => String(layer.id) === destination)!.variables.push(variable)
  emit("update:layers", layers)
  announcement.value = copy.value.moved(labels.value[variable], zones.value.find((zone) => zone.id === destination)!.label)
  await nextTick()
  document.getElementById(`preference-variable-${variable}`)?.focus()
}

async function addLayer(): Promise<void> {
  emit("addLayer")
  await nextTick()
  document.getElementById(`preference-zone-${props.layers.at(-1)!.id}`)?.focus()
}

function moveLayer(index: number, offset: number): void {
  const layers = [...props.layers]
  const [layer] = layers.splice(index, 1)
  layers.splice(index + offset, 0, layer!)
  emit("update:layers", layers)
  announcement.value = copy.value.layerMoved(index + 1, index + offset + 1)
}

async function removeLayer(id: string): Promise<void> {
  emit("update:layers", props.layers.filter((layer) => String(layer.id) !== id))
  announcement.value = copy.value.layerRemoved
  await nextTick()
  document.getElementById("add-preference-layer")?.focus()
}

function startDrag(event: PointerEvent, variable: ContextVariable): void {
  if (event.button !== 0) return
  pointerStart = { x: event.clientX, y: event.clientY, variable }
  const source = event.currentTarget as HTMLElement
  source.setPointerCapture(event.pointerId)
}

function continueDrag(event: PointerEvent): void {
  if (pointerStart === null) return
  if (Math.hypot(event.clientX - pointerStart.x, event.clientY - pointerStart.y) < 4) return
  draggedVariable.value = pointerStart.variable
  dragPosition.value = { x: event.clientX + 12, y: event.clientY + 12 }
  const zone = document.elementFromPoint(event.clientX, event.clientY)?.closest<HTMLElement>("[data-preference-zone]")
  dragOverZone.value = zone?.dataset.preferenceZone ?? null
}

function finishDrag(): void {
  draggedVariable.value = null
  dragOverZone.value = null
  pointerStart = null
}

function dropVariable(): void {
  const variable = draggedVariable.value
  const destination = dragOverZone.value
  finishDrag()
  if (variable !== null && destination !== null) void moveVariable(variable, destination)
}
</script>

<template>
  <FieldSet :data-invalid="errors.length > 0">
    <FieldLegend>{{ copy.responseTitle }}</FieldLegend>
    <FieldDescription id="preference-instructions">{{ copy.responseDescription }}</FieldDescription>
    <div class="flex flex-col gap-3">
      <section
        v-for="(zone, zoneIndex) in zones"
        :id="`preference-zone-${zone.id}`"
        :key="zone.id"
        :data-preference-zone="zone.id"
        role="group"
        :aria-label="zone.label"
        :aria-describedby="errors.length ? 'preference-errors' : 'preference-instructions'"
        :aria-invalid="errors.length > 0"
        tabindex="-1"
        :class="cn('min-w-0 rounded-lg border p-3 outline-none focus-visible:ring-2 focus-visible:ring-ring/30',
          draggedVariable !== null && dragOverZone === zone.id && 'border-primary bg-primary/8')"
      >
        <div class="mb-3 flex items-center justify-between gap-2">
          <h3 class="text-sm font-medium">{{ zone.label }}</h3>
          <div v-if="zoneIndex > 0" class="flex gap-1">
            <Button type="button" variant="ghost" size="icon-xs" :disabled="zoneIndex === 1" :aria-label="copy.moveLayerUp(zoneIndex)" @click="moveLayer(zoneIndex - 1, -1)"><ArrowUpIcon /></Button>
            <Button type="button" variant="ghost" size="icon-xs" :disabled="zoneIndex === layers.length" :aria-label="copy.moveLayerDown(zoneIndex)" @click="moveLayer(zoneIndex - 1, 1)"><ArrowDownIcon /></Button>
            <Button type="button" variant="ghost" size="icon-xs" :aria-label="copy.removeLayer(zoneIndex)" @click="removeLayer(zone.id)"><XIcon /></Button>
          </div>
        </div>
        <div class="flex min-h-9 flex-wrap gap-3">
          <div v-for="variable in zone.variables" :key="variable" class="flex items-center gap-1">
            <Button
              :id="`preference-variable-${variable}`"
              type="button" variant="outline" size="sm"
              :aria-label="copy.dragVariable(labels[variable])"
              class="touch-none select-none cursor-grab active:cursor-grabbing"
              @pointerdown="startDrag($event, variable)" @pointermove="continueDrag"
              @pointerup="dropVariable" @pointercancel="finishDrag" @lostpointercapture="finishDrag"
              @keydown.esc.prevent="finishDrag"
            >
              <GripVerticalIcon data-icon="inline-start" />{{ labels[variable] }}
            </Button>
            <Select :model-value="zone.id" @update:model-value="(value) => moveVariable(variable, String(value))">
              <SelectTrigger size="sm" :aria-label="copy.moveVariable(labels[variable])"><SelectValue /></SelectTrigger>
              <SelectContent><SelectGroup>
                <SelectItem v-for="destination in zones" :key="destination.id" :value="destination.id">{{ destination.label }}</SelectItem>
              </SelectGroup></SelectContent>
            </Select>
          </div>
          <p v-if="!zone.variables.length" class="self-center text-sm text-muted-foreground">{{ copy.dropHere }}</p>
        </div>
      </section>
    </div>
    <Button id="add-preference-layer" type="button" variant="outline" class="self-start" :disabled="layers.length >= 4" @click="addLayer"><PlusIcon data-icon="inline-start" />{{ copy.addLayer }}</Button>
    <p class="sr-only" role="status" aria-live="polite">{{ announcement }}</p>
    <FieldError v-if="errors.length" id="preference-errors" :errors="errors" />
    <Teleport to="body">
      <Badge v-if="draggedVariable !== null" class="pointer-events-none fixed" :style="{ left: `${dragPosition.x}px`, top: `${dragPosition.y}px` }" aria-hidden="true">{{ labels[draggedVariable] }}</Badge>
    </Teleport>
  </FieldSet>
</template>
