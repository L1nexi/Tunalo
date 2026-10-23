<script setup lang="ts">
import { ArrowDownIcon, ArrowUpIcon, GripVerticalIcon, PlusIcon, XIcon } from "@lucide/vue"
import { computed, nextTick, ref } from "vue"

import { CONTEXT_VARIABLES } from "@/api/profile"
import type { ContextVariable, Locale } from "@/api/profile"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FieldDescription, FieldError, FieldLegend, FieldSet } from "@/components/ui/field"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { CONTEXT_VARIABLE_LABELS, COPY } from "@/setup/copy"
import type { PreferenceLayer } from "@/setup/profile/model"

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
const hasPriorities = computed(() => props.layers.some((layer) => layer.variables.length > 0))
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
  if (destination === "new") {
    emit("addLayer")
    await nextTick()
    destination = String(props.layers.at(-1)!.id)
  }
  const layers = props.layers.map((layer) => ({
    ...layer, variables: layer.variables.filter((item) => item !== variable),
  }))
  if (destination !== "unassigned") layers.find((layer) => String(layer.id) === destination)!.variables.push(variable)
  emit("update:layers", layers)
  announcement.value = copy.value.moved(labels.value[variable], zones.value.find((zone) => zone.id === destination)!.label)
  await nextTick()
  document.getElementById(`preference-move-${variable}`)?.focus()
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
  <FieldSet class="gap-4" :data-invalid="errors.length > 0">
    <FieldLegend>{{ copy.responseTitle }}</FieldLegend>
    <FieldDescription id="preference-instructions" class="max-w-[72ch]">{{ hasPriorities ? copy.cascadeHelp : copy.noPriorityHelp }}</FieldDescription>
    <div class="flex flex-col gap-2">
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
          zoneIndex === 0 ? 'border-dashed bg-muted/30' : 'border-l-2 border-l-primary/50',
          draggedVariable !== null && dragOverZone === zone.id && 'border-primary bg-primary/8')"
      >
        <div class="flex min-w-0 flex-wrap items-center gap-2">
          <h3 class="mr-auto text-sm font-medium sm:mr-1 sm:w-28 sm:shrink-0">{{ zone.label }}</h3>
          <div class="order-last flex min-h-8 min-w-0 basis-full flex-wrap items-center gap-2 sm:order-none sm:flex-1 sm:basis-0">
            <div v-for="variable in zone.variables" :key="variable" class="flex items-center gap-0.5">
              <Button
                :id="`preference-variable-${variable}`"
                type="button" variant="outline" size="sm"
                :aria-label="copy.dragVariable(labels[variable])"
                class="touch-none select-none cursor-grab rounded-r-sm active:cursor-grabbing"
                @pointerdown="startDrag($event, variable)" @pointermove="continueDrag"
                @pointerup="dropVariable" @pointercancel="finishDrag" @lostpointercapture="finishDrag"
                @keydown.esc.prevent="finishDrag"
              >
                <GripVerticalIcon data-icon="inline-start" />{{ labels[variable] }}
              </Button>
              <Select :model-value="zone.id" @update:model-value="(value) => moveVariable(variable, String(value))">
                <SelectTrigger :id="`preference-move-${variable}`" size="sm" class="w-8 justify-center rounded-l-sm px-0" :aria-label="copy.moveVariable(labels[variable])" :title="copy.moveVariable(labels[variable])" />
                <SelectContent position="popper" align="start"><SelectGroup>
                  <SelectItem v-for="destination in zones" :key="destination.id" :value="destination.id">{{ destination.label }}</SelectItem>
                  <SelectItem v-if="layers.length < 4" value="new">{{ copy.moveToNewLayer }}</SelectItem>
                </SelectGroup></SelectContent>
              </Select>
            </div>
            <p v-if="!zone.variables.length" class="self-center text-sm text-muted-foreground">{{ zoneIndex === 0 ? copy.allAssigned : copy.dropHere }}</p>
          </div>
          <div v-if="zoneIndex > 0" class="flex shrink-0 gap-1">
            <Button type="button" variant="ghost" size="icon-sm" :disabled="zoneIndex === 1" :aria-label="copy.moveLayerUp(zoneIndex)" :title="copy.moveLayerUp(zoneIndex)" @click="moveLayer(zoneIndex - 1, -1)"><ArrowUpIcon /></Button>
            <Button type="button" variant="ghost" size="icon-sm" :disabled="zoneIndex === layers.length" :aria-label="copy.moveLayerDown(zoneIndex)" :title="copy.moveLayerDown(zoneIndex)" @click="moveLayer(zoneIndex - 1, 1)"><ArrowDownIcon /></Button>
            <Button type="button" variant="ghost" size="icon-sm" :aria-label="copy.removeLayer(zoneIndex)" :title="copy.removeLayer(zoneIndex)" @click="removeLayer(zone.id)"><XIcon /></Button>
          </div>
        </div>
        <p v-if="zoneIndex === 0 && zone.variables.length" class="mt-2 text-xs leading-relaxed text-muted-foreground">{{ copy.unassignedHelp }}</p>
      </section>
    </div>
    <p class="text-xs leading-relaxed text-muted-foreground">{{ copy.responseDescription }}</p>
    <Button id="add-preference-layer" type="button" variant="outline" class="self-start" :disabled="layers.length >= 4" @click="addLayer"><PlusIcon data-icon="inline-start" />{{ copy.addLayer }}</Button>
    <p class="sr-only" role="status" aria-live="polite">{{ announcement }}</p>
    <FieldError v-if="errors.length" id="preference-errors" :errors="errors" />
    <Teleport to="body">
      <Badge v-if="draggedVariable !== null" class="pointer-events-none fixed" :style="{ left: `${dragPosition.x}px`, top: `${dragPosition.y}px` }" aria-hidden="true">{{ labels[draggedVariable] }}</Badge>
    </Teleport>
  </FieldSet>
</template>
