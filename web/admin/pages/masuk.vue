<script setup lang="ts">
import { useSessionStore, type AdminRole } from '~/stores/session'

/**
 * Real admin auth is Phase 3 (hardened admin auth) and Phase 6. In demo mode
 * the role picker stands in for it, which also lets a reviewer see the portal
 * from each of the three roles — section 5.3 hides controls by role, and that
 * is only reviewable if the role can be changed.
 */
definePageMeta({ layout: 'auth' })

const { t } = useCopy()
const session = useSessionStore()
const router = useRouter()
const demo = useDemoMode()

const email = ref('siti@tanyaiman.id')
const role = ref<AdminRole>('editor')

const roles: AdminRole[] = ['editor', 'reviewer', 'super_admin']

async function signIn() {
  session.signIn(email.value, role.value)
  await router.push('/')
}
</script>

<template>
  <div class="w-full max-w-[380px]">
    <h1 class="text-[22px] text-primary">{{ t('login.title') }}</h1>

    <label for="email" class="mt-6 block text-[13px] font-medium text-primary">
      {{ t('login.email') }}
    </label>
    <input
      id="email"
      v-model="email"
      type="email"
      class="mt-1.5 min-h-[44px] w-full rounded-lg border border-strong bg-surface px-3 text-[14px] text-primary outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
    />

    <template v-if="demo">
      <p class="meta mt-4">{{ t('login.demo_hint') }}</p>
      <div class="mt-2 grid grid-cols-3 gap-2">
        <button
          v-for="option in roles"
          :key="option"
          type="button"
          :class="[
            'min-h-[40px] rounded-lg border px-2 text-[12.5px] transition',
            role === option
              ? 'border-accent bg-accent text-on-accent'
              : 'border-strong text-primary hover:bg-raised',
          ]"
          @click="role = option"
        >
          {{ t(`role.${option}`) }}
        </button>
      </div>
    </template>

    <template v-else>
      <label for="password" class="mt-4 block text-[13px] font-medium text-primary">
        {{ t('login.password') }}
      </label>
      <input
        id="password"
        type="password"
        class="mt-1.5 min-h-[44px] w-full rounded-lg border border-strong bg-surface px-3 text-[14px] text-primary outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
      />
    </template>

    <button
      type="button"
      class="mt-6 min-h-[44px] w-full rounded-lg bg-accent text-[14px] font-medium text-on-accent transition hover:bg-accent-hover"
      @click="signIn"
    >
      {{ t('login.submit') }}
    </button>
  </div>
</template>
