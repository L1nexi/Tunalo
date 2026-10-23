<script setup lang="ts">
import { PlusIcon, XIcon } from "@lucide/vue"
import { nextTick } from "vue"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
} from "@/components/ui/input-group"

const props = defineProps<{
  id: string
  placeholder: string
  addLabel: string
  removeLabel: string
  emptyLabel: string
  invalid?: boolean
  errorId?: string
  descriptionId?: string
}>()

const values = defineModel<string[]>({ required: true })
const input = defineModel<string>("pending", { required: true })

function addValue(): void {
  const value = input.value.trim()
  if (!value) return
  if (!values.value.some((existing) => existing.toLocaleLowerCase() === value.toLocaleLowerCase())) {
    values.value = [...values.value, value]
  }
  input.value = ""
}

async function removeValue(value: string): Promise<void> {
  values.value = values.value.filter((existing) => existing !== value)
  await nextTick()
  document.getElementById(props.id)?.focus()
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <InputGroup>
      <InputGroupInput
        :id="props.id"
        v-model="input"
        :placeholder="props.placeholder"
        :aria-invalid="props.invalid || undefined"
        :aria-describedby="[props.descriptionId, props.invalid ? props.errorId : undefined].filter(Boolean).join(' ') || undefined"
        @keydown.enter="(event: KeyboardEvent) => { if (!event.isComposing) { event.preventDefault(); addValue() } }"
      />
      <InputGroupAddon align="inline-end">
        <InputGroupButton :aria-label="props.addLabel" :disabled="!input.trim()" @click="addValue">
          <PlusIcon />
          <span>{{ props.addLabel }}</span>
        </InputGroupButton>
      </InputGroupAddon>
    </InputGroup>

    <div v-if="values.length" class="flex flex-wrap gap-2">
      <Badge
        v-for="value in values"
        :key="value"
        variant="secondary"
        class="h-auto min-h-8 max-w-full gap-1 pr-1"
      >
        <span class="min-w-0 whitespace-normal break-all">{{ value }}</span>
        <Button type="button" variant="ghost" size="icon-xs" class="shrink-0" :aria-label="`${props.removeLabel}: ${value}`" :title="`${props.removeLabel}: ${value}`" @click="removeValue(value)">
          <XIcon />
        </Button>
      </Badge>
    </div>
    <p v-else class="text-sm text-muted-foreground">{{ props.emptyLabel }}</p>
  </div>
</template>
