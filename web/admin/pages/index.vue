<script setup lang="ts">
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 6. Five cards, each linking to the view behind it.
 *
 * The answer-health card turns danger and says so plainly whenever the
 * validator pass rate is not 100%. It is a release gate (K4), and a dashboard
 * that lets it slide past as one number among five is not doing its job.
 */
const { t } = useCopy()
const session = useSessionStore()
const router = useRouter()
const api = useAdminApi()

const loading = ref(true)
const dashboard = ref({
  volumeThisWeek: 0,
  volumeChangePct: 15,
  validatorPassPct: 100,
  answerRatePct: 100,
  likeRatePct: 0,
})
const gaps = ref<any[]>([])
const reviewCount = ref(0)
const topTopics = ref<any[]>([])

onMounted(async () => {
  if (!session.isAuthenticated) {
    await router.replace('/masuk')
    return
  }

  try {
    const data = await api.getDashboard()
    dashboard.value = {
      volumeThisWeek: data.total_questions,
      volumeChangePct: data.volume_change_pct,
      validatorPassPct: data.validator_pass_pct,
      answerRatePct: data.answer_rate_pct,
      likeRatePct: data.like_rate_pct,
    }
    reviewCount.value = data.review_items
    topTopics.value = data.top_topics || []

    const gapsData = await api.getGaps()
    gaps.value = gapsData || []
  } finally {
    loading.value = false
  }
})

const validatorFailing = computed(() => dashboard.value.validatorPassPct < 100)
const topFive = computed(() => topTopics.value.slice(0, 5))
const largestGap = computed(() => gaps.value[0])
</script>

<template>
  <div>
    <PageHeader :title="t('dashboard.title')" :subtitle="t('dashboard.subtitle')" />

    <div v-if="loading" class="py-12 text-center text-[14px] text-secondary">
      Memuat data analitik...
    </div>

    <div v-else class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <StatCard
        :label="t('dashboard.volume')"
        :value="String(dashboard.volumeThisWeek)"
        to="/pertanyaan"
      >
        <p class="meta">
          {{ t('dashboard.volume_change', { change: `+${dashboard.volumeChangePct}%` }) }}
        </p>
      </StatCard>

      <StatCard :label="t('dashboard.gaps')" :value="String(gaps.length)" to="/kekosongan">
        <p v-if="largestGap" class="meta">
          {{ t('dashboard.gaps_largest', { name: largestGap.canonical }) }}
        </p>
      </StatCard>

      <StatCard :label="t('dashboard.review')" :value="String(reviewCount)" to="/tinjauan">
        <p class="meta">{{ t('dashboard.review_items', { count: reviewCount }) }}</p>
      </StatCard>

      <StatCard
        :label="t('dashboard.health')"
        :value="`${dashboard.validatorPassPct}%`"
        :alert="validatorFailing"
        to="/pertanyaan?validator=gagal"
      >
        <p class="meta">
          {{ t('dashboard.health_answer_rate') }} {{ dashboard.answerRatePct }}% ·
          {{ t('dashboard.health_like_rate') }} {{ dashboard.likeRatePct }}%
        </p>
        <p v-if="validatorFailing" class="mt-1.5 text-[12.5px] text-danger">
          {{ t('dashboard.health_alert') }}
        </p>
      </StatCard>

      <div class="rounded-xl border border-subtle bg-surface p-4 sm:col-span-2">
        <p class="meta">{{ t('dashboard.top_topics') }}</p>
        <ul class="mt-2 divide-y divide-subtle">
          <li
            v-for="topic in topFive"
            :key="topic.slug"
            class="flex items-center justify-between gap-3 py-2"
          >
            <NuxtLink to="/topik" class="text-[13.5px] text-primary hover:text-accent">
              {{ topic.label }}
            </NuxtLink>
            <div class="flex items-center gap-2">
              <StatusChip
                :label="t(`topics.curated_${topic.curated}`)"
                :tone="
                  topic.curated === 'published'
                    ? 'success'
                    : topic.curated === 'draft'
                      ? 'warning'
                      : 'neutral'
                "
              />
              <span class="tabular text-[13px] text-secondary">{{ topic.questions }}</span>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
