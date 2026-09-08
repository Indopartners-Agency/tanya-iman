/**
 * Demo mode backs the hosted client-approval build with fixtures instead of a
 * backend, so the static bundle can be deployed and reviewed before Phase 5
 * exists.
 *
 * One place reads the flag. Components ask this, never the runtime config, so
 * removing demo mode later is a matter of deleting this file and its callers.
 */
export function useDemoMode(): boolean {
  return useRuntimeConfig().public.demoMode === '1'
}
