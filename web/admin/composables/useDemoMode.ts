/** See the seeker app's useDemoMode. Same flag, same lifetime, same coercion. */
export function useDemoMode(): boolean {
  return String(useRuntimeConfig().public.demoMode) === '1'
}
