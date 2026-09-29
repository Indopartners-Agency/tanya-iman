import { defineStore } from 'pinia'
import type { AdminRole, AdminLoginResponse, AdminRefreshResponse } from '@tanya-iman/shared'

export type { AdminRole }

export const useSessionStore = defineStore('session', () => {
  const email = ref<string | null>(null)
  const role = ref<AdminRole>('editor')
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)

  // Restore stored session if present on the client
  if (typeof localStorage !== 'undefined') {
    const savedToken = localStorage.getItem('ti_admin_access_token')
    const savedRefresh = localStorage.getItem('ti_admin_refresh_token')
    const savedEmail = localStorage.getItem('ti_admin_email')
    const savedRole = localStorage.getItem('ti_admin_role') as AdminRole | null

    if (savedToken && savedEmail) {
      accessToken.value = savedToken
      refreshToken.value = savedRefresh
      email.value = savedEmail
      if (savedRole) role.value = savedRole
    }
  }

  const isAuthenticated = computed(() => email.value !== null)

  /** Section 5.3: a reviewer sees no editing controls anywhere. */
  const canEdit = computed(() => role.value === 'editor' || role.value === 'super_admin')
  const canAdminister = computed(() => role.value === 'super_admin')

  function signIn(nextEmail: string, nextRole: AdminRole) {
    email.value = nextEmail
    role.value = nextRole
    accessToken.value = 'demo-admin-token'
    refreshToken.value = 'demo-admin-refresh'
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('ti_admin_access_token', accessToken.value)
      localStorage.setItem('ti_admin_refresh_token', refreshToken.value)
      localStorage.setItem('ti_admin_email', nextEmail)
      localStorage.setItem('ti_admin_role', nextRole)
    }
  }

  async function login(loginEmail: string, password: string): Promise<void> {
    const config = useRuntimeConfig()
    const baseUrl = (config.public.apiBase || 'http://localhost:8000').replace(/\/$/, '')

    let res: Response
    try {
      res = await fetch(`${baseUrl}/api/admin/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password }),
      })
    } catch {
      // Fallback to non-prefixed route if /api is not mounted on older proxy
      res = await fetch(`${baseUrl}/admin/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password }),
      })
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      const detail = typeof err?.detail === 'string' ? err.detail : 'Gagal masuk. Periksa email dan kata sandi.'
      throw new Error(detail)
    }

    const data = (await res.json()) as AdminLoginResponse
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    email.value = data.email
    role.value = data.role

    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('ti_admin_access_token', data.access_token)
      localStorage.setItem('ti_admin_refresh_token', data.refresh_token)
      localStorage.setItem('ti_admin_email', data.email)
      localStorage.setItem('ti_admin_role', data.role)
    }
  }

  async function refresh(): Promise<string | null> {
    if (!refreshToken.value) return null
    const config = useRuntimeConfig()
    const baseUrl = (config.public.apiBase || 'http://localhost:8000').replace(/\/$/, '')

    try {
      const res = await fetch(`${baseUrl}/api/admin/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken.value }),
      })

      if (!res.ok) {
        signOut()
        return null
      }

      const data = (await res.json()) as AdminRefreshResponse
      accessToken.value = data.access_token
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('ti_admin_access_token', data.access_token)
      }
      return data.access_token
    } catch {
      signOut()
      return null
    }
  }

  function signOut() {
    email.value = null
    role.value = 'editor'
    accessToken.value = null
    refreshToken.value = null
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('ti_admin_access_token')
      localStorage.removeItem('ti_admin_refresh_token')
      localStorage.removeItem('ti_admin_email')
      localStorage.removeItem('ti_admin_role')
    }
  }

  return {
    email,
    role,
    accessToken,
    refreshToken,
    isAuthenticated,
    canEdit,
    canAdminister,
    signIn,
    login,
    refresh,
    signOut,
  }
})
