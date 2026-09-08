<script setup lang="ts">
/**
 * Admin UX section 17: no information is encoded by colour alone. Every chip
 * carries its text, and the tint is a second signal rather than the only one.
 */
withDefaults(
  defineProps<{
    label: string
    tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'info'
  }>(),
  { tone: 'neutral' },
)

const toneClass: Record<string, string> = {
  neutral: 'bg-raised text-primary',
  success: 'bg-success-bg text-success',
  warning: 'bg-warning-bg text-warning',
  danger: 'bg-danger-bg text-danger',
  info: 'bg-info-bg text-info',
}
</script>

<template>
  <span
    :class="[
      'inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-[11.5px]',
      toneClass[tone],
    ]"
  >
    {{ label }}
  </span>
</template>
