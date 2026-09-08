<script setup lang="ts">
/**
 * Chat UX section 8.1. The pending bubble appears immediately on send and is
 * replaced in place — it never vanishes without something taking its spot.
 *
 * Past 8 seconds a Meta line appears. It is honest, and it is what stops a
 * seeker from resending the same question three times.
 */
const { t } = useCopy()

const SLOW_AFTER_MS = 8000
const slow = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined

onMounted(() => {
  timer = setTimeout(() => (slow.value = true), SLOW_AFTER_MS)
})

onUnmounted(() => {
  if (timer) clearTimeout(timer)
})
</script>

<template>
  <div>
    <p class="flex gap-1.5 py-1" aria-live="polite">
      <span class="sr-only">{{ t('ui.composer_thinking') }}</span>
      <span
        v-for="i in 3"
        :key="i"
        class="h-2 w-2 animate-bounce rounded-full bg-strong"
        :style="{ animationDelay: `${(i - 1) * 0.15}s` }"
      />
    </p>
    <p v-if="slow" class="meta mt-1.5">{{ t('ui.still_working') }}</p>
  </div>
</template>
