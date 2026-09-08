<script setup lang="ts">
import type { Citation } from '@tanya-iman/shared'

/**
 * Chat UX section 9. The article title is the link text and the domain sits
 * beneath it in Meta type, so a seeker can see where a tap will send them
 * before they take it. Never a bare URL.
 */
defineProps<{ citations: Citation[] }>()

const { t } = useCopy()

/**
 * Links open in a new tab on web and in the external browser on Android.
 * Inside the widget they must escape the iframe — a citation that opens in a
 * 620px-tall frame strands the reader (Chat UX section 11).
 */
const { platform } = usePlatform()
const target = platform === 'widget' ? '_top' : '_blank'
</script>

<template>
  <div v-if="citations.length" class="mt-4 border-t border-subtle pt-3">
    <p class="meta mb-2">{{ t('ui.answer_sources') }}</p>
    <ul class="space-y-2.5">
      <li v-for="citation in citations" :key="citation.url" class="flex gap-2">
        <span aria-hidden="true" class="mt-0.5 shrink-0 text-secondary">&#128196;</span>
        <span class="min-w-0">
          <a
            :href="citation.url"
            :target="target"
            rel="noopener noreferrer"
            class="block text-[14px] leading-snug text-accent underline decoration-subtle underline-offset-2 hover:decoration-accent"
          >
            {{ citation.title }}
          </a>
          <span class="meta block">{{ citation.site }}</span>
        </span>
      </li>
    </ul>
  </div>
</template>
