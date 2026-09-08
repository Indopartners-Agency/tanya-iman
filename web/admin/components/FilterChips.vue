<script setup lang="ts">
/**
 * Section 7.2: active filters render as removable chips above the table, with
 * a single action that clears all of them.
 */
defineProps<{ filters: Array<{ key: string; label: string }> }>()
defineEmits<{ remove: [key: string]; clear: [] }>()

const { t } = useCopy()
</script>

<template>
  <div v-if="filters.length" class="mb-3 flex flex-wrap items-center gap-2">
    <button
      v-for="filter in filters"
      :key="filter.key"
      type="button"
      class="flex items-center gap-1.5 rounded-full bg-raised px-2.5 py-1 text-[12px] text-primary transition hover:bg-strong/40"
      @click="$emit('remove', filter.key)"
    >
      {{ filter.label }}
      <span aria-hidden="true" class="text-secondary">&#215;</span>
    </button>

    <button type="button" class="meta underline underline-offset-2" @click="$emit('clear')">
      {{ t('questions.clear_filters') }}
    </button>
  </div>
</template>
