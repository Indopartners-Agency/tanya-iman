<script setup lang="ts">
/**
 * Header, persistent source note, and the footer privacy link.
 *
 * In embed mode the header and the outer background are suppressed, but the
 * source note and the privacy link stay: F-4 and F-6 apply inside the widget
 * exactly as they do in the app (Chat UX section 11).
 */
const props = defineProps<{ embed?: boolean }>()

const { t } = useCopy()
const auth = useAuthStore()
const chat = useChatStore()
const router = useRouter()

const menuOpen = ref(false)

// In embed mode the host page sizes its iframe from what we report.
useEmbedHeight(computed(() => Boolean(props.embed)))

async function signOut() {
  menuOpen.value = false
  chat.reset()
  await auth.signOut()
  await router.push('/')
}
</script>

<template>
  <div :class="['flex h-dvh flex-col', embed ? 'bg-surface' : 'bg-base']">
    <header
      v-if="!embed"
      class="flex items-center justify-between border-b border-subtle bg-surface px-4 py-3"
    >
      <h1 class="font-serif text-[17px] text-primary">{{ t('ui.app_name') }}</h1>

      <div class="relative">
        <button
          type="button"
          class="grid h-11 w-11 place-items-center rounded-lg text-secondary transition hover:bg-raised"
          :aria-label="t('ui.menu')"
          :aria-expanded="menuOpen"
          @click="menuOpen = !menuOpen"
        >
          <span aria-hidden="true" class="text-lg leading-none">&#8942;</span>
        </button>

        <div
          v-if="menuOpen"
          class="absolute right-0 top-12 z-20 w-56 overflow-hidden rounded-xl border border-subtle bg-surface shadow-md"
        >
          <NuxtLink
            to="/privasi"
            class="block px-4 py-3 text-[14px] text-primary hover:bg-raised"
            @click="menuOpen = false"
          >
            {{ t('ui.privacy') }}
          </NuxtLink>
          <button
            type="button"
            class="block w-full px-4 py-3 text-left text-[14px] text-primary hover:bg-raised"
            @click="signOut"
          >
            {{ t('ui.logout') }}
          </button>
        </div>
      </div>
    </header>

    <!-- F-6: persistent, not dismissible, does not scroll away. -->
    <p class="meta border-b border-subtle bg-raised px-4 py-2">
      {{ t('shared.source_note') }}
    </p>

    <slot />

    <!-- F-4: reachable from every screen, including inside the widget. -->
    <footer class="border-t border-subtle bg-surface px-4 py-2 text-center">
      <NuxtLink
        to="/privasi"
        class="meta inline-flex min-h-[44px] items-center underline underline-offset-2"
      >
        {{ t('ui.privacy') }}
      </NuxtLink>
    </footer>
  </div>
</template>
