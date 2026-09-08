/**
 * Demo mode backs the hosted client-approval build with fixtures instead of a
 * backend, so the static bundle can be deployed and reviewed before Phase 5
 * exists.
 *
 * One place reads the flag. Components ask this, never the runtime config, so
 * removing demo mode later is a matter of deleting this file and its callers.
 *
 * Compared as a string because Nuxt serialises a numeric-looking runtime config
 * value as a number: NUXT_PUBLIC_DEMO_MODE=1 reaches the browser as `1`, not
 * `"1"`, and a strict `=== '1'` would silently never match in a built bundle.
 */
export function useDemoMode(): boolean {
  return String(useRuntimeConfig().public.demoMode) === '1'
}
