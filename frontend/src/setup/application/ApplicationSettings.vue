<script setup lang="ts">
import { TriangleAlertIcon } from "@lucide/vue"
import { computed } from "vue"

import type { Locale } from "@/api/profile"
import { useAutostart } from "@/autostart"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Field, FieldContent, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Switch } from "@/components/ui/switch"
import { COPY } from "@/setup/copy"

const props = defineProps<{ locale: Locale }>()
const copy = computed(() => COPY[props.locale])
const { enabled, status, canChange, busy, setEnabled, retry } = useAutostart()
const error = computed(() => {
  if (status.value === "load-error") return copy.value.application.loadError
  if (status.value === "save-error") return copy.value.application.saveError
  return ""
})
</script>

<template>
  <FieldGroup class="max-w-[47.5rem]" :aria-busy="busy">
    <Field orientation="horizontal">
      <FieldContent>
        <FieldLabel for="autostart">{{ copy.application.autostart }}</FieldLabel>
        <FieldDescription id="autostart-description">{{ copy.application.autostartDescription }}</FieldDescription>
      </FieldContent>
      <Switch
        id="autostart"
        class="mt-0.5"
        :model-value="enabled"
        :disabled="!canChange"
        aria-describedby="autostart-description"
        @update:model-value="setEnabled"
      />
    </Field>
    <p v-if="status === 'unavailable'" class="text-sm text-muted-foreground">{{ copy.application.desktopOnly }}</p>
    <p v-else-if="busy" class="text-sm text-muted-foreground" role="status">
      {{ status === 'loading' ? copy.application.loading : copy.application.saving }}
    </p>
    <Alert v-if="error" variant="destructive">
      <TriangleAlertIcon />
      <AlertDescription class="flex flex-col items-start gap-3">
        <p>{{ error }}</p>
        <Button type="button" variant="outline" size="sm" @click="retry">{{ copy.common.retry }}</Button>
      </AlertDescription>
    </Alert>
  </FieldGroup>
</template>
