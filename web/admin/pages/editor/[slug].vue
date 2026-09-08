<script setup lang="ts">
import { countWords, MAX_WORDS, MIN_WORDS } from '@tanya-iman/shared'
import { articles, topics } from '~/demo/fixtures'

/**
 * Admin UX section 10 (F-23, F-34).
 *
 * The word counter imports countWords from web/shared, which is a deliberate
 * port of backend/services/text.py. If this counter said 249 and the backend
 * said 251, the editor would stop trusting the tool and the whole idea of live
 * validation would be worth less than nothing.
 *
 * Not offered below 768px (section 16): writing a 250-word answer against live
 * validation on a phone is not a workflow worth designing for.
 */
const { t } = useCopy()
const route = useRoute()

const topic = computed(() => topics.find((tp) => tp.slug === route.params.slug))

const answer = ref('')
const selectedCitations = ref<string[]>([])
const citationSearch = ref('')
const showPublishConfirm = ref(false)
const toast = ref<string | null>(null)

/** V1 — length, counted with the backend's own function. */
const words = computed(() => countWords(answer.value))
const lengthOk = computed(() => words.value >= MIN_WORDS && words.value <= MAX_WORDS)

/**
 * V2 — terminology. The corpus and the product use "Allah" and "Isa Al-Masih";
 * "Tuhan" and "Yesus" are the two substitutions that must not reach a seeker.
 */
const BANNED = ['Tuhan', 'Yesus']
const bannedFound = computed(() =>
  BANNED.filter((word) => new RegExp(`\\b${word}\\b`, 'i').test(answer.value)),
)
const terminologyOk = computed(() => bannedFound.value.length === 0)

/** V3 — scripture balance, stated in words rather than as a code. */
const quranRefs = computed(() => (answer.value.match(/Q\.?S\.?\s?\d+/gi) ?? []).length)
const scriptureRefs = computed(
  () => (answer.value.match(/\b(Yohanes|Matius|Lukas|Markus|Mazmur|Kejadian)\b/gi) ?? []).length,
)

/** V4 — one or two citations, from approved sites only. */
const citationsOk = computed(
  () => selectedCitations.value.length >= 1 && selectedCitations.value.length <= 2,
)

const canPublish = computed(() => lengthOk.value && terminologyOk.value && citationsOk.value)

const filteredArticles = computed(() =>
  articles.filter((a) =>
    citationSearch.value
      ? a.title.toLowerCase().includes(citationSearch.value.toLowerCase())
      : true,
  ),
)

function toggleCitation(id: string) {
  const index = selectedCitations.value.indexOf(id)
  if (index >= 0) selectedCitations.value.splice(index, 1)
  else if (selectedCitations.value.length < 2) selectedCitations.value.push(id)
}

function saveDraft() {
  toast.value = t('common.saved')
}

function publish() {
  showPublishConfirm.value = false
  toast.value = t('common.saved')
}
</script>

<template>
  <RoleGate need="edit">
    <div>
      <PageHeader :title="t('editor.title')" :subtitle="topic?.label">
        <template #actions>
          <button
            type="button"
            class="rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
            @click="saveDraft"
          >
            {{ t('editor.save_draft') }}
          </button>
          <button
            type="button"
            :disabled="!canPublish"
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

          <p class="meta mt-2">{{ t('editor.draft_notice') }}</p>

          <div class="mt-5">
            <label for="citation-search" class="block text-[13px] font-medium text-primary">
              {{ t('editor.rule_citations') }}
            </label>
            <!-- Section 10: no free-text URL field exists, so an off-allowlist
                 link cannot be entered at all. -->
            <input
              id="citation-search"
              v-model="citationSearch"
              type="search"
              :placeholder="t('editor.citation_search')"
              class="mt-1.5 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary outline-none focus:border-accent"
            />
            <ul class="mt-2 space-y-1.5">
              <li v-for="article in filteredArticles" :key="article.id">
                <button
                  type="button"
                  :class="[
                    'flex w-full items-start gap-2 rounded-lg border px-3 py-2 text-left transition',
                    selectedCitations.includes(article.id)
                      ? 'border-accent bg-info-bg'
                      : 'border-subtle hover:bg-raised',
                  ]"
                  @click="toggleCitation(article.id)"
                >
                  <span class="min-w-0 flex-1">
                    <span class="block text-[13px] text-primary">{{ article.title }}</span>
                    <span class="meta">{{ article.site }}</span>
                  </span>
                  <span v-if="selectedCitations.includes(article.id)" class="text-accent">
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
              {{
                terminologyOk
                  ? t('editor.terminology_ok')
                  : t('editor.terminology_bad', { word: bannedFound[0] ?? '' })
              }}
            </p>
          </div>

          <div class="rounded-lg border border-subtle bg-surface px-3 py-2.5">
            <p class="meta">V3 {{ t('editor.rule_scripture') }}</p>
            <p class="mt-0.5 text-[13px] text-primary">
              {{ quranRefs }} rujukan Quran, {{ scriptureRefs }} rujukan Kitab Suci
            </p>
          </div>

          <div
            :class="[
              'rounded-lg border px-3 py-2.5',
              citationsOk ? 'border-success/40 bg-success-bg' : 'border-subtle bg-surface',
            ]"
          >
            <p :class="['text-[12px]', citationsOk ? 'text-success' : 'text-secondary']">
              V4 {{ t('editor.rule_citations') }}
            </p>
            <p
              :class="['tabular mt-0.5 text-[13px]', citationsOk ? 'text-success' : 'text-primary']"
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
