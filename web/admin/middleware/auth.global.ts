import { useSessionStore } from '~/stores/session'

/**
 * PRD F-19 & §7.4: Global route protection for the Editorial Admin Portal.
 * Redirects any unauthenticated navigation outside `/masuk` to `/masuk`.
 */
export default defineNuxtRouteMiddleware((to) => {
  if (to.path === '/masuk') return
  const session = useSessionStore()
  if (!session.isAuthenticated) {
    return navigateTo('/masuk', { replace: true })
  }
})
