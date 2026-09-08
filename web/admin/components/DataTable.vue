<script setup lang="ts">
/**
 * Admin UX section 7.3 and 16: sticky header, horizontal scroll on tablet with
 * the table never forcing the page itself to scroll sideways.
 */
defineProps<{ columns: Array<{ key: string; label: string; align?: 'right' }> }>()
</script>

<template>
  <div class="overflow-x-auto rounded-xl border border-subtle bg-surface">
    <table class="w-full min-w-[720px] border-collapse text-left">
      <thead class="sticky top-0 z-10 bg-raised">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :class="[
              'whitespace-nowrap px-3 py-2.5 text-[12px] font-medium text-secondary',
              column.align === 'right' ? 'text-right' : '',
            ]"
          >
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <slot />
      </tbody>
    </table>
  </div>
</template>
