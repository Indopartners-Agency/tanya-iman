<script setup lang="ts">
/**
 * F-5: one conversation, many questions. There is no "new question" button —
 * the seeker just keeps typing.
 *
 * Section 7.5: the view follows new messages only while the seeker is already
 * at the bottom. If they have scrolled up to reread an answer, a Pesan baru
 * pill appears instead of yanking them back down mid-sentence.
 */
const auth = useAuthStore()
const chat = useChatStore()
const router = useRouter()
const route = useRoute()
const { t } = useCopy()
const demo = useDemoMode()

const embed = computed(() => route.query.embed === '1')
const scroller = ref<HTMLElement | null>(null)
const atBottom = ref(true)
const unread = ref(false)

const BOTTOM_TOLERANCE_PX = 80

function onScroll() {
  const el = scroller.value
  if (!el) return
  atBottom.value = el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_TOLERANCE_PX
  if (atBottom.value) unread.value = false
}

function scrollToBottom(behavior: ScrollBehavior = 'smooth') {
  const el = scroller.value
  if (!el) return
  el.scrollTo({ top: el.scrollHeight, behavior })
  unread.value = false
}

onMounted(async () => {
  if (!auth.isAuthenticated && !demo) {
    await router.replace('/')
    return
  }
  if (demo && !auth.isAuthenticated) await auth.signInAsGuest()
  await chat.start()
})

watch(
  () => chat.messages.length,
  async () => {
    await nextTick()
    if (atBottom.value) scrollToBottom()
    else unread.value = true
  },
)
</script>

<template>
  <AppShell :embed="embed">
    <DemoScenarioBar v-if="demo && !embed" />

    <div
      :class="[
        'relative overflow-hidden',
        'flex-1',
      ]"
    >
      <div
        ref="scroller"
        :class="[
          'overflow-y-auto px-4 py-4',
          embed ? 'max-h-[440px] min-h-[220px]' : 'h-full',
        ]"
        aria-live="polite"
        @scroll="onScroll"
      >
        <div class="mx-auto flex max-w-measure flex-col gap-3">
          <MessageBubble
            v-for="message in chat.messages"
            :key="message.id"
            :message="message"
            @like="chat.toggleLike"
            @retry="chat.retry"
          />
        </div>
      </div>

      <button
        v-if="unread"
        type="button"
        class="absolute bottom-4 left-1/2 min-h-[44px] -translate-x-1/2 rounded-full bg-accent px-4 text-[13px] font-medium text-on-accent shadow-md"
        @click="scrollToBottom()"
      >
        {{ t('ui.new_messages') }}
      </button>
    </div>

    <div class="mx-auto w-full max-w-measure">
      <Composer :disabled="chat.sending" @submit="chat.ask" />
    </div>
  </AppShell>
</template>
