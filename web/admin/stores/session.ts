import { defineStore } from 'pinia'

/** Admin UX section 3. Three roles, hidden capabilities rather than disabled. */
export type AdminRole = 'editor' | 'reviewer' | 'super_admin'

export const useSessionStore = defineStore('session', () => {
  const email = ref<string | null>(null)
  const role = ref<AdminRole>('editor')

  const isAuthenticated = computed(() => email.value !== null)

  /** Section 5.3: a reviewer sees no editing controls anywhere. */
  const canEdit = computed(() => role.value === 'editor' || role.value === 'super_admin')
  const canAdminister = computed(() => role.value === 'super_admin')

  function signIn(nextEmail: string, nextRole: AdminRole) {
    email.value = nextEmail
    role.value = nextRole
  }

  function signOut() {
    email.value = null
  }

  return { email, role, isAuthenticated, canEdit, canAdminister, signIn, signOut }
})
