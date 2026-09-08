<script setup lang="ts">
/**
 * Chat UX section 7.4.
 *
 * Send is disabled while a request is in flight but the textarea stays
 * editable, so a seeker can compose their next question while waiting (F-26).
 * That is why `disabled` gates the button and not the field.
 */
const props = defineProps<{ disabled?: boolean }>()
const emit = defineEmits<{ submit: [text: string] }>()

const { t } = useCopy()
const MAX_CHARS = 1000 // mirrors MAX_QUESTION_CHARS in backend settings
const COUNTER_FROM = 800 // section 7.4: the counter appears only past 800

const text = ref('')
const textarea = ref<HTMLTextAreaElement | null>(null)

const tooLong = computed(() => text.value.length > MAX_CHARS)
const showCounter = computed(() => text.value.length >= COUNTER_FROM)
const canSend = computed(
  () => !props.disabled && text.value.trim().length > 0 && !tooLong.value,
)

/**
 * Enter sends on a physical keyboard; on touch it inserts a newline and the
 * send button is the only way to submit. The opposite convention loses people
 * mid-sentence (section 7.4).
 */
const isTouch = ref(false)
onMounted(() => {
  isTouch.value = window.matchMedia('(pointer: coarse)').matches
})

function submit() {
  if (!canSend.value) return
  emit('submit', text.value)
  text.value = ''
  resize()
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey || isTouch.value) return
  event.preventDefault()
  submit()
}

function resize() {
  const el = textarea.value
  if (!el) return
  el.style.height = 'auto'
  // 1 to 5 lines, then the textarea scrolls internally.
  el.style.height = `${Math.min(el.scrollHeight, 150)}px`
}
</script>

<template>
  <form
    class="flex items-end gap-2 border-t border-subtle bg-surface p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]"
    @submit.prevent="submit"
  >
    <div class="flex-1">
      <textarea
        ref="textarea"
        v-model="text"
        rows="1"
        :placeholder="t('ui.composer_placeholder')"
        :aria-label="t('ui.composer_placeholder')"
        class="w-full resize-none rounded-xl border border-strong bg-surface px-3 py-2.5 text-[15px] leading-relaxed text-primary outline-none transition placeholder:text-secondary focus:border-accent focus:ring-2 focus:ring-accent/15"
        @input="resize"
        @keydown="onKeydown"
      />
      <p
        v-if="showCounter"
        :class="['mt-1 text-right text-[12px]', tooLong ? 'text-warning' : 'text-secondary']"
      >
        {{ t('ui.composer_counter', { count: text.length }) }}
      </p>
    </div>

    <button
      type="submit"
      :disabled="!canSend"
      class="mb-0.5 min-h-[44px] shrink-0 rounded-xl bg-accent px-4 py-2.5 text-[14px] font-medium text-on-accent transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
    >
      {{ t('ui.composer_send') }}
    </button>
  </form>
</template>
