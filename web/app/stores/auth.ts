import { defineStore } from 'pinia'
import type { AuthMethod } from '@tanya-iman/shared'

/**
 * Seeker identity.
 *
 * Guests get a real Firebase anonymous uid rather than a client-side fake. That
 * is what makes F-4 possible: when a guest later verifies a phone number, the
 * anonymous credential is upgraded in place and their existing conversation
 * survives. A locally-invented id would strand that history.
 *
 * Phase 3 (PIP Task 3.1) replaces the dev token below with the Firebase SDK.
 */
export const useAuthStore = defineStore('auth', () => {
  const uid = ref<string | null>(null)
  const method = ref<AuthMethod | null>(null)
  const ready = ref(false)

  const isAuthenticated = computed(() => uid.value !== null)
  const isGuest = computed(() => method.value === 'guest')

  async function signInAsGuest() {
    // Phase 2 stand-in for Firebase anonymous auth. The uid is persisted so a
    // reload keeps the same conversation, which is the behaviour the real
    // implementation must also have.
    const stored = localStorage.getItem('ti_dev_uid')
    const rand =
      typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
        ? crypto.randomUUID().slice(0, 12)
        : Math.random().toString(36).slice(2, 14)
    const id = stored ?? `guest_${rand}`
    localStorage.setItem('ti_dev_uid', id)

    uid.value = id
    method.value = 'guest'
    ready.value = true
  }

  async function getIdToken(): Promise<string | null> {
    if (!uid.value || !method.value) return null
    // Matches the `dev:<uid>:<method>` form accepted by the backend only when
    // ENV=development. See backend/services/auth.py.
    return `dev:${uid.value}:${method.value}`
  }

  async function signOut() {
    localStorage.removeItem('ti_dev_uid')
    uid.value = null
    method.value = null
  }

  return {
    uid,
    method,
    ready,
    isAuthenticated,
    isGuest,
    signInAsGuest,
    getIdToken,
    signOut,
  }
})
