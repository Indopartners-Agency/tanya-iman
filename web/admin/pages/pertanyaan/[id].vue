<script setup lang="ts">
import { questions, retrievedChunks, validators } from '~/demo/fixtures'
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
const session = useSessionStore()

const question = computed(() => questions.find((q) => q.id === route.params.id))
const citedChunks = computed(() => retrievedChunks.filter((c) => c.cited))
const confirmDelete = ref(false)
const toast = ref<string | null>(null)

function doDelete() {
  confirmDelete.value = false
  // F-37: the success toast carries the audit entry id.
  toast.value = t('common.audit_id', { id: 'a_913' })
}
</script>

<template>
  <div v-if="question">
    <PageHeader :title="t('detail.title')" :subtitle="question.id">
      <template #actions>
        <button type="button" class="meta underline underline-offset-2">
          {{ t('detail.copy_link') }}
        </button>
        <button type="button" class="meta underline underline-offset-2">
          {{ t('detail.flag') }}
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
          <StatusChip :label="`${question.likes} suka`" />
        </div>

        <p class="mt-4 whitespace-pre-wrap text-[14px] leading-relaxed text-primary">
          Kitab Suci memperkenalkan Isa Al-Masih sebagai Firman Allah yang menjadi
          manusia. Ia disebut telah ada sejak semula bersama Allah, lalu hadir di
          tengah manusia untuk menyatakan kasih dan kebenaran-Nya.
        </p>

        <ul class="mt-4 space-y-1.5 border-t border-subtle pt-3">
          <li v-for="chunk in citedChunks" :key="chunk.id">
            <a
              :href="`https://${chunk.site}`"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[13px] text-accent underline underline-offset-2"
            >
              {{ chunk.articleTitle }}
            </a>
            <span class="meta block">{{ chunk.site }}</span>
          </li>
        </ul>
      </section>

      <aside class="space-y-4">
        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.classification') }}</p>
          <div class="mt-2 flex items-center gap-2">
            <StatusChip label="Teologi" tone="success" />
            <span class="tabular text-[13px] text-secondary">0,94</span>
          </div>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.retrieved') }}</p>
          <ul class="mt-2 space-y-2.5">
            <li
              v-for="chunk in retrievedChunks"
              :key="chunk.id"
              class="rounded-lg border border-subtle p-2.5"
            >
              <div class="flex items-start justify-between gap-2">
                <p class="text-[13px] text-primary">{{ chunk.articleTitle }}</p>
                <span class="tabular text-[12px] text-secondary">
                  {{ chunk.score.toFixed(2) }}
                </span>
              </div>
              <div class="mt-1.5">
                <StatusChip
                  :label="chunk.cited ? t('detail.cited') : t('detail.retrieved_only')"
                  :tone="chunk.cited ? 'success' : 'neutral'"
                />
              </div>
              <p class="meta mt-1.5 line-clamp-2">{{ chunk.text }}</p>
            </li>
          </ul>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.validation') }}</p>
          <ul class="mt-2 space-y-1.5">
            <li
              v-for="validator in validators"
              :key="validator.code"
              class="flex items-center justify-between gap-2 text-[13px]"
            >
              <span class="text-primary">{{ validator.code }} {{ validator.label }}</span>
              <StatusChip
                :label="validator.pass ? 'Lolos' : 'Gagal'"
                :tone="validator.pass ? 'success' : 'danger'"
              />
            </li>
          </ul>
          <p v-if="validators[0]" class="meta mt-2">{{ validators[0].measured }}</p>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.technical') }}</p>
          <dl class="mt-2 space-y-1 text-[12.5px]">
            <div class="flex justify-between gap-2">
              <dt class="text-secondary">Model</dt>
              <dd class="text-primary">claude-sonnet-class</dd>
            </div>
            <div class="flex justify-between gap-2">
              <dt class="text-secondary">prompt_version</dt>
              <dd class="tabular text-primary">v3</dd>
            </div>
            <div class="flex justify-between gap-2">
              <dt class="text-secondary">Latensi</dt>
              <dd class="tabular text-primary">4.120 ms</dd>
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
</template>
