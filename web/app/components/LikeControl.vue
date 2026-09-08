<script setup lang="ts">
/**
 * Chat UX section 10. One heart, optimistic, reversible (F-33), and no count —
 * a visible count would turn an unpopular answer into a less believable one,
 * which is the opposite of what the signal is for. Editorial reads the counts
 * in the admin portal instead.
 */
defineProps<{ liked: boolean }>()
defineEmits<{ toggle: [] }>()

const { t } = useCopy()
</script>

<template>
  <button
    type="button"
    class="mt-3 flex min-h-[44px] items-center gap-1.5 text-[13px] text-secondary transition hover:text-accent"
    :aria-pressed="liked"
    :aria-label="liked ? t('ui.answer_liked') : t('ui.answer_like')"
    @click="$emit('toggle')"
  >
    <span aria-hidden="true" class="text-[15px]">{{ liked ? '♥' : '♡' }}</span>
    <span>{{ liked ? t('ui.answer_liked') : t('ui.answer_like') }}</span>
  </button>
</template>
