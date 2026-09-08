import type { Config } from 'tailwindcss'

/**
 * Mirrors adminTokens in web/shared via the CSS variables in
 * assets/css/tokens.css. Components never name a colour (Admin UX 4.2).
 */
export default {
  content: [
    './components/**/*.{vue,ts}',
    './composables/**/*.ts',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './stores/**/*.ts',
    './demo/**/*.ts',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        base: 'var(--bg-base)',
        surface: 'var(--bg-surface)',
        raised: 'var(--bg-raised)',
        primary: 'var(--text-primary)',
        secondary: 'var(--text-secondary)',
        'on-accent': 'var(--text-on-accent)',
        accent: {
          DEFAULT: 'var(--accent-primary)',
          hover: 'var(--accent-hover)',
        },
        subtle: 'var(--border-subtle)',
        strong: 'var(--border-strong)',
        success: {
          DEFAULT: 'var(--status-success-text)',
          bg: 'var(--status-success-bg)',
        },
        warning: {
          DEFAULT: 'var(--status-warning-text)',
          bg: 'var(--status-warning-bg)',
        },
        danger: {
          DEFAULT: 'var(--status-danger-text)',
          bg: 'var(--status-danger-bg)',
        },
        info: {
          DEFAULT: 'var(--status-info-text)',
          bg: 'var(--status-info-bg)',
        },
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        serif: 'var(--font-serif)',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
      },
    },
  },
} satisfies Config
