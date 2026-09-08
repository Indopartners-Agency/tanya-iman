<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <div class="mb-5 flex flex-wrap items-end justify-between gap-3">
    <div>
      <h1 class="text-[22px] text-primary">{{ title }}</h1>
      <p v-if="subtitle" class="meta mt-1">{{ subtitle }}</p>
    </div>
    <div class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
