import type { Config } from 'tailwindcss'

/**
 * Colour utilities resolve to the CSS variables in assets/css/tokens.css, which
 * mirror seekerTokens in web/shared. Components therefore never name a colour —
 * Chat UX section 4.2 requires exactly that, and it is what makes a later dark
 * mode a variable swap rather than a rewrite.
 */
export default {
  content: [
    './components/**/*.{vue,ts}',
    './composables/**/*.ts',
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
        'bubble-user': 'var(--bubble-user)',
        'bubble-assistant': 'var(--bubble-assistant)',
        warning: {
          DEFAULT: 'var(--status-warning-text)',
          bg: 'var(--status-warning-bg)',
        },
        info: {
          DEFAULT: 'var(--status-info-text)',
          bg: 'var(--status-info-bg)',
        },
        care: {
          DEFAULT: 'var(--status-care-text)',
          bg: 'var(--status-care-bg)',
          border: 'var(--status-care-border)',
        },
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        serif: 'var(--font-serif)',
      },
      fontSize: {
        // Conversational Indonesian at default browser size is cramped. The
        // chat surface reads at 15px/1.7 throughout.
        base: ['15px', '1.7'],
      },
      maxWidth: {
        // Chat UX 4.4: measure capped near 65 characters; a full-width
        // conversation on a desktop monitor is unreadable.
        measure: '640px',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
      },
    },
  },
} satisfies Config
