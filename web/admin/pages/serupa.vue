<script setup lang="ts">
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 11. Sorted by member count descending — read from the top,
 * this list is the content queue.
 *
 * Expanding a cluster shows its members in their original wording, which is
 * where the editorial insight lives: the canonical phrasing tells you the
 * theme, the raw wording tells you how people actually talk about it.
 */
const { t } = useCopy()
const session = useSessionStore()
const api = useAdminApi()

const clusters = ref<any[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    clusters.value = await api.getClusters()
  } catch (e: any) {
    error.value = e?.message || 'Gagal memuat kluster.'
  } finally {
    loading.value = false
  }
})

const expanded = ref<string | null>(null)
const sorted = computed(() => [...clusters.value].sort((a, b) => b.count - a.count))

function timeLabel(iso: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
}
</script>

<template>
  <div>
    <PageHeader :title="t('clusters.title')" />

    <div v-if="loading" class="py-12 text-center text-secondary">Memuat…</div>
    <div v-else-if="error" class="py-8 text-center text-sm text-red-500">{{ error }}</div>
    <div v-else-if="sorted.length === 0" class="py-12 text-center text-secondary text-sm">
      Belum ada kluster pertanyaan.
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="cluster in sorted"
        :key="cluster.id"
        class="rounded-xl border border-subtle bg-surface"
      >
        <button
          type="button"
          class="flex w-full items-center gap-3 px-4 py-3 text-left"
          :aria-expanded="expanded === cluster.id"
          @click="expanded = expanded === cluster.id ? null : cluster.id"
        >
          <span class="tabular w-10 shrink-0 text-[15px] text-primary">{{ cluster.count }}</span>
          <span class="min-w-0 flex-1">
            <span class="block text-[13.5px] text-primary">{{ cluster.canonical }}</span>
            <span class="meta">
              {{ cluster.topicLabel }} · {{ t('clusters.col_last') }}
              {{ timeLabel(cluster.lastAsked) }}
            </span>
          </span>
          <StatusChip
            :label="cluster.hasCurated ? t('topics.curated_published') : t('topics.curated_none')"
            :tone="cluster.hasCurated ? 'success' : 'neutral'"
          />
        </button>

        <div v-if="expanded === cluster.id" class="border-t border-subtle px-4 py-3">
          <p class="meta mb-2">{{ t('clusters.members') }}</p>
          <ul class="space-y-1.5">
            <li v-for="member in cluster.members" :key="member" class="text-[13px] text-secondary">
              {{ member }}
            </li>
          </ul>
          <NuxtLink
            v-if="session.canEdit"
            :to="`/editor/${cluster.topicSlug}`"
            class="mt-3 inline-block text-[13px] text-accent underline underline-offset-2"
          >
            {{ t('clusters.make_curated') }}
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>
