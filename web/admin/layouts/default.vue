<script setup lang="ts">
import { useSessionStore } from '~/stores/session'
import { gapCount, reviewCount } from '~/demo/fixtures'

/**
 * Sidebar on desktop, top menu on tablet (Admin UX section 16).
 *
 * Kekosongan Materi and Antrean Tinjauan carry standing badge counts because
 * both represent work waiting to be done — section 3.
 */
const { t } = useCopy()
const session = useSessionStore()
const route = useRoute()
const router = useRouter()
const demo = useDemoMode()

const nav = computed(() => [
  { to: '/', label: t('nav.dashboard'), badge: 0 },
  { to: '/pertanyaan', label: t('nav.questions'), badge: 0 },
  { to: '/topik', label: t('nav.topics'), badge: 0 },
  { to: '/serupa', label: t('nav.clusters'), badge: 0 },
  { to: '/kekosongan', label: t('nav.gaps'), badge: gapCount },
  { to: '/tinjauan', label: t('nav.review'), badge: reviewCount },
  ...(session.canAdminister
    ? [{ to: '/pengaturan', label: t('nav.settings'), badge: 0 }]
    : []),
])

function isActive(to: string): boolean {
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}

async function signOut() {
  session.signOut()
  await router.push('/masuk')
}
</script>

<template>
  <div class="min-h-dvh lg:grid lg:grid-cols-[240px_minmax(0,1fr)]">
    <aside class="border-b border-subtle bg-surface lg:border-b-0 lg:border-r">
      <div class="flex items-center gap-2 px-5 py-4">
        <span class="font-serif text-[16px] text-primary">{{ t('app') }}</span>
        <span class="meta border-l border-subtle pl-2">{{ t('portal') }}</span>
      </div>

      <nav class="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:overflow-visible">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex shrink-0 items-center justify-between gap-2 rounded-lg px-3 py-2 text-[13.5px] transition',
            isActive(item.to) ? 'bg-accent text-on-accent' : 'text-primary hover:bg-raised',
          ]"
        >
          <span>{{ item.label }}</span>
          <span
            v-if="item.badge"
            :class="[
              'tabular rounded-full px-1.5 py-0.5 text-[11px]',
              isActive(item.to) ? 'bg-surface/20' : 'bg-warning-bg text-warning',
            ]"
          >
            {{ item.badge }}
          </span>
        </NuxtLink>
      </nav>
    </aside>

    <div class="flex min-w-0 flex-col">
      <header class="flex items-center gap-3 border-b border-subtle bg-surface px-5 py-3">
        <p v-if="demo" class="meta flex-1 rounded-md bg-info-bg px-2.5 py-1 text-info">
          {{ t('demo_banner') }}
        </p>
        <span v-else class="flex-1" />

        <span class="rounded-full bg-raised px-2.5 py-1 text-[12px] text-primary">
          {{ t(`role.${session.role}`) }}
        </span>
        <span class="meta hidden sm:inline">{{ session.email }}</span>
        <button type="button" class="meta underline underline-offset-2" @click="signOut">
          {{ t('common.logout') }}
        </button>
      </header>

      <main class="min-w-0 flex-1 px-5 py-6">
        <slot />
      </main>
    </div>
  </div>
</template>
