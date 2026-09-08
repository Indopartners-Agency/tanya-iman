<script setup lang="ts">
withDefaults(
  defineProps<{ label: string; value: string; to?: string; alert?: boolean }>(),
  { alert: false },
)
</script>

<template>
  <component
    :is="to ? resolveComponent('NuxtLink') : 'div'"
    :to="to"
    :class="[
      'block rounded-xl border p-4 transition',
      alert ? 'border-danger/40 bg-danger-bg' : 'border-subtle bg-surface hover:border-strong',
    ]"
  >
    <p :class="['meta', alert ? 'text-danger' : '']">{{ label }}</p>
    <p :class="['tabular mt-1 text-[24px]', alert ? 'text-danger' : 'text-primary']">
      {{ value }}
    </p>
    <div class="mt-2">
      <slot />
    </div>
  </component>
</template>
