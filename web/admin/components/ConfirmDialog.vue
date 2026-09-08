<script setup lang="ts">
/**
 * Section 15 (F-37): destructive actions name the exact target, state that the
 * action is irreversible, and require an explicit confirm. There is no
 * "don't ask again".
 */
defineProps<{ open: boolean; title: string; body: string; danger?: boolean }>()
defineEmits<{ confirm: []; cancel: [] }>()

const { t } = useCopy()
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 grid place-items-center bg-primary/40 px-6"
    role="dialog"
    aria-modal="true"
  >
    <div class="w-full max-w-md rounded-xl border border-subtle bg-surface p-5 shadow-md">
      <h2 class="text-[17px] text-primary">{{ title }}</h2>
      <p class="mt-2 text-[14px] leading-relaxed text-secondary">{{ body }}</p>
      <p v-if="danger" class="mt-2 text-[13px] text-danger">{{ t('common.irreversible') }}</p>

      <div class="mt-5 flex justify-end gap-2">
        <button
          type="button"
          class="rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
          @click="$emit('cancel')"
        >
          {{ t('common.cancel') }}
        </button>
        <button
          type="button"
          :class="[
            'rounded-lg px-3 py-2 text-[13px] text-on-accent transition',
            danger ? 'bg-danger hover:opacity-90' : 'bg-accent hover:bg-accent-hover',
          ]"
          @click="$emit('confirm')"
        >
          {{ t('common.confirm') }}
        </button>
      </div>
    </div>
  </div>
</template>
