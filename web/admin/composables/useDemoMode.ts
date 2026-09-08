/** See the seeker app's useDemoMode. Same flag, same lifetime. */
export function useDemoMode(): boolean {
  return useRuntimeConfig().public.demoMode === '1'
}
