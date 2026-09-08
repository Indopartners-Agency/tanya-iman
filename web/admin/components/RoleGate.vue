<script setup lang="ts">
import { useSessionStore } from '~/stores/session'

/**
 * Section 5.3: unavailable actions are hidden rather than disabled, and a
 * reviewer who navigates straight to an editor route gets a role-aware
 * message — not a blank page and not a raw 403.
 */
const props = defineProps<{ need: 'edit' | 'administer' }>()

const { t } = useCopy()
const session = useSessionStore()

const allowed = computed(() =>
  props.need === 'edit' ? session.canEdit : session.canAdminister,
)
</script>

<template>
  <slot v-if="allowed" />
  <div v-else class="rounded-xl border border-subtle bg-surface px-6 py-10 text-center">
    <p class="text-[14px] text-secondary">{{ t('common.no_access') }}</p>
  </div>
</template>
