<script setup lang="ts">
import { App } from '@capacitor/app'

/**
 * Chat UX section 12. Opened only by the Android back button, mid-conversation.
 */
const { open } = useExitConfirm()
const { t } = useCopy()

function leave() {
  void App.exitApp()
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 grid place-items-center bg-[rgba(0,0,0,0.4)] px-6"
    role="dialog"
    aria-modal="true"
    :aria-label="t('ui.exit_title')"
  >
    <div class="w-full max-w-[340px] rounded-2xl bg-surface p-5 shadow-md">
      <p class="font-serif text-[17px] text-primary">{{ t('ui.exit_title') }}</p>
      <p class="mt-2 text-[14px] leading-relaxed text-secondary">{{ t('ui.exit_body') }}</p>
      <div class="mt-5 flex justify-end gap-2">
        <button
          type="button"
          class="min-h-[44px] rounded-lg px-4 text-[14px] font-medium text-accent hover:bg-raised"
          @click="open = false"
        >
          {{ t('ui.exit_stay') }}
        </button>
        <button
          type="button"
          class="min-h-[44px] rounded-lg bg-accent px-4 text-[14px] font-medium text-on-accent hover:bg-accent-hover"
          @click="leave"
        >
          {{ t('ui.exit_leave') }}
        </button>
      </div>
    </div>
  </div>
</template>
