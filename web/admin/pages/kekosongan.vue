<script setup lang="ts">
/**
 * Admin UX section 12. The highest-value output of the product for editorial:
 * everything else tells them what they have, this tells them what is missing.
 *
 * A gap cannot be marked resolved by assertion — the state is derived from the
 * corpus after the next ingestion run confirms the question is now answerable.
 */
const { t } = useCopy()
const api = useAdminApi()

const gaps = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    gaps.value = await api.getGaps()
  } finally {
    loading.value = false
  }
})

const sorted = computed(() => [...gaps.value].sort((a, b) => b.count - a.count))

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

    <div v-if="loading" class="py-12 text-center text-[14px] text-secondary">
      Memuat daftar kekosongan konten...
    </div>

    <DataTable v-else :columns="columns">
      <tr
        v-for="gap in sorted"
        :key="gap.id"
        class="border-t border-subtle transition hover:bg-raised/60"
      >
        <td class="px-3 py-2.5 text-[13.5px] text-primary">{{ gap.canonical }}</td>
        <td class="px-3 py-2.5 text-right text-[13px] text-primary">{{ gap.count }}</td>
        <td class="px-3 py-2.5 text-[12.5px] text-secondary">{{ timeLabel(gap.lastAsked) }}</td>
        <td class="px-3 py-2.5">
          <StatusChip
            :label="gap.nearestTopic || 'Lainnya'"
            :tone="gap.nearestTopic === 'Lainnya' ? 'warning' : 'neutral'"
          />
        </td>
        <td class="px-3 py-2.5 text-right">
          <button type="button" class="text-[13px] text-accent underline underline-offset-2">
            {{ t('gaps.resolved') }}
          </button>
        </td>
      </tr>
    </DataTable>

    <p class="meta mt-3 max-w-[70ch]">{{ t('gaps.resolved_note') }}</p>
  </div>
</template>
