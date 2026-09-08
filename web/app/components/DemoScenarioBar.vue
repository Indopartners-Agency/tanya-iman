<script setup lang="ts">
import { scenarios, type DemoScenario } from '~/demo/scenarios'
import { forceScenario } from '~/composables/useDemoClient'

/**
 * Renders only in demo mode. Lets a reviewer walk every response state of Chat
 * UX section 8 without having to guess a question that triggers each one.
 *
 * Deleted with the rest of demo mode in Phase 5.
 */
const { t } = useCopy()
const chat = useChatStore()

const active = ref<DemoScenario | null>(null)
const open = ref(false)

async function run(scenario: DemoScenario) {
  active.value = scenario
  open.value = false
  forceScenario(scenario)
  await chat.ask(scenario.question)
  // One-shot: the next freely-typed question routes by keyword again.
  forceScenario(null)
}
</script>

<template>
  <div class="border-b border-subtle bg-info-bg px-4 py-2">
    <div class="mx-auto flex max-w-measure flex-wrap items-center gap-x-3 gap-y-1.5">
      <p class="meta flex-1 text-info">{{ t('ui.demo_banner') }}</p>

      <div class="relative">
        <button
          type="button"
          class="min-h-[36px] rounded-lg border border-info/30 px-3 text-[12px] font-medium text-info transition hover:bg-surface"
          :aria-expanded="open"
          @click="open = !open"
        >
          {{ t('ui.demo_scenario') }}
          <span aria-hidden="true" class="ml-1">&#9662;</span>
        </button>

        <div
          v-if="open"
          class="absolute right-0 top-10 z-30 w-72 overflow-hidden rounded-xl border border-subtle bg-surface shadow-md"
        >
          <button
            v-for="scenario in scenarios"
            :key="scenario.label"
            type="button"
            class="block w-full px-4 py-3 text-left text-[13px] text-primary transition hover:bg-raised"
            @click="run(scenario)"
          >
            <span class="block font-medium">{{ scenario.label }}</span>
            <span class="meta mt-0.5 block truncate">{{ scenario.question }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
