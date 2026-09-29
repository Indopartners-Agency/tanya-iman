<script setup lang="ts">
/**
 * Admin UX section 13. One worklist, four sources.
 *
 * Crisis and emotional-deferral records are visible to every admin role but
 * carry a standing notice that they are sensitive and must not leave the
 * portal.
 */
const { t } = useCopy()
const api = useAdminApi()

const items = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await api.getReviews()
    items.value = data.map((d: any) => ({
      id: d.id,
      type: d.type || 'validator',
      summary: d.summary || '',
      at: d.at || '',
      reviewed: d.reviewed || false,
    }))
  } catch (e) {
    console.warn('Failed to load reviews:', e)
  } finally {
    loading.value = false
  }
})

const toneFor: Record<string, 'warning' | 'danger' | 'info'> = {
  ambiguous: 'warning',
  validator: 'danger',
  crisis: 'danger',
  emotional: 'info',
}

function markReviewed(id: string) {
  const item = items.value.find((i) => i.id === id)
  if (item) item.reviewed = true
}

function timeLabel(iso: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const columns = [
  { key: 'type', label: t('review.col_type') },
  { key: 'summary', label: t('review.col_summary') },
  { key: 'time', label: t('review.col_time') },
  { key: 'action', label: '' },
]
</script>

<template>
  <div>
    <PageHeader :title="t('review.title')" />

    <p class="mb-3 rounded-lg bg-info-bg px-3 py-2 text-[13px] text-info">
      {{ t('review.sensitive') }}
    </p>

    <div v-if="loading" class="py-12 text-center text-secondary">Memuat…</div>
    <div v-else-if="items.length === 0" class="py-12 text-center text-secondary text-sm">
      Tidak ada item yang perlu ditinjau.
    </div>

    <DataTable v-else :columns="columns">
      <tr
        v-for="item in items"
        :key="item.id"
        :class="['border-t border-subtle', item.reviewed ? 'opacity-55' : '']"
      >
        <td class="px-3 py-2.5">
          <StatusChip :label="t(`review.type_${item.type}`)" :tone="toneFor[item.type]" />
        </td>
        <td class="px-3 py-2.5 text-[13.5px] text-primary">{{ item.summary }}</td>
        <td class="px-3 py-2.5 text-[12.5px] text-secondary">{{ timeLabel(item.at) }}</td>
        <td class="px-3 py-2.5 text-right">
          <button
            v-if="!item.reviewed"
            type="button"
            class="text-[13px] text-accent underline underline-offset-2"
            @click="markReviewed(item.id)"
          >
            {{ t('review.mark_reviewed') }}
          </button>
          <span v-else class="meta">&#10003;</span>
        </td>
      </tr>
    </DataTable>
  </div>
</template>
