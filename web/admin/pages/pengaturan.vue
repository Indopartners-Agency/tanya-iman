<script setup lang="ts">
import { audit } from '~/demo/fixtures'

/**
 * Admin UX section 14. super_admin only.
 *
 * The support contact (F-45) is deliberately shown as unset: the number and
 * the emotional-deferral copy behind it are owned by the client's pastoral
 * team (SOW dependency B1), and the template still carries its PLACEHOLDER
 * marker. Shipping an invented number here would be worse than showing none.
 */
const { t } = useCopy()

const columns = [
  { key: 'actor', label: t('settings.col_actor') },
  { key: 'action', label: t('settings.col_action') },
  { key: 'target', label: t('settings.col_target') },
  { key: 'time', label: t('settings.col_time') },
]

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
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

          <dl class="mt-3 space-y-3">
            <div>
              <dt class="text-[13px] text-primary">{{ t('settings.retention') }}</dt>
              <dd class="tabular text-[13px] text-secondary">12</dd>
            </div>
            <div>
              <dt class="text-[13px] text-primary">{{ t('settings.rate_limit') }}</dt>
              <dd class="tabular text-[13px] text-secondary">30</dd>
            </div>
            <div>
              <dt class="text-[13px] text-primary">{{ t('settings.similarity') }}</dt>
              <dd class="tabular text-[13px] text-secondary">0,72</dd>
              <p class="mt-1 rounded-lg bg-warning-bg px-2.5 py-1.5 text-[12.5px] text-warning">
                {{ t('settings.similarity_warning') }}
              </p>
            </div>
          </dl>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.contact') }}</h2>

          <p class="mt-3 rounded-lg bg-warning-bg px-3 py-2 text-[13px] text-warning">
            {{ t('settings.contact_pending') }}
          </p>

          <label class="mt-3 block text-[13px] text-primary">
            {{ t('settings.contact_name') }}
          </label>
          <input
            type="text"
            disabled
            class="mt-1 min-h-[40px] w-full rounded-lg border border-subtle bg-raised px-3 text-[13.5px] text-secondary"
          />

          <label class="mt-3 block text-[13px] text-primary">
            {{ t('settings.contact_number') }}
          </label>
          <input
            type="tel"
            disabled
            class="mt-1 min-h-[40px] w-full rounded-lg border border-subtle bg-raised px-3 text-[13.5px] text-secondary"
          />
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.corpus') }}</h2>
          <p class="meta mt-2">{{ t('settings.last_run') }}: 7 Sep 2026, 02:00</p>
          <p class="meta">5 situs · 1.284 artikel · 9.412 potongan</p>
          <button
            type="button"
            class="mt-3 rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
          >
            {{ t('settings.run_ingestion') }}
          </button>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.accounts') }}</h2>
          <ul class="mt-2 divide-y divide-subtle">
            <li class="flex items-center justify-between py-2">
              <span class="text-[13px] text-primary">siti@tanyaiman.id</span>
              <StatusChip :label="t('role.editor')" />
            </li>
            <li class="flex items-center justify-between py-2">
              <span class="text-[13px] text-primary">budi@tanyaiman.id</span>
              <StatusChip :label="t('role.reviewer')" />
            </li>
            <li class="flex items-center justify-between py-2">
              <span class="text-[13px] text-primary">admin@tanyaiman.id</span>
              <StatusChip :label="t('role.super_admin')" tone="info" />
            </li>
          </ul>
        </section>
      </div>

      <h2 class="mt-6 text-[15px] text-primary">{{ t('settings.audit') }}</h2>
      <div class="mt-2">
        <DataTable :columns="columns">
          <tr v-for="entry in audit" :key="entry.id" class="border-t border-subtle">
            <td class="px-3 py-2.5 text-[13px] text-primary">{{ entry.actor }}</td>
            <td class="px-3 py-2.5 text-[13px] text-primary">{{ entry.action }}</td>
            <td class="px-3 py-2.5 text-[13px] text-secondary">{{ entry.target }}</td>
            <td class="px-3 py-2.5 text-[12.5px] text-secondary">{{ timeLabel(entry.at) }}</td>
          </tr>
        </DataTable>
      </div>
    </div>
  </RoleGate>
</template>
