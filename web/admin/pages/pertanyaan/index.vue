<script setup lang="ts">
import type { QuestionRow } from '~/demo/fixtures'

/**
 * Admin UX section 7. Seven columns, filters as removable chips, CSV export
 * that exports the current filter rather than the current page (F-36).
 *
 * Filter state lives in the URL query string (section 5.4) so "grief questions
 * in the last 30 days with no grounding" can be pasted into a chat message and
 * opened by a colleague.
 *
 * No phone number appears here, by design (section 7.4).
 */
const { t } = useCopy()
const route = useRoute()
const router = useRouter()
const api = useAdminApi()

const questions = ref<QuestionRow[]>([])
const topics = ref<any[]>([])
const loading = ref(true)

const search = ref(String(route.query.q ?? ''))
const topicFilter = ref(String(route.query.topik ?? ''))
const resultFilter = ref(String(route.query.hasil ?? ''))

onMounted(async () => {
  try {
    const [qData, tData] = await Promise.all([
      api.getQuestions(),
      api.getTopics(),
    ])
    questions.value = qData as QuestionRow[]
    topics.value = tData
  } finally {
    loading.value = false
  }
})

watch([search, topicFilter, resultFilter], ([q, topik, hasil]) => {
  router.replace({
    query: {
      ...(q ? { q } : {}),
      ...(topik ? { topik } : {}),
      ...(hasil ? { hasil } : {}),
    },
  })
})

const rows = computed(() =>
  questions.value.filter((row) => {
    if (search.value && !row.question.toLowerCase().includes(search.value.toLowerCase()))
      return false
    if (topicFilter.value && row.topicSlug !== topicFilter.value) return false
    if (resultFilter.value && row.result !== resultFilter.value) return false
    return true
  }),
)

const activeFilters = computed(() => [
  ...(search.value ? [{ key: 'q', label: `“${search.value}”` }] : []),
  ...(topicFilter.value
    ? [
        {
          key: 'topik',
          label: topics.value.find((tp) => tp.slug === topicFilter.value)?.label ?? topicFilter.value,
        },
      ]
    : []),
  ...(resultFilter.value ? [{ key: 'hasil', label: t(`result.${resultFilter.value}`) }] : []),
])

function removeFilter(key: string) {
  if (key === 'q') search.value = ''
  if (key === 'topik') topicFilter.value = ''
  if (key === 'hasil') resultFilter.value = ''
}

function clearFilters() {
  search.value = ''
  topicFilter.value = ''
  resultFilter.value = ''
}

const resultTone: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'neutral'> = {
  generated: 'success',
  curated: 'success',
  refusal: 'info',
  no_grounding: 'warning',
  crisis: 'danger',
  emotional_deferral: 'info',
  error: 'danger',
}

const channelLabel: Record<string, string> = {
  web: t('common.channel_web'),
  widget: t('common.channel_widget'),
  android: t('common.channel_android'),
}

const resultKeys = ['generated', 'curated', 'refusal', 'no_grounding', 'crisis', 'error']

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * F-36: exports every row matching the current filter, not the page on screen.
 * No phone number is included in any form (section 7.4).
 */
function exportCsv() {
  const header = ['waktu', 'pertanyaan', 'topik', 'hasil', 'suka', 'kanal']
  const lines = rows.value.map((row: QuestionRow) =>
    [
      row.askedAt,
      `"${row.question.replace(/"/g, '""')}"`,
      row.topicLabel,
      row.result,
      row.likes,
      row.channel,
    ].join(','),
  )
  const blob = new Blob([[header.join(','), ...lines].join('\n')], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'pertanyaan.csv'
  link.click()
  URL.revokeObjectURL(url)
}

const columns = [
  { key: 'time', label: t('questions.col_time') },
  { key: 'question', label: t('questions.col_question') },
  { key: 'topic', label: t('questions.col_topic') },
  { key: 'result', label: t('questions.col_result') },
  { key: 'likes', label: t('questions.col_likes'), align: 'right' as const },
  { key: 'channel', label: t('questions.col_channel') },
  { key: 'flags', label: t('questions.col_flags') },
]
</script>

<template>
  <div>
    <PageHeader :title="t('questions.title')">
      <template #actions>
        <button
          type="button"
          class="rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
          @click="exportCsv"
        >
          {{ t('questions.export') }}
        </button>
      </template>
    </PageHeader>

    <div class="mb-3 flex flex-wrap gap-2">
      <input
        v-model="search"
        type="search"
        :placeholder="t('questions.search')"
        class="min-h-[40px] flex-1 rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary outline-none focus:border-accent"
      />
      <select
        v-model="topicFilter"
        class="min-h-[40px] rounded-lg border border-strong bg-surface px-2 text-[13.5px] text-primary"
      >
        <option value="">{{ t('questions.col_topic') }}</option>
        <option v-for="topic in topics" :key="topic.slug" :value="topic.slug">
          {{ topic.label }}
        </option>
      </select>
      <select
        v-model="resultFilter"
        class="min-h-[40px] rounded-lg border border-strong bg-surface px-2 text-[13.5px] text-primary"
      >
        <option value="">{{ t('questions.col_result') }}</option>
        <option v-for="key in resultKeys" :key="key" :value="key">
          {{ t(`result.${key}`) }}
        </option>
      </select>
    </div>

    <FilterChips :filters="activeFilters" @remove="removeFilter" @clear="clearFilters" />

    <EmptyState v-if="!rows.length" :message="t('questions.empty')">
      <button type="button" class="meta underline underline-offset-2" @click="clearFilters">
        {{ t('questions.clear_filters') }}
      </button>
    </EmptyState>

    <DataTable v-else :columns="columns">
      <tr
        v-for="row in rows"
        :key="row.id"
        class="border-t border-subtle transition hover:bg-raised/60"
      >
        <td class="whitespace-nowrap px-3 py-2.5 text-[12.5px] text-secondary">
          {{ timeLabel(row.askedAt) }}
        </td>
        <td class="px-3 py-2.5">
          <NuxtLink
            :to="`/pertanyaan/${row.id}`"
            class="line-clamp-2 text-[13.5px] text-primary hover:text-accent"
            :title="row.question"
          >
            {{ row.question }}
          </NuxtLink>
        </td>
        <td class="px-3 py-2.5">
          <StatusChip
            :label="row.topicLabel"
            :tone="row.topicSlug === 'lainnya' ? 'warning' : 'neutral'"
          />
        </td>
        <td class="px-3 py-2.5">
          <StatusChip :label="t(`result.${row.result}`)" :tone="resultTone[row.result]" />
        </td>
        <td class="px-3 py-2.5 text-right text-[13px] text-primary">{{ row.likes }}</td>
        <td class="px-3 py-2.5 text-[13px] text-secondary" :title="row.hostSite">
          {{ channelLabel[row.channel] }}
        </td>
        <td class="px-3 py-2.5">
          <span v-if="row.flags.includes('ambiguous')" :title="t('review.type_ambiguous')">
            &#9888;
          </span>
          <span v-if="row.flags.includes('validator')" :title="t('review.type_validator')">
            &#9873;
          </span>
        </td>
      </tr>
    </DataTable>
  </div>
</template>
