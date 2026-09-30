<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div
    data-slot="card-footer"
    :class="cn('rounded-b-xl px-(--card-spacing) [.border-t]:pt-(--card-spacing) flex items-center', props.class)"
  >
    <slot />
  </div>
</template>
