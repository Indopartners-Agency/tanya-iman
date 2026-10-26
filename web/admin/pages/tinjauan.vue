<script setup lang="ts">
/**
 * Admin UX section 13 & Runbook section 6. One worklist, four sources:
 * - Flagged corpus chunks (terminology screening)
 * - Crisis events
 * - Validator failures
 * - Emotional-deferral samples & ambiguous classifications
 *
 * Crisis and emotional-deferral records are visible to every admin role but
 * carry a standing notice that they are sensitive and must not leave the
 * portal.
 */
const { t } = useCopy()
const api = useAdminApi()

const items = ref<any[]>([])
const loading = ref(true)
const expandedId = ref<string | null>(null)
const typeFilter = ref<string>('')
const noteInputs = ref<Record<string, string>>({})
const rewriteInputs = ref<Record<string, string>>({})
const busyId = ref<string | null>(null)
const toast = ref<string | null>(null)
const error = ref<string | null>(null)

async function loadReviews() {
  loading.value = true
  try {
    const data = await api.getReviews()
    items.value = data.map((d: any) => ({
      id: d.id,
      questionId: d.question_id || null,
      source: d.source || 'chunk',
      type: d.type || 'validator',
      summary: d.summary || '',
      detailText: d.detail_text || d.text || d.summary || '',
      url: d.url || '',
      site: d.site || '',
      matchedTerms: d.matched_terms || [],
      decision: d.decision || 'pending',
      note: d.note || '',
      at: d.at || '',
      reviewed: Boolean(d.reviewed),
    }))
    for (const item of items.value) {
      if (item.note && !noteInputs.value[item.id]) {
        noteInputs.value[item.id] = item.note
      }
      if (item.detailText && !rewriteInputs.value[item.id]) {
        rewriteInputs.value[item.id] = item.detailText
      }
    }
  } catch (e: any) {
    error.value = e?.message || 'Gagal memuat antrean tinjauan.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadReviews()
})

const filteredItems = computed(() => {
  if (!typeFilter.value) return items.value
  return items.value.filter((i) => i.type === typeFilter.value)
})

const toneFor: Record<string, 'warning' | 'danger' | 'info'> = {
  ambiguous: 'warning',
  validator: 'danger',
  crisis: 'danger',
  emotional: 'info',
}

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

async function submitDecision(item: any, decision = 'accept') {
  busyId.value = item.id
  error.value = null
  toast.value = null
  try {
    const note = noteInputs.value[item.id]?.trim() || undefined
    const rewritten =
      decision === 'rewrite' ? rewriteInputs.value[item.id]?.trim() || undefined : undefined
    await api.resolveReview(item.id, decision, note, rewritten)
    item.reviewed = true
    item.decision = decision
    if (note) item.note = note
    if (rewritten) item.detailText = rewritten
    toast.value = 'Status tinjauan berhasil disimpan.'
  } catch (e: any) {
    error.value = e?.message || 'Gagal menyimpan keputusan tinjauan.'
  } finally {
    busyId.value = null
  }
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

    <p v-if="toast" class="mb-3 rounded-lg bg-success-bg px-3 py-2 text-[13px] text-success">
      {{ toast }}
    </p>
    <p v-if="error" class="mb-3 rounded-lg bg-danger-bg px-3 py-2 text-[13px] text-danger">
      {{ error }}
    </p>

    <div class="mb-3 flex flex-wrap items-center gap-2">
      <select
        v-model="typeFilter"
        class="min-h-[40px] rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary"
      >
        <option value="">Semua Jenis ({{ items.length }})</option>
        <option value="validator">{{ t('review.type_validator') }}</option>
        <option value="crisis">{{ t('review.type_crisis') }}</option>
        <option value="emotional">{{ t('review.type_emotional') }}</option>
        <option value="ambiguous">{{ t('review.type_ambiguous') }}</option>
      </select>
    </div>

    <div v-if="loading" class="py-12 text-center text-secondary">Memuat…</div>
    <div v-else-if="filteredItems.length === 0" class="py-12 text-center text-sm text-secondary">
      Tidak ada item yang perlu ditinjau.
    </div>

    <DataTable v-else :columns="columns">
      <template v-for="item in filteredItems" :key="item.id">
        <tr
          :class="[
            'cursor-pointer border-t border-subtle transition hover:bg-raised/60',
            item.reviewed ? 'opacity-55' : '',
          ]"
          @click="toggleExpand(item.id)"
        >
          <td class="px-3 py-2.5">
            <StatusChip
              :label="t(`review.type_${item.type}`)"
              :tone="toneFor[item.type] || 'warning'"
            />
          </td>
          <td class="px-3 py-2.5 text-[13.5px] text-primary">
            <span class="font-medium">{{ item.summary }}</span>
            <span v-if="item.note" class="meta mt-0.5 block">Catatan: {{ item.note }}</span>
          </td>
          <td class="whitespace-nowrap px-3 py-2.5 text-[12.5px] text-secondary">
            {{ timeLabel(item.at) }}
          </td>
          <td class="px-3 py-2.5 text-right" @click.stop>
            <button
              v-if="!item.reviewed"
              type="button"
              :disabled="busyId === item.id"
              class="text-[13px] text-accent underline underline-offset-2 hover:opacity-80 disabled:opacity-40"
              @click="submitDecision(item, 'accept')"
            >
              {{ t('review.mark_reviewed') }}
            </button>
            <span v-else class="meta">&#10003; ({{ item.decision }})</span>
          </td>
        </tr>

        <!-- Expanded detail row -->
        <tr v-if="expandedId === item.id" class="border-t border-subtle bg-raised/40">
          <td colspan="4" class="px-4 py-3.5">
            <div class="space-y-3">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex flex-wrap items-center gap-2">
                  <span v-if="item.site" class="meta">Sumber: {{ item.site }}</span>
                  <span
                    v-for="term in item.matchedTerms"
                    :key="term"
                    class="rounded bg-danger-bg px-2 py-0.5 text-[11.5px] text-danger"
                  >
                    {{ term }}
                  </span>
                </div>
                <NuxtLink
                  v-if="item.questionId"
                  :to="`/pertanyaan/${item.questionId}`"
                  class="text-[13px] text-accent underline underline-offset-2"
                >
                  Lihat detail pertanyaan &rarr;
                </NuxtLink>
                <a
                  v-else-if="item.url"
                  :href="item.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-[13px] text-accent underline underline-offset-2"
                >
                  Buka artikel sumber &rarr;
                </a>
              </div>

              <div class="rounded-lg border border-subtle bg-surface p-3 text-[13.5px] leading-relaxed text-primary whitespace-pre-wrap">
                {{ item.detailText }}
              </div>

              <!-- Optional rewrite textarea for flagged corpus chunks -->
              <div v-if="item.source === 'chunk' && !item.reviewed" class="space-y-1.5">
                <label class="block text-[12.5px] text-secondary">
                  Tulis ulang teks potongan (opsional untuk keputusan Tulis Ulang):
                </label>
                <textarea
                  v-model="rewriteInputs[item.id]"
                  rows="3"
                  class="w-full rounded-lg border border-strong bg-surface p-2.5 text-[13px] text-primary outline-none focus:border-accent"
                />
              </div>

              <!-- Optional review note & actions -->
              <div class="flex flex-wrap items-center gap-2">
                <input
                  v-model="noteInputs[item.id]"
                  type="text"
                  :placeholder="t('review.note')"
                  class="min-h-[38px] flex-1 rounded-lg border border-strong bg-surface px-3 text-[13px] text-primary outline-none focus:border-accent"
                />
                <template v-if="item.source === 'chunk'">
                  <button
                    type="button"
                    :disabled="busyId === item.id"
                    class="rounded-lg bg-accent px-3 py-2 text-[12.5px] text-on-accent transition hover:bg-accent-hover disabled:opacity-40"
                    @click="submitDecision(item, 'accept')"
                  >
                    Terima (Accept)
                  </button>
                  <button
                    type="button"
                    :disabled="busyId === item.id"
                    class="rounded-lg border border-strong bg-surface px-3 py-2 text-[12.5px] text-primary transition hover:bg-raised disabled:opacity-40"
                    @click="submitDecision(item, 'rewrite')"
                  >
                    Tulis Ulang (Rewrite)
                  </button>
                  <button
                    type="button"
                    :disabled="busyId === item.id"
                    class="rounded-lg bg-danger-bg px-3 py-2 text-[12.5px] text-danger transition hover:opacity-80 disabled:opacity-40"
                    @click="submitDecision(item, 'exclude')"
                  >
                    Kecualikan (Exclude)
                  </button>
                </template>
                <button
                  v-else
                  type="button"
                  :disabled="busyId === item.id"
                  class="rounded-lg bg-accent px-3 py-2 text-[12.5px] text-on-accent transition hover:bg-accent-hover disabled:opacity-40"
                  @click="submitDecision(item, 'reviewed')"
                >
                  {{ t('review.mark_reviewed') }}
                </button>
              </div>
            </div>
          </td>
        </tr>
      </template>
    </DataTable>
  </div>
</template>
