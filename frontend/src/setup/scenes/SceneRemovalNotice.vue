<script setup lang="ts">
import { XIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale } from "@/api/profile"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { COPY } from "@/setup/copy"

const props = defineProps<{ locale: Locale; name: string; submitting: boolean }>()
const emit = defineEmits<{ restore: []; dismiss: [] }>()
const copy = computed(() => COPY[props.locale].scenes)
</script>

<template>
  <Alert class="flex items-center gap-3">
    <div class="min-w-0 flex-1">
      <AlertTitle>{{ copy.removed }}</AlertTitle>
      <AlertDescription class="break-words">{{ name }}</AlertDescription>
    </div>
    <Button size="sm" variant="secondary" :disabled="submitting" @click="emit('restore')">{{
      copy.undo
    }}</Button>
    <Button size="icon-sm" variant="ghost" :aria-label="copy.dismissRemoval" @click="emit('dismiss')"
      ><XIcon
    /></Button>
  </Alert>
</template>
