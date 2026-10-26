<script setup lang="ts">
import { countWords, MAX_WORDS, MIN_WORDS } from '@tanya-iman/shared'

/**
 * Admin UX section 10 (F-14, F-23, F-34).
 *
 * The word counter imports countWords from web/shared, which is a deliberate
 * port of backend/services/text.py. Live V1–V4 rules mirror
 * backend/engine/validators.py so the editor gets immediate, accurate feedback.
 */
const { t } = useCopy()
const route = useRoute()
const api = useAdminApi()

interface CitationItem {
  id?: string
  article_id?: string | null
  title: string
  url: string
  site: string
}

const topic = ref<any>(null)
const corpusArticles = ref<CitationItem[]>([])
const loading = ref(true)

const answer = ref('')
const selectedCitations = ref<CitationItem[]>([])
const citationSearch = ref('')
const showPublishConfirm = ref(false)
const toast = ref<string | null>(null)
const error = ref<string | null>(null)
const busy = ref(false)

const slug = String(route.params.slug || '')
const clusterQuestion = computed(() => String(route.query.q || ''))

onMounted(async () => {
  try {
    const [data, articlesList] = await Promise.all([
      api.getTopic(slug),
      api.getArticles(),
    ])
    topic.value = data
    corpusArticles.value = articlesList || []

    if (data?.curatedAnswer) {
      answer.value = data.curatedAnswer
    }
    if (Array.isArray(data?.curatedCitations) && data.curatedCitations.length > 0) {
      selectedCitations.value = data.curatedCitations.map((c: any) => ({
        id: c.article_id || c.url,
        article_id: c.article_id || null,
        title: c.title,
        url: c.url,
        site: c.site,
      }))
    }
  } catch (e: any) {
    error.value = e?.message || 'Gagal memuat data topik atau artikel korpus.'
  } finally {
    loading.value = false
  }
})

/** V1 — length, counted with the backend's own function. */
const words = computed(() => countWords(answer.value))
const lengthOk = computed(() => words.value >= MIN_WORDS && words.value <= MAX_WORDS)

/**
 * V2 — terminology. The corpus and the product use "Allah" and "Isa Al-Masih";
 * "Tuhan", "Yesus", and "Jesus" must not reach a seeker, and at least one
 * mention of "Allah" or "Isa Al-Masih" is required.
 */
const BANNED = ['Tuhan', 'Yesus', 'Jesus']
const bannedFound = computed(() =>
  BANNED.filter((word) => new RegExp(`\\b${word}\\b`, 'i').test(answer.value)),
)
const requiredTermPresent = computed(() =>
  /\b(Allah|Isa\s+Al-Masih)\b/i.test(answer.value),
)
const terminologyOk = computed(
  () => bannedFound.value.length === 0 && requiredTermPresent.value,
)

/** Highlighted preview showing forbidden terms in context when present. */
const highlightedForbiddenHtml = computed(() => {
  if (bannedFound.value.length === 0) return ''
  const escaped = answer.value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  return escaped.replace(
    /\b(Tuhan|TUHAN|Yesus|Jesus)\b/gi,
    '<mark class="rounded bg-danger-bg px-1 font-semibold text-danger">$1</mark>',
  )
})

/** V3 — scripture balance across all 66 canonical Bible books and Quran refs. */
const BIBLE_BOOKS_PATTERN =
  '(?:(?:1|I)\\s+Samuel|(?:2|II)\\s+Samuel|(?:1|I)\\s+Raja-raja|(?:2|II)\\s+Raja-raja|' +
  '(?:1|I)\\s+Tawarikh|(?:2|II)\\s+Tawarikh|Kidung\\s+Agung|Kisah\\s+Para\\s+Rasul|' +
  '(?:1|I)\\s+Korintus|(?:2|II)\\s+Korintus|(?:1|I)\\s+Tesalonika|(?:2|II)\\s+Tesalonika|' +
  '(?:1|I)\\s+Timotius|(?:2|II)\\s+Timotius|(?:1|I)\\s+Petrus|(?:2|II)\\s+Petrus|' +
  '(?:1|I)\\s+Yohanes|(?:2|II)\\s+Yohanes|(?:3|III)\\s+Yohanes|Kejadian|Keluaran|Imamat|' +
  'Bilangan|Ulangan|Yosua|Hakim-hakim|Rut|Ezra|Nehemia|Ester|Ayub|Mazmur|Amsal|' +
  'Pengkhotbah|Yesaya|Yeremia|Ratapan|Yehezkiel|Daniel|Hosea|Yoel|Amos|Obaja|Yunus|' +
  'Mikha|Nahum|Habakuk|Zefanya|Hagai|Zakharia|Maleakhi|Matius|Markus|Lukas|Yohanes|' +
  'Roma|Galatia|Efesus|Filipi|Kolose|Titus|Filemon|Ibrani|Yakobus|Yudas|Wahyu)'

const BIBLE_RE = new RegExp(`\\b${BIBLE_BOOKS_PATTERN}\\s+\\d+(?::\\d+(?:-\\d+)?)?`, 'gi')
const QURAN_RE = new RegExp(
  `\\b(?:Qs\\.|QS|Surah|Surat)\\s+(?!(?:${BIBLE_BOOKS_PATTERN}|Paulus|Rasul\\s+Paulus|Kiriman)\\b)([A-Za-z0-9\\-]+(?:\\s+[0-9]+(?::[0-9]+)?)?)`,
  'gi',
)

const quranMatches = computed(() => [...answer.value.matchAll(QURAN_RE)])
const bibleMatches = computed(() => [...answer.value.matchAll(BIBLE_RE)])
const quranRefs = computed(() => quranMatches.value.length)
const scriptureRefs = computed(() => bibleMatches.value.length)

const quranLeadingOk = computed(() => {
  if (quranRefs.value !== 1) return true
  const firstMatch = quranMatches.value[0]
  if (!firstMatch || firstMatch.index === undefined || words.value === 0) return true
  const wordsBefore = countWords(answer.value.slice(0, firstMatch.index))
  return wordsBefore / words.value <= 0.25
})

const scriptureOk = computed(() => {
  if (quranRefs.value > 1) return false
  if (quranRefs.value === 1) {
    return quranLeadingOk.value && scriptureRefs.value >= 2
  }
  return true
})

const scriptureMessage = computed(() => {
  if (quranRefs.value > 1) {
    return `Maksimal 1 rujukan Al-Quran (saat ini ${quranRefs.value}).`
  }
  if (quranRefs.value === 1 && !quranLeadingOk.value) {
    return 'Rujukan Al-Quran harus berada di 25% awal jawaban.'
  }
  if (quranRefs.value === 1 && scriptureRefs.value < 2) {
    return `Rujukan Al-Quran wajib disertai minimal 2 rujukan Alkitab (saat ini ${scriptureRefs.value}).`
  }
  return `${quranRefs.value} rujukan Quran, ${scriptureRefs.value} rujukan Kitab Suci`
})

/** V4 — one or two citations, from approved sites only. */
const citationsOk = computed(
  () => selectedCitations.value.length >= 1 && selectedCitations.value.length <= 2,
)

const canPublish = computed(
  () => lengthOk.value && terminologyOk.value && scriptureOk.value && citationsOk.value,
)

const filteredArticles = computed(() => {
  const q = citationSearch.value.trim().toLowerCase()
  return corpusArticles.value.filter((a) =>
    q ? a.title.toLowerCase().includes(q) || a.site.toLowerCase().includes(q) : true,
  )
})

function isCitationSelected(article: CitationItem): boolean {
  return selectedCitations.value.some(
    (c) => (c.url && article.url && c.url === article.url) || (c.id && c.id === article.id),
  )
}

function toggleCitation(article: CitationItem) {
  const index = selectedCitations.value.findIndex(
    (c) => (c.url && article.url && c.url === article.url) || (c.id && c.id === article.id),
  )
  if (index >= 0) {
    selectedCitations.value.splice(index, 1)
  } else if (selectedCitations.value.length < 2) {
    selectedCitations.value.push({
      id: article.id,
      article_id: article.id || null,
      title: article.title,
      url: article.url,
      site: article.site,
    })
  }
}

function formatCitationsPayload() {
  return selectedCitations.value.map((c) => ({
    title: c.title,
    url: c.url,
    site: c.site,
    article_id: c.article_id || c.id || null,
  }))
}

async function saveDraft() {
  busy.value = true
  error.value = null
  toast.value = null
  try {
    await api.updateTopicAnswer(slug, answer.value, 'draft', formatCitationsPayload())
    toast.value = t('common.saved')
  } catch (e: any) {
    error.value = e?.message || 'Gagal menyimpan draf'
  } finally {
    busy.value = false
  }
}

async function publish() {
  showPublishConfirm.value = false
  busy.value = true
  error.value = null
  toast.value = null
  try {
    await api.updateTopicAnswer(slug, answer.value, 'published', formatCitationsPayload())
    toast.value = t('common.saved')
  } catch (e: any) {
    error.value = e?.message || 'Gagal mempublikasikan jawaban'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <RoleGate need="edit">
    <div>
      <PageHeader :title="t('editor.title')" :subtitle="topic?.label">
        <template #actions>
          <button
            type="button"
            :disabled="busy"
            class="rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised disabled:opacity-40"
            @click="saveDraft"
          >
            {{ t('editor.save_draft') }}
          </button>
          <button
            type="button"
            :disabled="!canPublish || busy"
            class="rounded-lg bg-accent px-3 py-2 text-[13px] text-on-accent transition hover:bg-accent-hover disabled:opacity-40"
            @click="showPublishConfirm = true"
          >
            {{ t('editor.publish') }}
          </button>
        </template>
      </PageHeader>

      <p v-if="toast" class="mb-3 rounded-lg bg-success-bg px-3 py-2 text-[13px] text-success">
        {{ toast }}
      </p>

      <p v-if="error" class="mb-3 rounded-lg bg-danger-bg px-3 py-2 text-[13px] text-danger">
        {{ error }}
      </p>

      <div
        v-if="clusterQuestion"
        class="mb-4 rounded-xl border border-subtle bg-info-bg px-4 py-3 text-[13px] text-info"
      >
        <span class="font-medium">Konteks Kluster Pertanyaan:</span>
        “{{ clusterQuestion }}”
      </div>

      <!-- Section 16: the editor is not offered below 768px. -->
      <p class="rounded-lg bg-warning-bg px-3 py-2 text-[13px] text-warning md:hidden">
        {{ t('editor.too_narrow') }}
      </p>

      <div class="hidden gap-4 md:grid md:grid-cols-[minmax(0,1fr)_300px]">
        <section>
          <label for="answer" class="block text-[13px] font-medium text-primary">
            {{ t('editor.answer_label') }}
          </label>
          <textarea
            id="answer"
            v-model="answer"
            rows="14"
            class="mt-1.5 w-full resize-y rounded-xl border border-strong bg-surface p-3 text-[14px] leading-relaxed text-primary outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
          />

          <div
            v-if="bannedFound.length > 0"
            class="mt-2 rounded-lg border border-danger/40 bg-surface p-3 text-[13px] leading-relaxed text-primary"
          >
            <p class="meta mb-1 text-danger">Sorotan kata terlarang (V2):</p>
            <!-- eslint-disable-next-line vue/no-v-html -->
            <p class="whitespace-pre-wrap" v-html="highlightedForbiddenHtml" />
          </div>

          <p class="meta mt-2">{{ t('editor.draft_notice') }}</p>

          <div class="mt-5">
            <label for="citation-search" class="block text-[13px] font-medium text-primary">
              {{ t('editor.rule_citations') }}
            </label>

            <!-- Selected citations summary -->
            <div v-if="selectedCitations.length > 0" class="mt-2 flex flex-wrap gap-2">
              <span
                v-for="cit in selectedCitations"
                :key="cit.url"
                class="inline-flex items-center gap-1.5 rounded-full border border-accent bg-info-bg px-3 py-1 text-[12.5px] text-primary"
              >
                <span>{{ cit.title }} ({{ cit.site }})</span>
                <button
                  type="button"
                  class="text-secondary hover:text-danger"
                  @click="toggleCitation(cit)"
                >
                  &times;
                </button>
              </span>
            </div>

            <!-- Section 10: no free-text URL field exists, so an off-allowlist
                 link cannot be entered at all. -->
            <input
              id="citation-search"
              v-model="citationSearch"
              type="search"
              :placeholder="t('editor.citation_search')"
              class="mt-2 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary outline-none focus:border-accent"
            />
            <ul class="mt-2 max-h-64 space-y-1.5 overflow-y-auto">
              <li v-for="article in filteredArticles" :key="article.id || article.url">
                <button
                  type="button"
                  :class="[
                    'flex w-full items-start gap-2 rounded-lg border px-3 py-2 text-left transition',
                    isCitationSelected(article)
                      ? 'border-accent bg-info-bg'
                      : 'border-subtle hover:bg-raised',
                  ]"
                  @click="toggleCitation(article)"
                >
                  <span class="min-w-0 flex-1">
                    <span class="block text-[13px] text-primary">{{ article.title }}</span>
                    <span class="meta">{{ article.site }}</span>
                  </span>
                  <span v-if="isCitationSelected(article)" class="text-accent">
                    &#10003;
                  </span>
                </button>
              </li>
            </ul>
          </div>
        </section>

        <!-- The live rule panel. Updates per keystroke. -->
        <aside class="space-y-2.5">
          <p class="meta">{{ t('editor.rules') }}</p>

          <div
            :class="[
              'rounded-lg border px-3 py-2.5',
              lengthOk ? 'border-success/40 bg-success-bg' : 'border-danger/40 bg-danger-bg',
            ]"
          >
            <p :class="['text-[12px]', lengthOk ? 'text-success' : 'text-danger']">
              V1 {{ t('editor.rule_length') }}
            </p>
            <p :class="['tabular mt-0.5 text-[13.5px]', lengthOk ? 'text-success' : 'text-danger']">
              {{ t('editor.words', { count: words }) }}
            </p>
          </div>

          <div
            :class="[
              'rounded-lg border px-3 py-2.5',
              terminologyOk ? 'border-success/40 bg-success-bg' : 'border-danger/40 bg-danger-bg',
            ]"
            aria-live="polite"
          >
            <p :class="['text-[12px]', terminologyOk ? 'text-success' : 'text-danger']">
              V2 {{ t('editor.rule_terminology') }}
            </p>
            <p :class="['mt-0.5 text-[13px]', terminologyOk ? 'text-success' : 'text-danger']">
              <template v-if="bannedFound.length > 0">
                {{ t('editor.terminology_bad', { word: bannedFound[0] ?? '' }) }}
              </template>
              <template v-else-if="!requiredTermPresent">
                Wajib memuat sebutan ‘Allah’ atau ‘Isa Al-Masih’.
              </template>
              <template v-else>
                {{ t('editor.terminology_ok') }}
              </template>
            </p>
          </div>

          <div
            :class="[
              'rounded-lg border px-3 py-2.5',
              scriptureOk ? 'border-subtle bg-surface' : 'border-danger/40 bg-danger-bg',
            ]"
          >
            <p :class="['text-[12px]', scriptureOk ? 'meta' : 'text-danger']">
              V3 {{ t('editor.rule_scripture') }}
            </p>
            <p :class="['mt-0.5 text-[13px]', scriptureOk ? 'text-primary' : 'text-danger']">
              {{ scriptureMessage }}
            </p>
          </div>

          <div
            :class="[
              'rounded-lg border px-3 py-2.5',
              citationsOk ? 'border-success/40 bg-success-bg' : 'border-danger/40 bg-danger-bg',
            ]"
          >
            <p :class="['text-[12px]', citationsOk ? 'text-success' : 'text-danger']">
              V4 {{ t('editor.rule_citations') }}
            </p>
            <p
              :class="['tabular mt-0.5 text-[13px]', citationsOk ? 'text-success' : 'text-danger']"
            >
              {{ t('editor.citations_count', { count: selectedCitations.length }) }}
            </p>
          </div>
        </aside>
      </div>

      <ConfirmDialog
        :open="showPublishConfirm"
        :title="t('editor.publish')"
        :body="t('editor.publish_confirm')"
        @confirm="publish"
        @cancel="showPublishConfirm = false"
      />
    </div>
  </RoleGate>
</template>
