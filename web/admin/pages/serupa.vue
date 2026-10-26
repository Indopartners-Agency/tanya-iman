<script setup lang="ts">
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 11. Sorted by member count descending — read from the top,
 * this list is the content queue.
 *
 * Expanding a cluster shows its members in their original wording, which is
 * where the editorial insight lives: the canonical phrasing tells you the
 * theme, the raw wording tells you how people actually talk about it.
 *
 * Supports topic filtering, canonical phrasing renaming (PUT /clusters/{id}/rename),
 * and cluster merging (POST /clusters/{id}/merge) per PRD F-22.
 */
const { t } = useCopy()
const session = useSessionStore()
const api = useAdminApi()

const clusters = ref<any[]>([])
const topics = ref<any[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const toast = ref<string | null>(null)

const selectedTopic = ref<string>('')
const expanded = ref<string | null>(null)

// Rename modal state
const renameModalOpen = ref(false)
const renameTarget = ref<any>(null)
const renameCanonical = ref('')
const renameLoading = ref(false)

// Merge modal state
const mergeModalOpen = ref(false)
const mergeTarget = ref<any>(null)
const mergeSourceId = ref('')
const mergeLoading = ref(false)

// Delete modal state
const confirmDeleteOpen = ref(false)
const clusterToDelete = ref<any>(null)
const deleteLoading = ref(false)

async function loadData() {
  try {
    loading.value = true
    const [cData, tData] = await Promise.all([
      api.getClusters(),
      api.getTopics(),
    ])
    clusters.value = cData
    topics.value = tData
  } catch (e: any) {
    error.value = e?.message || 'Gagal memuat data kluster.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

const filteredClusters = computed(() => {
  let list = clusters.value
  if (selectedTopic.value) {
    list = list.filter((c) => c.topicSlug === selectedTopic.value)
  }
  return [...list].sort((a, b) => b.count - a.count)
})

function countForTopic(slug: string): number {
  return clusters.value.filter((c) => c.topicSlug === slug).length
}

function timeLabel(iso: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
}

// Rename handlers
function openRename(cluster: any) {
  renameTarget.value = cluster
  renameCanonical.value = cluster.canonical
  renameModalOpen.value = true
}

async function handleRename() {
  if (!renameTarget.value || !renameCanonical.value.trim()) return
  renameLoading.value = true
  try {
    const updated = await api.renameCluster(renameTarget.value.id, renameCanonical.value.trim())
    const idx = clusters.value.findIndex((c) => c.id === renameTarget.value.id)
    if (idx !== -1) {
      clusters.value[idx].canonical = updated.canonical
    }
    toast.value = `Berhasil mengubah nama kluster menjadi "${updated.canonical}"`
    renameModalOpen.value = false
  } catch (err: any) {
    toast.value = `Gagal mengubah nama: ${err?.message || 'Terjadi kesalahan'}`
  } finally {
    renameLoading.value = false
  }
}

// Merge handlers
function openMerge(cluster: any) {
  mergeTarget.value = cluster
  mergeSourceId.value = ''
  mergeModalOpen.value = true
}

// Eligible source clusters for merge (same topic preferred first)
const mergeCandidateClusters = computed(() => {
  if (!mergeTarget.value) return []
  return clusters.value
    .filter((c) => c.id !== mergeTarget.value.id)
    .sort((a, b) => {
      const aSame = a.topicSlug === mergeTarget.value.topicSlug ? 0 : 1
      const bSame = b.topicSlug === mergeTarget.value.topicSlug ? 0 : 1
      if (aSame !== bSame) return aSame - bSame
      return b.count - a.count
    })
})

async function handleMerge() {
  if (!mergeTarget.value || !mergeSourceId.value) return
  mergeLoading.value = true
  try {
    await api.mergeCluster(mergeTarget.value.id, mergeSourceId.value)
    toast.value = `Berhasil menggabungkan kluster.`
    mergeModalOpen.value = false
    await loadData()
  } catch (err: any) {
    toast.value = `Gagal menggabungkan kluster: ${err?.message || 'Terjadi kesalahan'}`
  } finally {
    mergeLoading.value = false
  }
}

// Delete handlers
function openDelete(cluster: any) {
  clusterToDelete.value = cluster
  confirmDeleteOpen.value = true
}

async function doDeleteCluster() {
  if (!clusterToDelete.value) return
  confirmDeleteOpen.value = false
  deleteLoading.value = true
  try {
    await api.deleteCluster(clusterToDelete.value.id)
    clusters.value = clusters.value.filter((c) => c.id !== clusterToDelete.value.id)
    toast.value = `Kluster berhasil dihapus.`
  } catch (err: any) {
    toast.value = `Gagal menghapus kluster: ${err?.message || 'Terjadi kesalahan'}`
  } finally {
    deleteLoading.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader :title="t('clusters.title')" />

    <!-- Filter & Toolbar -->
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <select
          v-model="selectedTopic"
          class="min-h-[40px] rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary outline-none focus:border-accent"
        >
          <option value="">{{ t('clusters.filter_all') }} ({{ clusters.length }})</option>
          <option v-for="top in topics" :key="top.slug" :value="top.slug">
            {{ top.label }} ({{ countForTopic(top.slug) }})
          </option>
        </select>
        <span class="meta">{{ filteredClusters.length }} kluster ditemukan</span>
      </div>
    </div>

    <!-- Notification toast -->
    <p v-if="toast" class="mb-3 rounded-lg bg-success-bg px-3 py-2 text-[13px] text-success">
      {{ toast }}
    </p>

    <!-- Content State -->
    <div v-if="loading" class="py-12 text-center text-secondary">Memuat kluster pertanyaan…</div>
    <div v-else-if="error" class="py-8 text-center text-sm text-danger">{{ error }}</div>
    <div v-else-if="filteredClusters.length === 0" class="py-12 text-center text-secondary text-sm">
      Belum ada kluster pertanyaan untuk topik ini.
    </div>

    <!-- Clusters Accordion List -->
    <div v-else class="space-y-2">
      <div
        v-for="cluster in filteredClusters"
        :key="cluster.id"
        class="rounded-xl border border-subtle bg-surface transition hover:border-strong"
      >
        <button
          type="button"
          class="flex w-full items-center gap-3 px-4 py-3 text-left"
          :aria-expanded="expanded === cluster.id"
          @click="expanded = expanded === cluster.id ? null : cluster.id"
        >
          <span class="tabular w-10 shrink-0 text-[15px] font-medium text-primary">
            {{ cluster.count }}
          </span>
          <span class="min-w-0 flex-1">
            <span class="block text-[13.5px] text-primary">{{ cluster.canonical }}</span>
            <span class="meta">
              {{ cluster.topicLabel }} · {{ t('clusters.col_last') }}
              {{ timeLabel(cluster.lastAsked) }}
            </span>
          </span>
          <StatusChip
            :label="cluster.hasCurated ? t('topics.curated_published') : t('topics.curated_none')"
            :tone="cluster.hasCurated ? 'success' : 'neutral'"
          />
        </button>

        <!-- Expanded panel -->
        <div v-if="expanded === cluster.id" class="border-t border-subtle px-4 py-3">
          <p class="meta mb-2">{{ t('clusters.members') }} ({{ cluster.members.length }})</p>
          <ul class="space-y-1.5 pl-1">
            <li
              v-for="member in cluster.members"
              :key="member"
              class="list-inside list-disc text-[13px] text-secondary"
            >
              {{ member }}
            </li>
          </ul>

          <!-- Action buttons -->
          <div class="mt-4 flex flex-wrap items-center gap-3 border-t border-subtle pt-3">
            <NuxtLink
              v-if="session.canEdit"
              :to="{
                path: `/editor/${cluster.topicSlug}`,
                query: { cluster: cluster.id, q: cluster.canonical },
              }"
              class="text-[13px] text-accent underline underline-offset-2 hover:opacity-80"
            >
              {{ t('clusters.make_curated') }}
            </NuxtLink>

            <button
              v-if="session.canEdit"
              type="button"
              class="rounded-lg border border-strong bg-raised px-2.5 py-1.5 text-[12.5px] text-primary transition hover:bg-subtle"
              @click="openRename(cluster)"
            >
              {{ t('clusters.rename') }}
            </button>

            <button
              v-if="session.canEdit"
              type="button"
              class="rounded-lg border border-strong bg-raised px-2.5 py-1.5 text-[12.5px] text-primary transition hover:bg-subtle"
              @click="openMerge(cluster)"
            >
              {{ t('clusters.merge') }}
            </button>

            <button
              v-if="session.canAdminister"
              type="button"
              class="rounded-lg bg-danger-bg px-2.5 py-1.5 text-[12.5px] text-danger transition hover:opacity-80"
              @click="openDelete(cluster)"
            >
              {{ t('clusters.delete') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Rename Modal -->
    <div
      v-if="renameModalOpen"
      class="fixed inset-0 z-50 grid place-items-center bg-primary/40 px-6"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-lg rounded-xl border border-subtle bg-surface p-5 shadow-lg">
        <h2 class="text-[16px] font-semibold text-primary">{{ t('clusters.rename_title') }}</h2>
        <p class="mt-1 text-[13px] text-secondary">{{ t('clusters.rename_desc') }}</p>

        <input
          v-model="renameCanonical"
          type="text"
          class="mt-3 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary outline-none focus:border-accent"
          placeholder="Formulasi pertanyaan umum…"
          @keyup.enter="handleRename"
        />

        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
            @click="renameModalOpen = false"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="button"
            :disabled="renameLoading || !renameCanonical.trim()"
            class="rounded-lg bg-accent px-3 py-2 text-[13px] text-on-accent transition hover:bg-accent-hover disabled:opacity-50"
            @click="handleRename"
          >
            {{ renameLoading ? 'Menyimpan…' : 'Simpan Perubahan' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Merge Modal -->
    <div
      v-if="mergeModalOpen"
      class="fixed inset-0 z-50 grid place-items-center bg-primary/40 px-6"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-lg rounded-xl border border-subtle bg-surface p-5 shadow-lg">
        <h2 class="text-[16px] font-semibold text-primary">{{ t('clusters.merge_title') }}</h2>
        <p class="mt-1 text-[13px] text-secondary">{{ t('clusters.merge_desc') }}</p>

        <div class="mt-3 rounded-lg bg-raised p-2.5 text-[13px]">
          <span class="meta block">Kluster Target:</span>
          <span class="text-primary font-medium">{{ mergeTarget?.canonical }}</span>
        </div>

        <label class="mt-3 block text-[13px] text-primary">Pilih Kluster Sumber:</label>
        <select
          v-model="mergeSourceId"
          class="mt-1 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary outline-none focus:border-accent"
        >
          <option value="">-- Pilih kluster untuk dilebur --</option>
          <option
            v-for="cand in mergeCandidateClusters"
            :key="cand.id"
            :value="cand.id"
          >
            {{ cand.canonical }} ({{ cand.count }} anggota, {{ cand.topicLabel }})
          </option>
        </select>

        <div class="mt-5 flex justify-end gap-2">
          <button
            type="button"
            class="rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
            @click="mergeModalOpen = false"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="button"
            :disabled="mergeLoading || !mergeSourceId"
            class="rounded-lg bg-accent px-3 py-2 text-[13px] text-on-accent transition hover:bg-accent-hover disabled:opacity-50"
            @click="handleMerge"
          >
            {{ mergeLoading ? 'Menggabungkan…' : 'Gabungkan Kluster' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Dialog -->
    <ConfirmDialog
      :open="confirmDeleteOpen"
      :title="t('clusters.delete')"
      :body="clusterToDelete ? `Hapus kluster '${clusterToDelete.canonical}' secara permanen?` : ''"
      danger
      @confirm="doDeleteCluster"
      @cancel="confirmDeleteOpen = false"
    />
  </div>
</template>
