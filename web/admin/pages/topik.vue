<script setup lang="ts">
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 9. Sorted by question count descending, so read top-down
 * this table is the editorial priority list — the highest-demand topic without
 * a curated answer is the first row the eye lands on.
 */
const { t } = useCopy()
const session = useSessionStore()
const router = useRouter()
const api = useAdminApi()

const topics = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  if (!session.isAuthenticated) {
    await router.replace('/masuk')
    return
  }

  try {
    topics.value = await api.getTopics()
  } finally {
    loading.value = false
  }
})

const sorted = computed(() => [...topics.value].sort((a, b) => b.questions - a.questions))

const totalQuestions = computed(() => topics.value.reduce((sum, tp) => sum + tp.questions, 0))
const lainnya = computed(() => topics.value.find((tp) => tp.slug === 'lainnya'))
/** PRD Appendix A: past 10%, the taxonomy needs a new topic. */
const lainnyaHigh = computed(
  () => !!lainnya.value && totalQuestions.value > 0 && lainnya.value.questions / totalQuestions.value > 0.1,
)

const columns = [
  { key: 'topic', label: t('topics.col_topic') },
  { key: 'questions', label: t('topics.col_questions'), align: 'right' as const },
  { key: 'likes', label: t('topics.col_likes'), align: 'right' as const },
  { key: 'curated', label: t('topics.col_curated') },
  { key: 'refusal', label: t('topics.col_refusal'), align: 'right' as const },
  { key: 'action', label: '' },
]
</script>

<template>
  <div>
    <PageHeader :title="t('topics.title')" />

    <p v-if="lainnyaHigh" class="mb-3 rounded-lg bg-warning-bg px-3 py-2 text-[13px] text-warning">
      {{ t('topics.lainnya_warning') }}
    </p>

    <div v-if="loading" class="py-12 text-center text-[14px] text-secondary">
      Memuat daftar topik...
    </div>

    <DataTable v-else :columns="columns">
      <tr
        v-for="topic in sorted"
        :key="topic.slug"
        class="border-t border-subtle transition hover:bg-raised/60"
      >
        <td class="px-3 py-2.5 text-[13.5px] text-primary">{{ topic.label }}</td>
        <td class="px-3 py-2.5 text-right text-[13px] text-primary">{{ topic.questions }}</td>
        <td class="px-3 py-2.5 text-right text-[13px] text-secondary">{{ topic.likes }}</td>
        <td class="px-3 py-2.5">
          <StatusChip
            :label="t(`topics.curated_${topic.curated || 'none'}`)"
            :tone="
              topic.curated === 'published'
                ? 'success'
                : topic.curated === 'draft'
                  ? 'warning'
                  : 'neutral'
            "
          />
          <span v-if="topic.curatedBy" class="meta mt-0.5 block">
            {{ topic.curatedBy }}
          </span>
        </td>
        <td
          class="px-3 py-2.5 text-right text-[13px]"
          :class="(topic.refusalRate || 0) > 0.15 ? 'text-warning' : 'text-secondary'"
        >
          {{ Math.round((topic.refusalRate || 0) * 100) }}%
        </td>
        <td class="px-3 py-2.5 text-right">
          <NuxtLink
            v-if="session.canEdit"
            :to="`/editor/${topic.slug}`"
            class="text-[13px] text-accent underline underline-offset-2"
          >
            {{ (!topic.curated || topic.curated === 'none') ? t('topics.write') : t('topics.edit') }}
          </NuxtLink>
        </td>
      </tr>
    </DataTable>
  </div>
</template>
