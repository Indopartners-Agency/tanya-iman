import { createClient, type ApiClient } from '@tanya-iman/shared'
import { useAuthStore } from '~/stores/auth'
import { createDemoClient } from '~/composables/useDemoClient'

let client: ApiClient | null = null

export function useApi(): ApiClient {
  if (!client) {
    const config = useRuntimeConfig()

    // The demo client implements the same ApiClient interface, so the swap is
    // invisible to every store, page, and component downstream.
    if (useDemoMode()) {
      client = createDemoClient()
      return client
    }

    const auth = useAuthStore()
    // Resolved per request rather than captured once: Firebase ID tokens
    // expire after an hour and a seeker may well sit on one conversation
    // longer than that.
    client = createClient({
      baseUrl: config.public.apiBase,
      getToken: () => auth.getIdToken(),
    })
  }
  return client
}
