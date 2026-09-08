<script setup lang="ts">
/**
 * Section 5.1: an empty list explains why it might be empty and offers a way
 * out, rather than showing a bare "no results".
 */
defineProps<{ message: string }>()
</script>

<template>
  <div class="rounded-xl border border-dashed border-strong bg-surface px-6 py-10 text-center">
    <p class="text-[14px] text-secondary">{{ message }}</p>
    <div class="mt-3">
      <slot />
    </div>
  </div>
</template>
