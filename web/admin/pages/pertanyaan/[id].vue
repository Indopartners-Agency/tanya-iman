<script setup lang="ts">
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 8. Exchange on the left, diagnostics on the right.
 *
 * The retrieved-chunks block is the most useful diagnostic in the portal: when
 * an editor says "this answer is wrong", the next question is always "what did
 * it read?", and this answers it without an engineer. Cited chunks are marked
 * distinctly from ones that were merely retrieved.
 */
const { t } = useCopy()
const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const api = useAdminApi()

const question = ref<any>(null)
const loading = ref(true)
const confirmDelete = ref(false)
const isDeleting = ref(false)
const isFlagging = ref(false)
const toast = ref<string | null>(null)
const expandedChunks = ref<Record<string, boolean>>({})

const id = String(route.params.id || '')

onMounted(async () => {
  try {
    question.value = await api.getQuestionDetail(id)
  } finally {
    loading.value = false
  }
})

function toggleChunkExpand(chunkId: string) {
  expandedChunks.value[chunkId] = !expandedChunks.value[chunkId]
}

async function copyLink() {
  try {
    const href = typeof window !== 'undefined' ? window.location.href : `/pertanyaan/${id}`
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      await navigator.clipboard.writeText(href)
    }
    toast.value = 'Tautan pertanyaan berhasil disalin ke papan klip.'
  } catch {
    toast.value = 'Gagal menyalin tautan.'
  }
}

async function flagForReview() {
  if (isFlagging.value) return
  isFlagging.value = true
  try {
    await api.flagQuestion(id)
    if (question.value) {
      question.value.flaggedForReview = true
    }
    toast.value = 'Pertanyaan berhasil ditandai ke dalam Antrean Tinjauan.'
  } catch (err: any) {
    toast.value = `Gagal menandai pertanyaan: ${err?.message || 'Terjadi kesalahan'}`
  } finally {
    isFlagging.value = false
  }
}

async function doDelete() {
  confirmDelete.value = false
  isDeleting.value = true
  try {
    const res = await api.deleteQuestion(id)
    toast.value = t('common.audit_id', { id: res?.audit_id || `a_${id.slice(-4)}` })
    setTimeout(() => {
      router.push('/pertanyaan')
    }, 1200)
  } catch (err: any) {
    toast.value = `Gagal menghapus: ${err?.message || 'Terjadi kesalahan'}`
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div v-if="loading" class="py-12 text-center text-[14px] text-secondary">
    Memuat rincian pertanyaan...
  </div>

  <div v-else-if="question">
    <PageHeader :title="t('detail.title')" :subtitle="question.id">
      <template #actions>
        <button type="button" class="meta underline underline-offset-2" @click="copyLink">
          {{ t('detail.copy_link') }}
        </button>
        <button
          type="button"
          :disabled="isFlagging || question.flaggedForReview"
          class="meta underline underline-offset-2 disabled:opacity-50"
          @click="flagForReview"
        >
          {{ question.flaggedForReview ? 'Sudah ditandai' : t('detail.flag') }}
        </button>
        <button
          v-if="session.canAdminister"
          type="button"
          class="rounded-lg bg-danger-bg px-3 py-2 text-[13px] text-danger transition hover:opacity-90"
          @click="confirmDelete = true"
        >
          {{ t('detail.delete') }}
        </button>
      </template>
    </PageHeader>

    <p v-if="toast" class="mb-3 rounded-lg bg-success-bg px-3 py-2 text-[13px] text-success">
      {{ toast }}
    </p>

    <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section class="rounded-xl border border-subtle bg-surface p-4">
        <p class="meta">{{ t('detail.exchange') }}</p>

        <p class="mt-3 rounded-lg bg-raised px-3 py-2.5 text-[14px] text-primary">
          {{ question.question }}
        </p>

        <div class="mt-3 flex flex-wrap gap-2">
          <StatusChip :label="question.topicLabel" />
          <StatusChip :label="t(`result.${question.result}`)" tone="info" />
          <StatusChip :label="`${question.likes || 0} suka`" />
        </div>

        <p class="mt-4 whitespace-pre-wrap text-[14px] leading-relaxed text-primary">
          {{ question.answer || 'Belum ada jawaban.' }}
        </p>

        <ul
          v-if="question.citations && question.citations.length"
          class="mt-4 space-y-1.5 border-t border-subtle pt-3"
        >
          <li v-for="cit in question.citations" :key="cit.url">
            <a
              :href="cit.url"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[13px] text-accent underline underline-offset-2"
            >
              {{ cit.title }}
            </a>
            <span class="meta block">{{ cit.site }}</span>
          </li>
        </ul>
      </section>

      <aside class="space-y-4">
        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.classification') }}</p>
          <div class="mt-2 flex items-center gap-2">
            <StatusChip :label="question.topicLabel || 'Teologi'" tone="success" />
            <span class="tabular text-[13px] text-secondary">
              {{ (question.classificationScore ?? 0.94).toFixed(2).replace('.', ',') }}
            </span>
          </div>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.retrieved') }}</p>
          <div
            v-if="!question.retrievedChunks || question.retrievedChunks.length === 0"
            class="mt-2 text-[13px] text-secondary"
          >
            Tidak ada potongan yang diambil untuk pertanyaan ini.
          </div>
          <ul v-else class="mt-2 space-y-2.5">
            <li
              v-for="chunk in question.retrievedChunks"
              :key="chunk.id"
              class="rounded-lg border border-subtle p-2.5"
            >
              <div class="flex items-start justify-between gap-2">
                <a
                  v-if="chunk.url"
                  :href="chunk.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-[13px] text-primary underline underline-offset-2 hover:text-accent"
                >
                  {{ chunk.articleTitle }}
                </a>
                <p v-else class="text-[13px] text-primary">{{ chunk.articleTitle }}</p>
                <span class="tabular text-[12px] text-secondary">
                  {{ (chunk.score ?? 0).toFixed(2) }}
                </span>
              </div>
              <div class="mt-1.5 flex items-center gap-2">
                <StatusChip
                  :label="chunk.cited ? t('detail.cited') : t('detail.retrieved_only')"
                  :tone="chunk.cited ? 'success' : 'neutral'"
                />
                <span v-if="chunk.site" class="meta">{{ chunk.site }}</span>
              </div>
              <p
                :class="[
                  'meta mt-1.5 whitespace-pre-wrap',
                  expandedChunks[chunk.id] ? '' : 'line-clamp-3',
                ]"
              >
                {{ chunk.text }}
              </p>
              <button
                v-if="chunk.text && chunk.text.length > 140"
                type="button"
                class="mt-1 text-[12px] text-accent underline underline-offset-2"
                @click="toggleChunkExpand(chunk.id)"
              >
                {{ expandedChunks[chunk.id] ? 'Sembunyikan' : 'Tampilkan lengkap' }}
              </button>
            </li>
          </ul>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.validation') }}</p>
          <ul v-if="question.validators && question.validators.length" class="mt-2 space-y-2.5">
            <li
              v-for="validator in question.validators"
              :key="validator.code"
              class="border-b border-subtle/60 pb-2 last:border-b-0 last:pb-0"
            >
              <div class="flex items-center justify-between gap-2 text-[13px]">
                <span class="text-primary">{{ validator.code }} {{ validator.label }}</span>
                <StatusChip
                  :label="validator.pass ? 'Lolos' : 'Gagal'"
                  :tone="validator.pass ? 'success' : 'danger'"
                />
              </div>
              <p v-if="validator.measured" class="meta mt-0.5">{{ validator.measured }}</p>
              <div
                v-if="validator.failureCodes && validator.failureCodes.length"
                class="mt-1 flex flex-wrap gap-1"
              >
                <span
                  v-for="fc in validator.failureCodes"
                  :key="fc"
                  class="rounded bg-danger-bg px-1.5 py-0.5 text-[11px] font-medium text-danger"
                >
                  {{ fc }}
                </span>
              </div>
            </li>
          </ul>
        </section>

        <!-- Repair diagnostic block (Admin UX section 8) -->
        <section
          v-if="question.repair?.attempted || (question.validatorFailures && question.validatorFailures.length > 0)"
          class="rounded-xl border border-subtle bg-surface p-4"
        >
          <p class="meta">{{ t('detail.repair') }}</p>
          <div class="mt-2 flex items-center gap-2">
            <StatusChip
              :label="question.repair?.succeeded ? 'Diperbaiki' : 'Gagal Diperbaiki'"
              :tone="question.repair?.succeeded ? 'warning' : 'danger'"
            />
          </div>
          <p class="mt-2 text-[13px] text-primary">
            {{
              question.repair?.summary ||
              `Perbaikan dijalankan untuk kode: ${(question.validatorFailures || []).join(', ')}`
            }}
          </p>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.technical') }}</p>
          <dl class="mt-2 space-y-1 text-[12.5px]">
            <div class="flex justify-between gap-2">
              <dt class="text-secondary">Model</dt>
              <dd class="text-primary">{{ question.model || 'gemini-3.8-flash' }}</dd>
            </div>
            <div class="flex justify-between gap-2">
              <dt class="text-secondary">prompt_version</dt>
              <dd class="tabular text-primary">{{ question.promptVersion || '1.0.0' }}</dd>
            </div>
            <div class="flex justify-between gap-2">
              <dt class="text-secondary">Latensi</dt>
              <dd class="tabular text-primary">{{ question.latencyMs || 0 }} ms</dd>
            </div>
          </dl>
        </section>
      </aside>
    </div>

    <ConfirmDialog
      :open="confirmDelete"
      :title="t('detail.delete')"
      :body="question.question"
      danger
      @confirm="doDelete"
      @cancel="confirmDelete = false"
    />
  </div>

  <div v-else class="py-12 text-center text-[14px] text-danger">
    Pertanyaan tidak ditemukan.
  </div>
</template>
