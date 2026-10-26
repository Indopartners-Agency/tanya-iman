<script setup lang="ts">
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 12. The highest-value output of the product for editorial:
 * everything else tells them what they have, this tells them what is missing.
 */
const { t } = useCopy()
const api = useAdminApi()
const session = useSessionStore()

const gaps = ref<any[]>([])
const loading = ref(true)
const toast = ref<string | null>(null)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    gaps.value = await api.getGaps()
  } catch (e: any) {
    error.value = e?.message || 'Gagal memuat daftar kekosongan materi.'
  } finally {
    loading.value = false
  }
})

const sorted = computed(() => [...gaps.value].sort((a, b) => b.count - a.count))

async function markGapResolved(gap: any) {
  try {
    await api.resolveGap(gap.id)
    gaps.value = gaps.value.filter((g) => g.id !== gap.id)
    toast.value = `Kekosongan "${gap.canonical}" ditandai sudah ditulis.`
  } catch (e: any) {
    error.value = e?.message || 'Gagal menandai kekosongan materi.'
  }
}

const columns = [
  { key: 'canonical', label: t('gaps.col_canonical') },
  { key: 'count', label: t('gaps.col_count'), align: 'right' as const },
  { key: 'last', label: t('gaps.col_last') },
  { key: 'topic', label: t('gaps.col_topic') },
  { key: 'action', label: '' },
]

function timeLabel(iso: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
}
</script>

<template>
  <div>
    <PageHeader :title="t('gaps.title')" :subtitle="t('gaps.subtitle')" />

    <p v-if="toast" class="mb-3 rounded-lg bg-success-bg px-3 py-2 text-[13px] text-success">
      {{ toast }}
    </p>
    <p v-if="error" class="mb-3 rounded-lg bg-danger-bg px-3 py-2 text-[13px] text-danger">
      {{ error }}
    </p>

    <div v-if="loading" class="py-12 text-center text-[14px] text-secondary">
      Memuat daftar kekosongan konten...
    </div>

    <div v-else-if="sorted.length === 0" class="py-12 text-center text-[14px] text-secondary">
      Tidak ada kekosongan materi yang belum ditangani.
    </div>

    <DataTable v-else :columns="columns">
      <tr
        v-for="gap in sorted"
        :key="gap.id"
        class="border-t border-subtle transition hover:bg-raised/60"
      >
        <td class="px-3 py-2.5 text-[13.5px] text-primary">{{ gap.canonical }}</td>
        <td class="tabular px-3 py-2.5 text-right text-[13px] text-primary">{{ gap.count }}</td>
        <td class="px-3 py-2.5 text-[12.5px] text-secondary">{{ timeLabel(gap.lastAsked) }}</td>
        <td class="px-3 py-2.5">
          <StatusChip
            :label="gap.nearestTopic || 'Lainnya'"
            :tone="gap.nearestTopic === 'Lainnya' ? 'warning' : 'neutral'"
          />
        </td>
        <td class="px-3 py-2.5 text-right">
          <div v-if="session.canEdit" class="inline-flex items-center gap-3">
            <NuxtLink
              v-if="gap.topicSlug"
              :to="{ path: `/editor/${gap.topicSlug}`, query: { q: gap.canonical } }"
              class="text-[13px] text-secondary underline underline-offset-2 hover:text-primary"
            >
              {{ t('topics.write') }}
            </NuxtLink>
            <button
              type="button"
              class="text-[13px] text-accent underline underline-offset-2 hover:opacity-80"
              @click="markGapResolved(gap)"
            >
              {{ t('gaps.resolved') }}
            </button>
          </div>
        </td>
      </tr>
    </DataTable>

    <p class="meta mt-3 max-w-[70ch]">{{ t('gaps.resolved_note') }}</p>
  </div>
</template>
