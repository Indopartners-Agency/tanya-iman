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
  const storedUid =
    typeof localStorage !== 'undefined' ? localStorage.getItem('ti_dev_uid') : null
  const storedMethod =
    typeof localStorage !== 'undefined'
      ? (localStorage.getItem('ti_dev_method') as AuthMethod | null)
      : null

  const uid = ref<string | null>(storedUid)
  const method = ref<AuthMethod | null>(storedUid ? (storedMethod ?? 'guest') : null)
  const ready = ref(Boolean(storedUid))

  const isAuthenticated = computed(() => uid.value !== null)
  const isGuest = computed(() => method.value === 'guest')

  async function signInAsGuest() {
    // Phase 2 stand-in for Firebase anonymous auth. The uid is persisted so a
    // reload keeps the same conversation, which is the behaviour the real
    // implementation must also have.
    const stored =
      typeof localStorage !== 'undefined' ? localStorage.getItem('ti_dev_uid') : null
    const rand =
      typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
        ? crypto.randomUUID().slice(0, 12)
        : Math.random().toString(36).slice(2, 14)
    const id = stored ?? `guest_${rand}`
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('ti_dev_uid', id)
      localStorage.setItem('ti_dev_method', 'guest')
    }

    uid.value = id
    method.value = 'guest'
    ready.value = true
  }

  async function signInWithPhone(phone: string, channel: 'sms' | 'whatsapp' = 'whatsapp') {
    // F-4 & F-25: upgrading from guest preserves the existing uid so active
    // session and conversation history carry over seamlessly.
    const cleanPhone = phone.replace(/\D/g, '')
    const existingUid =
      uid.value ??
      (typeof localStorage !== 'undefined' ? localStorage.getItem('ti_dev_uid') : null)
    const id = existingUid ?? `user_${cleanPhone || 'verified'}`
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('ti_dev_uid', id)
      localStorage.setItem('ti_dev_method', channel)
    }

    uid.value = id
    method.value = channel
    ready.value = true
  }

  async function getIdToken(): Promise<string | null> {
    if (!uid.value || !method.value) return null
    // Matches the `dev:<uid>:<method>` form accepted by the backend only when
    // ENV=development. See backend/services/auth.py.
    return `dev:${uid.value}:${method.value}`
  }

  async function signOut() {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('ti_dev_uid')
      localStorage.removeItem('ti_dev_method')
    }
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
    signInWithPhone,
    getIdToken,
    signOut,
  }
})
