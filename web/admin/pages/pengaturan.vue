<script setup lang="ts">
/**
 * Admin UX section 14. super_admin only.
 *
 * The support contact (F-45) is shown as unset until configured by the client's
 * pastoral team (SOW dependency B1). Placeholder values are rejected client-side
 * and server-side.
 */
const { t } = useCopy()
const api = useAdminApi()

const config = ref<Record<string, string>>({
  retention_months: '12',
  rate_limit_per_hour: '30',
  similarity_threshold: '0.72',
  contact_name: '',
  contact_number: '',
})
const initialSimilarity = ref('0.72')
const systemSaved = ref(false)
const contactSaved = ref(false)
const systemError = ref<string | null>(null)
const contactError = ref<string | null>(null)
const confirmSimilarityOpen = ref(false)
const confirmContactOpen = ref(false)
const confirmIngestionOpen = ref(false)

const ingestion = ref<{
  status: string
  sites_count: number
  articles_count: number
  chunks_count: number
  last_run_at: string | null
}>({
  status: 'idle',
  sites_count: 5,
  articles_count: 0,
  chunks_count: 0,
  last_run_at: null,
})
const ingestionRunning = ref(false)

const accounts = ref<Array<{ id: string; email: string; role: string }>>([])
const newAccountEmail = ref('')
const newAccountPassword = ref('')
const newAccountRole = ref<'editor' | 'reviewer' | 'super_admin'>('editor')
const accountError = ref<string | null>(null)

const auditLogs = ref<any[]>([])
const auditLoading = ref(true)
const auditActorFilter = ref('')
const auditActionFilter = ref('')
const auditDateFrom = ref('')
const auditDateTo = ref('')

const PLACEHOLDER_RE = /(?:placeholder|tbd|todo|xxx|08xx|0000|contoh|belum)/i

const isContactPlaceholder = computed(() => {
  const name = (config.value.contact_name || '').trim()
  const num = (config.value.contact_number || '').trim()
  return !name || !num || PLACEHOLDER_RE.test(name) || PLACEHOLDER_RE.test(num)
})

async function refreshAudit() {
  auditLoading.value = true
  try {
    auditLogs.value =
      (await api.getAuditLogs({
        actor: auditActorFilter.value || undefined,
        action: auditActionFilter.value || undefined,
        dateFrom: auditDateFrom.value || undefined,
        dateTo: auditDateTo.value || undefined,
      })) || []
  } catch (e) {
    console.warn('Failed to load audit logs:', e)
  } finally {
    auditLoading.value = false
  }
}

onMounted(async () => {
  try {
    const [data, logs, ingestStatus, acctList] = await Promise.all([
      api.getConfig(),
      api.getAuditLogs(),
      api.getIngestionStatus(),
      api.getAdminAccounts(),
    ])
    if (data) {
      config.value = {
        ...config.value,
        ...data,
        contact_name: data.contact_name === 'PLACEHOLDER' ? '' : (data.contact_name ?? ''),
        contact_number: data.contact_number === 'PLACEHOLDER' ? '' : (data.contact_number ?? ''),
      }
      initialSimilarity.value = config.value.similarity_threshold
    }
    auditLogs.value = logs || []
    if (ingestStatus) ingestion.value = { ...ingestion.value, ...ingestStatus }
    if (acctList) accounts.value = acctList
  } catch (e) {
    console.warn('Failed to load system config or audit logs:', e)
  } finally {
    auditLoading.value = false
  }
})

function requestSaveSystem() {
  systemError.value = null
  systemSaved.value = false
  if (config.value.similarity_threshold !== initialSimilarity.value) {
    confirmSimilarityOpen.value = true
    return
  }
  void saveSystemConfig()
}

async function saveSystemConfig() {
  confirmSimilarityOpen.value = false
  systemError.value = null
  try {
    await api.updateConfig('retention_months', String(config.value.retention_months))
    await api.updateConfig('rate_limit_per_hour', String(config.value.rate_limit_per_hour))
    await api.updateConfig('similarity_threshold', String(config.value.similarity_threshold))
    initialSimilarity.value = String(config.value.similarity_threshold)
    systemSaved.value = true
    await refreshAudit()
  } catch (err: any) {
    systemError.value = err?.message || 'Gagal menyimpan pengaturan sistem.'
  }
}

function requestSaveContact() {
  contactError.value = null
  contactSaved.value = false
  const name = (config.value.contact_name || '').trim()
  const number = (config.value.contact_number || '').trim()
  if (!name || !number || PLACEHOLDER_RE.test(name) || PLACEHOLDER_RE.test(number)) {
    contactError.value =
      'Nama dan nomor kontak dukungan harus diisi dengan nilai resmi (bukan PLACEHOLDER).'
    return
  }
  confirmContactOpen.value = true
}

async function saveContactConfig() {
  confirmContactOpen.value = false
  contactError.value = null
  try {
    await api.updateConfig('contact_name', config.value.contact_name.trim())
    await api.updateConfig('contact_number', config.value.contact_number.trim())
    contactSaved.value = true
    await refreshAudit()
  } catch (err: any) {
    contactError.value = err?.message || 'Gagal menyimpan kontak dukungan.'
  }
}

async function triggerIngestion() {
  confirmIngestionOpen.value = false
  ingestionRunning.value = true
  try {
    const res = await api.runIngestion()
    if (res) {
      ingestion.value = {
        ...ingestion.value,
        ...res,
      }
    }
    await refreshAudit()
  } finally {
    ingestionRunning.value = false
  }
}

async function addAdminAccount() {
  accountError.value = null
  const email = newAccountEmail.value.trim()
  const password = newAccountPassword.value
  if (!email || !password) {
    accountError.value = 'Email dan kata sandi wajib diisi.'
    return
  }
  try {
    const created = await api.createAdminAccount(email, password, newAccountRole.value)
    accounts.value.push(created)
    newAccountEmail.value = ''
    newAccountPassword.value = ''
    await refreshAudit()
  } catch (err: any) {
    accountError.value = err?.message || 'Gagal menambahkan akun admin.'
  }
}

async function removeAdminAccount(id: string) {
  accountError.value = null
  try {
    await api.deleteAdminAccount(id)
    accounts.value = accounts.value.filter((a) => a.id !== id)
    await refreshAudit()
  } catch (err: any) {
    accountError.value = err?.message || 'Gagal menghapus akun admin.'
  }
}

const filteredAuditLogs = computed(() =>
  auditLogs.value.filter((entry) => {
    if (
      auditActorFilter.value &&
      !String(entry.actor || '')
        .toLowerCase()
        .includes(auditActorFilter.value.toLowerCase())
    )
      return false
    if (
      auditActionFilter.value &&
      !String(entry.action || '')
        .toLowerCase()
        .includes(auditActionFilter.value.toLowerCase())
    )
      return false
    if (auditDateFrom.value) {
      const fromTs = new Date(auditDateFrom.value).getTime()
      if (!Number.isNaN(fromTs) && new Date(entry.at).getTime() < fromTs) return false
    }
    if (auditDateTo.value) {
      const endStr =
        auditDateTo.value.length === 10 ? `${auditDateTo.value}T23:59:59.999` : auditDateTo.value
      const toTs = new Date(endStr).getTime()
      if (!Number.isNaN(toTs) && new Date(entry.at).getTime() > toTs) return false
    }
    return true
  }),
)

const columns = [
  { key: 'actor', label: t('settings.col_actor') },
  { key: 'action', label: t('settings.col_action') },
  { key: 'target', label: t('settings.col_target') },
  { key: 'time', label: t('settings.col_time') },
]

function timeLabel(iso: string | null): string {
  if (!iso) return 'Belum pernah dijalankan'
  return new Date(iso).toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <RoleGate need="administer">
    <div>
      <PageHeader :title="t('settings.title')" />

      <div class="grid gap-4 lg:grid-cols-2">
        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.system') }}</h2>

          <div class="mt-3 space-y-3">
            <div>
              <label class="block text-[13px] text-primary">{{ t('settings.retention') }}</label>
              <input
                v-model="config.retention_months"
                type="number"
                min="1"
                max="60"
                class="mt-1 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 tabular text-[13.5px] text-primary"
              />
            </div>
            <div>
              <label class="block text-[13px] text-primary">{{ t('settings.rate_limit') }}</label>
              <input
                v-model="config.rate_limit_per_hour"
                type="number"
                min="1"
                max="500"
                class="mt-1 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 tabular text-[13.5px] text-primary"
              />
            </div>
            <div>
              <label class="block text-[13px] text-primary">{{ t('settings.similarity') }}</label>
              <input
                v-model="config.similarity_threshold"
                type="number"
                step="0.01"
                min="0"
                max="1"
                class="mt-1 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 tabular text-[13.5px] text-primary"
              />
              <p class="mt-1 rounded-lg bg-warning-bg px-2.5 py-1.5 text-[12.5px] text-warning">
                {{ t('settings.similarity_warning') }}
              </p>
            </div>
          </div>

          <p v-if="systemError" class="mt-2 text-[12.5px] text-danger">{{ systemError }}</p>
          <p v-if="systemSaved" class="mt-2 text-[12.5px] text-success">{{ t('common.saved') }}</p>

          <button
            type="button"
            class="mt-3 rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
            @click="requestSaveSystem"
          >
            {{ t('common.save') }}
          </button>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.contact') }}</h2>

          <p
            v-if="isContactPlaceholder"
            class="mt-3 rounded-lg bg-warning-bg px-3 py-2 text-[13px] text-warning"
          >
            {{ t('settings.contact_pending') }}
          </p>

          <label class="mt-3 block text-[13px] text-primary">
            {{ t('settings.contact_name') }}
          </label>
          <input
            v-model="config.contact_name"
            type="text"
            placeholder="Mis. Tim Peduli Tanya Iman"
            class="mt-1 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary"
          />

          <label class="mt-3 block text-[13px] text-primary">
            {{ t('settings.contact_number') }}
          </label>
          <input
            v-model="config.contact_number"
            type="tel"
            placeholder="Mis. +62 812-xxxx-xxxx"
            class="mt-1 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary"
          />

          <p v-if="contactError" class="mt-2 text-[12.5px] text-danger">{{ contactError }}</p>
          <p v-if="contactSaved" class="mt-2 text-[12.5px] text-success">{{ t('common.saved') }}</p>

          <button
            type="button"
            class="mt-3 rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
            @click="requestSaveContact"
          >
            {{ t('common.save') }}
          </button>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.corpus') }}</h2>
          <p class="meta mt-2">
            {{ t('settings.last_run') }}: {{ timeLabel(ingestion.last_run_at) }}
          </p>
          <p class="meta">
            {{ ingestion.sites_count }} situs · {{ ingestion.articles_count }} artikel ·
            {{ ingestion.chunks_count }} potongan
          </p>
          <button
            type="button"
            :disabled="ingestionRunning"
            class="mt-3 rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised disabled:opacity-50"
            @click="confirmIngestionOpen = true"
          >
            {{ ingestionRunning ? t('common.loading') : t('settings.run_ingestion') }}
          </button>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.accounts') }}</h2>
          <ul class="mt-2 divide-y divide-subtle">
            <li
              v-for="acct in accounts"
              :key="acct.id"
              class="flex items-center justify-between gap-2 py-2"
            >
              <span class="text-[13px] text-primary">{{ acct.email }}</span>
              <div class="flex items-center gap-2">
                <StatusChip
                  :label="t(`role.${acct.role}`)"
                  :tone="acct.role === 'super_admin' ? 'info' : 'neutral'"
                />
                <button
                  type="button"
                  class="text-[12px] text-danger hover:underline"
                  @click="removeAdminAccount(acct.id)"
                >
                  Hapus
                </button>
              </div>
            </li>
          </ul>

          <div class="mt-3 border-t border-subtle pt-3">
            <div class="grid gap-2 sm:grid-cols-3">
              <input
                v-model="newAccountEmail"
                type="email"
                placeholder="email@tanyaiman.id"
                class="min-h-[38px] rounded-lg border border-strong bg-surface px-2.5 text-[13px] text-primary"
              />
              <input
                v-model="newAccountPassword"
                type="password"
                placeholder="Kata sandi"
                class="min-h-[38px] rounded-lg border border-strong bg-surface px-2.5 text-[13px] text-primary"
              />
              <select
                v-model="newAccountRole"
                class="min-h-[38px] rounded-lg border border-strong bg-surface px-2 text-[13px] text-primary"
              >
                <option value="editor">{{ t('role.editor') }}</option>
                <option value="reviewer">{{ t('role.reviewer') }}</option>
                <option value="super_admin">{{ t('role.super_admin') }}</option>
              </select>
            </div>
            <p v-if="accountError" class="mt-1.5 text-[12px] text-danger">{{ accountError }}</p>
            <button
              type="button"
              class="mt-2 rounded-lg border border-strong px-3 py-1.5 text-[12.5px] text-primary transition hover:bg-raised"
              @click="addAdminAccount"
            >
              + Tambah akun
            </button>
          </div>
        </section>
      </div>

      <h2 class="mt-6 text-[15px] text-primary">{{ t('settings.audit') }}</h2>
      <div class="mt-2 flex flex-wrap gap-2">
        <input
          v-model="auditActorFilter"
          type="search"
          placeholder="Filter pelaku…"
          class="min-h-[38px] rounded-lg border border-strong bg-surface px-3 text-[13px] text-primary"
        />
        <input
          v-model="auditActionFilter"
          type="search"
          placeholder="Filter tindakan…"
          class="min-h-[38px] rounded-lg border border-strong bg-surface px-3 text-[13px] text-primary"
        />
        <input
          v-model="auditDateFrom"
          type="date"
          aria-label="Audit dari tanggal"
          class="min-h-[38px] rounded-lg border border-strong bg-surface px-2 text-[13px] text-primary"
        />
        <input
          v-model="auditDateTo"
          type="date"
          aria-label="Audit sampai tanggal"
          class="min-h-[38px] rounded-lg border border-strong bg-surface px-2 text-[13px] text-primary"
        />
      </div>

      <div class="mt-2">
        <DataTable :columns="columns">
          <tr v-if="auditLoading" class="border-t border-subtle">
            <td colspan="4" class="px-3 py-6 text-center text-[13px] text-secondary">
              Memuat jejak audit...
            </td>
          </tr>
          <tr v-else-if="filteredAuditLogs.length === 0" class="border-t border-subtle">
            <td colspan="4" class="px-3 py-6 text-center text-[13px] text-secondary">
              Belum ada jejak audit yang tercatat.
            </td>
          </tr>
          <tr v-for="entry in filteredAuditLogs" :key="entry.id" class="border-t border-subtle">
            <td class="px-3 py-2.5 text-[13px] text-primary">{{ entry.actor }}</td>
            <td class="px-3 py-2.5 text-[13px] text-primary">{{ entry.action }}</td>
            <td class="px-3 py-2.5 text-[13px] text-secondary" :title="entry.detail">
              {{ entry.target }}
            </td>
            <td class="px-3 py-2.5 text-[12.5px] text-secondary">{{ timeLabel(entry.at) }}</td>
          </tr>
        </DataTable>
      </div>

      <ConfirmDialog
        :open="confirmSimilarityOpen"
        :title="t('settings.similarity')"
        :body="t('settings.similarity_warning')"
        @confirm="saveSystemConfig"
        @cancel="confirmSimilarityOpen = false"
      />

      <ConfirmDialog
        :open="confirmContactOpen"
        :title="t('settings.contact')"
        body="Nomor kontak dukungan ini akan ditampilkan kepada penanya yang membutuhkan pendampingan emosional."
        @confirm="saveContactConfig"
        @cancel="confirmContactOpen = false"
      />

      <ConfirmDialog
        :open="confirmIngestionOpen"
        :title="t('settings.corpus')"
        body="Jalankan pengambilan materi dari 5 situs yang disetujui sekarang?"
        @confirm="triggerIngestion"
        @cancel="confirmIngestionOpen = false"
      />
    </div>
  </RoleGate>
</template>
