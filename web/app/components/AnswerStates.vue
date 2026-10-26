<script setup lang="ts">
import type { Message } from '~/stores/chat'
import { parseTextWithPhoneLinks } from '~/utils/phoneLinks'

/**
 * The non-standard response states (Chat UX section 8).
 *
 * Each is distinguishable without colour — the copy and the layout differ, not
 * only the tint (section 13). The crisis state is a card with no bubble tail,
 * wider padding, and a border, so it does not read as one more reply.
 */
const props = defineProps<{ message: Message }>()
defineEmits<{ retry: [id: string] }>()

const { t } = useCopy()
const demo = useDemoMode()

const remaining = ref(props.message.retryAfterSeconds ?? 0)
let ticker: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  if (props.message.answerSource !== 'rate_limited') return
  // Section 8.4: the countdown ticks live and resolves without a reload.
  ticker = setInterval(() => {
    remaining.value = Math.max(0, remaining.value - 1)
    if (remaining.value === 0 && ticker) clearInterval(ticker)
  }, 1000)
})

onUnmounted(() => {
  if (ticker) clearInterval(ticker)
})

const countdown = computed(() => {
  const minutes = Math.floor(remaining.value / 60)
  const seconds = remaining.value % 60
  return minutes > 0
    ? `${minutes} menit ${String(seconds).padStart(2, '0')} detik`
    : `${seconds} detik`
})

const parsedParts = computed(() => parseTextWithPhoneLinks(props.message.text))
</script>

<template>
  <!-- Refusal and no-grounding: informational, no icon, no citations, no like. -->
  <div
    v-if="message.answerSource === 'refusal' || message.answerSource === 'no_grounding'"
    class="rounded-2xl rounded-bl-md bg-info-bg px-4 py-3.5 text-[15px] leading-relaxed text-info"
  >
    <p class="whitespace-pre-wrap">
      {{ message.answerSource === 'refusal' ? t('shared.refusal') : t('shared.no_grounding') }}
    </p>
  </div>

  <!-- Emotional deferral (F-44): empathetic referral card with tappable tel: link, no retry button, no like. -->
  <div
    v-else-if="message.answerSource === 'emotional_deferral'"
    class="rounded-2xl rounded-bl-md bg-info-bg px-4 py-3.5 text-[15px] leading-relaxed text-info"
    role="note"
  >
    <p class="whitespace-pre-wrap">
      <template v-for="(part, i) in parsedParts" :key="i">
        <a
          v-if="part.tel"
          :href="`tel:${part.tel}`"
          class="inline-flex min-h-[44px] items-center font-medium underline underline-offset-2"
        >
          {{ part.text }}
        </a>
        <span v-else>{{ part.text }}</span>
      </template>
    </p>
  </div>

  <!-- Crisis (F-30): a card, not a reply. No scripture, no citations, no like. Tappable tel: numbers. -->
  <div
    v-else-if="message.answerSource === 'crisis'"
    class="rounded-2xl border-l-4 bg-care-bg px-5 py-4 text-[15px] leading-relaxed text-care"
    style="border-left-color: var(--status-care-border)"
    role="note"
  >
    <p class="whitespace-pre-wrap">
      <template v-for="(part, i) in parsedParts" :key="i">
        <a
          v-if="part.tel"
          :href="`tel:${part.tel}`"
          class="inline-flex min-h-[44px] items-center font-medium underline underline-offset-2"
        >
          {{ part.text }}
        </a>
        <span v-else>{{ part.text }}</span>
      </template>
    </p>
    <p v-if="demo" class="meta mt-3 italic">{{ t('ui.crisis_demo_note') }}</p>
  </div>

  <!-- Rate limited: a live countdown, resolving on its own. -->
  <div
    v-else-if="message.answerSource === 'rate_limited'"
    class="rounded-2xl rounded-bl-md bg-warning-bg px-4 py-3.5 text-[15px] leading-relaxed text-warning"
  >
    <p>{{ t('shared.rate_limit', { minutes: Math.ceil(remaining / 60) }) }}</p>
    <p v-if="remaining > 0" class="meta mt-1.5">
      {{ t('ui.rate_limited_in', { time: countdown }) }}
    </p>
  </div>

  <!-- Error: the one state with an action. -->
  <div
    v-else
    class="rounded-2xl rounded-bl-md bg-warning-bg px-4 py-3.5 text-[15px] leading-relaxed text-warning"
  >
    <p>{{ message.text || t('shared.error') }}</p>
    <button
      v-if="message.failedQuestion"
      type="button"
      class="mt-2 min-h-[44px] font-medium underline underline-offset-2"
      @click="$emit('retry', message.id)"
    >
      {{ t('ui.retry') }}
    </button>
  </div>
</template>
