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
const password = ref('')
const role = ref<AdminRole>('editor')
const error = ref<string | null>(null)
const busy = ref(false)

const roles: AdminRole[] = ['editor', 'reviewer', 'super_admin']

async function signIn() {
  if (demo) {
    session.signIn(email.value, role.value)
    await router.push('/')
    return
  }

  if (!email.value || !password.value) {
    error.value = 'Email dan kata sandi wajib diisi'
    return
  }

  busy.value = true
  error.value = null

  try {
    await session.login(email.value, password.value)
    await router.push('/')
  } catch (err: any) {
    error.value = err?.message || 'Gagal masuk. Periksa email dan kata sandi Anda.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-[380px]">
    <h1 class="text-[22px] text-primary">{{ t('login.title') }}</h1>

    <form class="mt-6" @submit.prevent="signIn">
      <label for="email" class="block text-[13px] font-medium text-primary">
        {{ t('login.email') }}
      </label>
      <input
        id="email"
        v-model="email"
        type="email"
        required
        autocomplete="email"
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
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          class="mt-1.5 min-h-[44px] w-full rounded-lg border border-strong bg-surface px-3 text-[14px] text-primary outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
        />
      </template>

      <p v-if="error" class="mt-3 text-[13px] text-danger">{{ error }}</p>

      <button
        type="submit"
        :disabled="busy"
        class="mt-6 min-h-[44px] w-full rounded-lg bg-accent text-[14px] font-medium text-on-accent transition hover:bg-accent-hover disabled:opacity-50"
      >
        {{ busy ? 'Memproses...' : t('login.submit') }}
      </button>
    </form>
  </div>
</template>
