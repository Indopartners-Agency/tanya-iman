<script setup lang="ts">
/**
 * Chat UX section 5 (F-1).
 *
 * All three options are full-width buttons of equal size. Guest is outline
 * rather than filled — permitted as a difference in weight — but it is never
 * smaller, lower-contrast, or below the fold. Someone with questions about
 * faith may have good reasons not to attach their phone number to them, and
 * making that the awkward path costs us the conversation.
 *
 * No option is explained. If a label needs explaining, the label is wrong.
 */
const { t } = useCopy()
const auth = useAuthStore()
const router = useRouter()

const busy = ref(false)

async function continueAsGuest() {
  busy.value = true
  try {
    await auth.signInAsGuest()
    await router.push('/chat')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="flex min-h-dvh flex-col bg-base px-6">
    <div class="flex flex-1 flex-col justify-center">
      <div class="mx-auto w-full max-w-[400px]">
        <h1 class="text-center font-serif text-[30px] leading-tight text-primary">
          {{ t('ui.app_name') }}
        </h1>
        <p class="mx-auto mt-3 max-w-[28ch] text-center text-[15px] leading-relaxed text-secondary">
          {{ t('ui.tagline') }}
        </p>

        <div class="mt-10 space-y-3">
          <NuxtLink
            to="/masuk?channel=sms"
            class="flex min-h-[52px] w-full items-center justify-center rounded-xl bg-accent px-4 text-[15px] font-medium text-on-accent transition hover:bg-accent-hover"
          >
            {{ t('ui.login_sms') }}
          </NuxtLink>

          <NuxtLink
            to="/masuk?channel=whatsapp"
            class="flex min-h-[52px] w-full items-center justify-center rounded-xl bg-accent px-4 text-[15px] font-medium text-on-accent transition hover:bg-accent-hover"
          >
            {{ t('ui.login_whatsapp') }}
          </NuxtLink>

          <button
            type="button"
            :disabled="busy"
            class="flex min-h-[52px] w-full items-center justify-center rounded-xl border-2 border-accent bg-transparent px-4 text-[15px] font-medium text-accent transition hover:bg-raised disabled:opacity-50"
            @click="continueAsGuest"
          >
            {{ t('ui.login_guest') }}
          </button>
        </div>
      </div>
    </div>

    <!-- F-4: footer link, 44px tap target even though the text is small. -->
    <footer class="py-4 text-center">
      <NuxtLink
        to="/privasi"
        class="meta inline-flex min-h-[44px] items-center underline underline-offset-2"
      >
        {{ t('ui.privacy') }}
      </NuxtLink>
    </footer>
  </main>
</template>
