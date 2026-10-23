<script setup lang="ts">
import { ChevronDownIcon } from "@lucide/vue"
import { computed } from "vue"
import type { Locale, PlaylistScanResult } from "@/api/profile"
import { Button } from "@/components/ui/button"
import {
  Combobox,
  ComboboxAnchor,
  ComboboxTrigger,
  ComboboxList,
  ComboboxInput,
  ComboboxEmpty,
  ComboboxViewport,
  ComboboxGroup,
  ComboboxItem,
} from "@/components/ui/combobox"
import { COPY } from "@/setup/copy"
const props = defineProps<{
  modelValue: string
  locale: Locale
  playlists: PlaylistScanResult["playlists"]
  label: string
  invalid?: boolean
  describedby?: string
  placeholder?: string
}>()
const emit = defineEmits<{ "update:modelValue": [value: string] }>()
const copy = computed(() => COPY[props.locale].scenes)
function update(value: unknown): void {
  if (typeof value === "string") emit("update:modelValue", value)
}
</script>
<template>
  <Combobox :model-value="modelValue" :reset-search-term-on-blur="true" @update:model-value="update">
    <ComboboxAnchor as-child
      ><ComboboxTrigger as-child>
        <Button
          variant="outline"
          class="w-full min-w-0 justify-between"
          :aria-label="label"
          :aria-invalid="invalid"
          :aria-describedby="describedby"
          :disabled="!playlists.length"
        >
          <span class="min-w-0 truncate" :title="modelValue">{{
            modelValue || placeholder || copy.choosePlaylist
          }}</span>
          <ChevronDownIcon data-icon="inline-end" />
        </Button> </ComboboxTrigger
    ></ComboboxAnchor>
    <ComboboxList>
      <ComboboxInput :placeholder="copy.searchPlaylist" :display-value="() => ''" />
      <ComboboxEmpty>{{ copy.noPlaylistMatch }}</ComboboxEmpty>
      <ComboboxViewport
        ><ComboboxGroup>
          <ComboboxItem v-for="playlist in playlists" :key="playlist.name" :value="playlist.name">
            <span class="min-w-0 truncate" :title="playlist.name">{{ playlist.name }}</span>
          </ComboboxItem>
        </ComboboxGroup></ComboboxViewport
      >
    </ComboboxList>
  </Combobox>
</template>
