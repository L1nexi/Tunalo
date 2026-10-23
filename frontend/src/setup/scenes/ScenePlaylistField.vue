<script setup lang="ts">
import { computed } from "vue"
import type { Locale, PlaylistScanResult } from "@/api/profile"
import { Button } from "@/components/ui/button"
import { Field, FieldLabel } from "@/components/ui/field"
import { COPY } from "@/setup/copy"
import PlaylistPicker from "./PlaylistPicker.vue"

const props = defineProps<{
  locale: Locale
  playlists: PlaylistScanResult["playlists"]
  label: string
}>()
const playlist = defineModel<string>({ required: true })
const copy = computed(() => COPY[props.locale].scenes)
</script>

<template>
  <Field>
    <FieldLabel>
      {{ label }} <span class="text-muted-foreground">{{ copy.optional }}</span>
    </FieldLabel>
    <PlaylistPicker
      v-model="playlist"
      :locale="locale"
      :playlists="playlists"
      :label="label"
      :placeholder="copy.later"
    />
    <Button
      v-if="playlist"
      type="button"
      variant="ghost"
      size="sm"
      class="self-start"
      @click="playlist = ''"
      >{{ copy.chooseLater }}</Button
    >
  </Field>
</template>
